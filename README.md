# DeltaX homepage V3

A lightweight page plus a tiny standard-library Python server for secure round link control. R1, R2, R3 remain independent services; this server **never** changes their authentication or game state.

## Local preview

```bash
cd deltax-homepage-v3
export DELTAX_ADMIN_PASSWORD='choose-a-unique-password-at-least-12-characters'
python3 server.py
```

Visit http://localhost:5500/ for the page and http://localhost:5500/admin for round controls. On the admin page, enter the password above, supply HTTPS URLs for the round destinations, toggle round access, and click **Save round settings**.

Running `python3 -m http.server` is **not** supported in this version; use `server.py` because the admin and public round-state API require it.

## Deployment behind your existing Nginx

**Do not replace your entire Nginx configuration.** Make a backup and add/change only the main DeltaX homepage site's `location /` proxy. Leave the separate R1/R2/R3 server blocks unchanged.

On the VM, put this directory somewhere persistent, e.g. `/opt/deltax-homepage-v3`. Ensure the service account can write only to `data/` and never to the code directory.

Run it as a systemd service with a secure environment file (owned by root, mode 600) holding a strong unique `DELTAX_ADMIN_PASSWORD` and optionally `DELTAX_PORT=5500`. Run as a non-root account. Set `WorkingDirectory=/opt/deltax-homepage-v3` and `ExecStart=/usr/bin/python3 /opt/deltax-homepage-v3/server.py`.

In the **existing HTTPS homepage** Nginx `server` block, proxy to `http://127.0.0.1:5500`:

```nginx
location / {
    proxy_pass http://127.0.0.1:5500;
    proxy_set_header Host $http_host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
}
```

Keep HTTPS enabled; admin cookies are marked `Secure` when Nginx forwards `X-Forwarded-Proto: https`. **Never expose port 5500 directly on the public internet.** Prefer Nginx rate limiting or VPN/IP restrictions for `/admin` and `/api/admin/`. This example's built-in login throttle alone is not a complete internet perimeter defense. Disable caching for `/api/` at any CDN or proxy.

**Important:** If your existing homepage Nginx routing has special paths, inspect and preserve them. Test using `sudo nginx -t` before reloading. Use a process manager to restart the Python service automatically.

## Operational use

* Open `https://YOUR-HOMEPAGE-DOMAIN/admin` on your laptop or phone.
* Log in with the password defined in the service environment, set URLs and toggle the rounds, then **save**.
* Visitors on the homepage see changes automatically (polls every 5 seconds while the tab is visible).
* Admin session lasts up to four hours and resets on service restart. Password is never stored in the site's public files.
* Round status is saved atomically in `data/rounds.json`; back up this file. Default after missing/corrupt state is all rounds locked.
* Locking a card **does not prevent direct access** to an R1/R2/R3 URL. Round apps must enforce their own access policies.

## Visuals

Logo uses the provided poster extraction with reduced brightness and no halo. The background stays black. Only the mathematical function and its tracking point move. Reduced-motion devices show a stationary graph. All other elements remain still.
