(() => {
  'use strict';
  const grid = document.getElementById('round-grid');
  const icon = (name) => name === 'arrow'
    ? '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19 19 5M8 5h11v11"/></svg>'
    : '<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/></svg>';
  const validHttps = (value) => {
    try { const u = new URL(value); return u.protocol === 'https:' && Boolean(u.hostname) && !u.username && !u.password; }
    catch { return false; }
  };
  const defaults = [
    {number:'01',label:'WizTime & MathRally',kicker:'ROUND ONE',detail:'Enter round one'},
    {number:'02',label:'LevelUp',kicker:'ROUND TWO',detail:'Enter round two'},
    {number:'03',label:'GrandFinale',kicker:'FINAL ROUND',detail:'Enter the finale'}
  ];
  let previous = '';
  function renderRounds(rounds){
    const signature=JSON.stringify(rounds);
    if(signature===previous)return;
    previous=signature;
    grid.replaceChildren();
    defaults.forEach((base,index) => {
      const round = {...base,...(rounds[index] || {})};
      const available = round.enabled === true && validHttps(round.url);
      const card = document.createElement(available ? 'a' : 'article');
      card.className = `round-card ${available ? 'available' : 'locked'}`;
      if(available){card.href=round.url;card.rel='noopener noreferrer';card.setAttribute('aria-label',`Enter ${base.label}`);}
      else card.setAttribute('aria-label',`${base.label}, locked`);
      const top=document.createElement('div');top.className='round-card-top';
      const numbering=document.createElement('span');numbering.textContent=`${base.number} / ${base.kicker}`;
      const status=document.createElement('span');status.className='status';status.textContent=available?'ENTER ROUND':'LOCKED';
      top.append(numbering,status);
      const center=document.createElement('div');center.className='round-card-center';center.innerHTML=icon(available?'arrow':'lock');
      const bottom=document.createElement('div');bottom.className='round-card-bottom';
      const h=document.createElement('h3');h.textContent=base.label;
      const caption=document.createElement('span');caption.textContent=available?base.detail:'Not available yet';
      bottom.append(h,caption);card.append(top,center,bottom);grid.append(card);
    });
  }
  async function refreshRounds(){
    try {
      const response=await fetch('/api/rounds',{cache:'no-store'});
      if(!response.ok)throw Error('round status unavailable');
      const data=await response.json();
      if(!Array.isArray(data.rounds))throw Error('invalid round status');
      renderRounds(data.rounds);
    }catch(err){
      // Fail closed: never display a stale link as open after an error.
      renderRounds(defaults.map(r=>({...r,enabled:false,url:''})));
    }
  }
  refreshRounds();
  window.setInterval(()=>{if(!document.hidden)refreshRounds()},5000);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshRounds()});

  // If the authentic logo is supplied, display it; otherwise preserve a clean fallback.
  const logo = document.getElementById('event-logo');
  const fallback = document.getElementById('logo-fallback');
  logo.addEventListener('load', () => { if (logo.naturalWidth > 0) { logo.hidden = false; fallback.hidden = true; } });
  logo.addEventListener('error', () => { logo.hidden = true; fallback.hidden = false; });
  if (logo.complete && logo.naturalWidth > 0) { logo.hidden = false; fallback.hidden = true; }

  // The graph is the sole continuous animation. Freeze it for reduced motion.
  const path=document.getElementById('graph-path');
  const under=document.getElementById('graph-underlay');
  const point=document.getElementById('graph-point');
  const cross=document.getElementById('point-cross');
  const reduced=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const sampleCount=220;
  function frame(time){
    const t=reduced?0:time*0.00024;
    const f=x=>Math.sin(x-t)+.35*Math.sin(3*x+.6*t);
    const co=x=>[260+x*47,200-f(x)*75];
    const p=[];
    for(let i=0;i<=sampleCount;i++){
      const x=-5.6+11.2*i/sampleCount;
      const [px,py]=co(x);
      p.push(`${i?'L':'M'}${px.toFixed(1)} ${py.toFixed(1)}`);
    }
    const d=p.join(' ');
    path.setAttribute('d',d);under.setAttribute('d',d);
    const [px,py]=co(3.22);
    point.setAttribute('cx',px);point.setAttribute('cy',py);
    point.setAttribute('opacity','1');
    cross.setAttribute('d',`M${(px-13).toFixed(1)} ${py.toFixed(1)}h26 M${px.toFixed(1)} ${(py-13).toFixed(1)}v26`);
    cross.style.opacity='1';
    if(!reduced)window.requestAnimationFrame(frame);
  }
  window.requestAnimationFrame(frame);
})();
