#!/usr/bin/env python3
"""DeltaX gateway. Standard library only. Bind localhost; put behind HTTPS Nginx."""
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data' / 'rounds.json'
PASSWORD = os.environ.get('DELTAX_ADMIN_PASSWORD', '')
PORT = int(os.environ.get('DELTAX_PORT', '5500'))
HOST = os.environ.get('DELTAX_BIND', '127.0.0.1')
SESSION_SECONDS = 4 * 60 * 60
SESSIONS = {}
FAILURES = {}
LOCK = threading.RLock()
PUBLIC_FILES = {'/':'index.html','/index.html':'index.html','/styles.css':'styles.css','/app.js':'app.js','/admin':'admin.html','/admin.html':'admin.html',
'/admin.js':'admin.js','/admin.css':'admin.css','/assets/deltax-logo.png':'assets/deltax-logo.png',
'/assets/pioneers-symbol.png':'assets/pioneers-symbol.png','/assets/favicon.svg':'assets/favicon.svg'}
MIMES = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'}

def read_state():
    try:
        with DATA.open(encoding='utf-8') as f: val = json.load(f)
        rounds=val['rounds']
        if len(rounds)!=3:raise ValueError('expected three rounds')
        return {'rounds':[{'enabled':bool(r.get('enabled',False)), 'url':str(r.get('url',''))} for r in rounds]}
    except (OSError,ValueError,TypeError,KeyError):
        return {'rounds':[{'enabled':False,'url':''} for _ in range(3)]}

def store_state(value):
    DATA.parent.mkdir(exist_ok=True)
    tmp=DATA.with_name('.rounds-'+secrets.token_hex(6)+'.tmp')
    try:
        with tmp.open('x',encoding='utf-8') as f:
            json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(tmp,DATA)
    finally:
        tmp.unlink(missing_ok=True)

def valid_url(value):
    if not isinstance(value,str) or len(value)>2048:return False
    try:
        u=urlsplit(value)
        return u.scheme=='https' and bool(u.hostname) and not u.username and not u.password and all(ord(c)>=32 for c in value)
    except ValueError:return False

class Handler(BaseHTTPRequestHandler):
    server_version='DeltaXGateway'
    def send(self,code,body=b'',content_type='application/json',cookies=None):
        self.send_response(code)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store' if self.path.startswith('/api/') or self.path.startswith('/admin') else 'no-cache')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('X-Frame-Options','DENY')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' https://fonts.googleapis.com; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self'; base-uri 'none'; object-src 'none'; frame-ancestors 'none'; form-action 'self'")
        if cookies:self.send_header('Set-Cookie',cookies)
        self.end_headers()
        self.wfile.write(body)
    def reply(self,code,value,cookies=None):
        self.send(code,json.dumps(value).encode('utf-8'),'application/json',cookies)
    def secure_cookie(self):
        return 'Secure; ' if self.headers.get('X-Forwarded-Proto')=='https' else ''
    def logged_in(self):
        cookies=self.headers.get('Cookie','')
        token=next((p.strip().partition('=')[2] for p in cookies.split(';') if p.strip().startswith('deltax_session=')),None)
        with LOCK:
            session=SESSIONS.get(token)
            if not session:return None
            if session['expires'] < time.time():
                SESSIONS.pop(token,None);return None
            return session
    def do_GET(self):
        path=urlsplit(self.path).path
        if path=='/api/rounds':
            with LOCK:state=read_state()
            return self.reply(200,state)
        if path=='/api/admin/session':
            s=self.logged_in()
            return self.reply(200,{'authenticated':bool(s),'csrf':s['csrf'] if s else None,'configured':bool(PASSWORD)})
        if path=='/api/admin/state':
            if not self.logged_in():return self.reply(401,{'error':'Sign in required.'})
            with LOCK:state=read_state()
            return self.reply(200,state)
        if path in PUBLIC_FILES:
            filename=BASE/PUBLIC_FILES[path]
            try:data=filename.read_bytes()
            except OSError:return self.send(404,b'Not found','text/plain')
            return self.send(200,data,MIMES.get(filename.suffix,'application/octet-stream'))
        return self.send(404,b'Not found','text/plain')
    def request_body(self):
        if self.headers.get('Content-Type','').split(';')[0].strip() != 'application/json':raise ValueError('JSON body required.')
        length=int(self.headers.get('Content-Length','0'))
        if length < 1 or length>8192:raise ValueError('Invalid request size.')
        obj=json.loads(self.rfile.read(length))
        if not isinstance(obj,dict):raise ValueError('Invalid JSON object.')
        return obj
    def origin_ok(self):
        origin=self.headers.get('Origin','')
        if not origin:return False
        try:
            url=urlsplit(origin)
            # Nginx must forward original Host, and only locally trusted proxy can forward proto.
            expected=self.headers.get('Host','')
            scheme='https' if self.headers.get('X-Forwarded-Proto')=='https' else 'http'
            return origin==f'{scheme}://{expected}' and url.path==''
        except ValueError:return False
    def do_POST(self):
        path=urlsplit(self.path).path
        if not path.startswith('/api/admin/'):
            return self.reply(404,{'error':'Not found.'})
        if not self.origin_ok():return self.reply(403,{'error':'Invalid request origin.'})
        try:body=self.request_body()
        except (ValueError,TypeError,json.JSONDecodeError):return self.reply(400,{'error':'Invalid request body.'})
        if path=='/api/admin/login':
            if not PASSWORD or len(PASSWORD)<12:return self.reply(503,{'error':'Admin password is not configured (minimum 12 characters).'})
            ip=self.client_address[0]
            with LOCK:
                attempts=FAILURES.get(ip,[])
                attempts=[v for v in attempts if time.time()-v < 900]
                if len(attempts)>=8:return self.reply(429,{'error':'Too many attempts. Try again in 15 minutes.'})
                supplied=body.get('password','')
                if not isinstance(supplied,str) or not hmac.compare_digest(hashlib.sha256(supplied.encode()).digest(),hashlib.sha256(PASSWORD.encode()).digest()):
                    attempts.append(time.time());FAILURES[ip]=attempts
                    return self.reply(401,{'error':'Incorrect password.'})
                FAILURES.pop(ip,None)
                token=secrets.token_urlsafe(32);csrf=secrets.token_urlsafe(32)
                SESSIONS[token]={'expires':time.time()+SESSION_SECONDS,'csrf':csrf}
            cookie=f'deltax_session={token}; HttpOnly; {self.secure_cookie()}SameSite=Strict; Path=/; Max-Age={SESSION_SECONDS}'
            return self.reply(200,{'authenticated':True,'csrf':csrf},cookie)
        session=self.logged_in()
        if not session:return self.reply(401,{'error':'Session expired. Sign in again.'})
        csrf=self.headers.get('X-CSRF-Token','')
        if not hmac.compare_digest(csrf,session['csrf']):return self.reply(403,{'error':'Invalid security token.'})
        if path=='/api/admin/logout':
            cookie='deltax_session=; HttpOnly; '+self.secure_cookie()+'SameSite=Strict; Path=/; Max-Age=0'
            with LOCK:
                for pair in self.headers.get('Cookie','').split(';'):
                    if pair.strip().startswith('deltax_session='):SESSIONS.pop(pair.strip().partition('=')[2],None)
            return self.reply(200,{'ok':True},cookie)
        if path=='/api/admin/rounds':
            rounds=body.get('rounds')
            if not isinstance(rounds,list) or len(rounds)!=3:return self.reply(400,{'error':'Exactly three rounds are required.'})
            clean=[]
            for i,r in enumerate(rounds):
                if not isinstance(r,dict) or type(r.get('enabled')) is not bool:return self.reply(400,{'error':f'Invalid status for round {i+1}.'})
                url=r.get('url','')
                if url and not valid_url(url):return self.reply(400,{'error':f'Round {i+1} requires a valid HTTPS URL.'})
                if r['enabled'] and not url:return self.reply(400,{'error':f'Set the URL before opening round {i+1}.'})
                clean.append({'enabled':r['enabled'],'url':url})
            with LOCK:
                try:store_state({'rounds':clean})
                except OSError:return self.reply(500,{'error':'Could not save. Check server data directory permissions.'})
            return self.reply(200,{'ok':True,'rounds':clean})
        return self.reply(404,{'error':'Not found.'})

if __name__=='__main__':
    if HOST not in ('127.0.0.1','localhost','::1'):
        raise SystemExit('For safety, DELTAX_BIND must be loopback. Use Nginx for public HTTPS access.')
    print(f'DeltaX gateway http://{HOST}:{PORT} | admin {"enabled" if len(PASSWORD)>=12 else "disabled"}',flush=True)
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()
