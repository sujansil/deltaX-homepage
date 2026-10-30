# Delta X homepage

A standalone static homepage. No React build, npm packages, database or Python
virtual environment is needed. Python 3 is used only for local preview.
This package does not modify, start, stop or merge the round applications.

## Local setup

1. Extract this folder beside (not inside) the round projects.
2. Edit `dist/config.js`. R1 defaults to the known local address
   `http://127.0.0.1:8000/player/`. Set `r2` to the actual R2 player URL
   printed by R2 startup. It is intentionally blank until confirmed.
3. Start the round applications using their own supported startup commands.
   If both need port 8000, configure distinct ports before running together.
   Changing a homepage link does not change an application's listening port.
4. In this folder run `bash start.sh`.
5. Open `http://127.0.0.1:8080`. Click each round link to verify navigation.
   Press Ctrl+C in this terminal to stop only the homepage.

Round 3 remains disabled. Blank/invalid R1 or R2 URLs show "Link not configured".
Configured links do not indicate that the backend is online or the round open.
Ordinary navigation is used; authentication is owned by each round application.

## Files

- `dist/index.html`: page structure and text.
- `dist/style.css`: appearance and mobile layout.
- `dist/config.js`: the two round destinations; edit these without rebuilding.
- `dist/app.js`: loads and validates HTTP/HTTPS destinations.
- `start.sh`: loopback-only local preview on port 8080.

## Server deployment sequence

1. Prepare both current repositories, database migrations, server configuration
   and test scripts locally before creating the billed server.
2. Create the chosen VPS, configure SSH access and firewall, and install Docker
   Engine with Compose using the current supported instructions for its OS.
3. Deploy R1 and R2 with separate service identities, secrets and persistent
   database/media storage. Keep database/Redis ports private. Use process/container
   restart policies and logs; do not use the local development preview script
   unchanged as the production service manager.
4. Serve ONLY `dist/` as the public homepage with a reverse proxy such as Caddy
   or Nginx. Proxy round applications and R2 WebSockets appropriately.
5. Update `config.js` to reachable server URLs. Once a domain is available,
   use HTTPS destinations such as https://r1.YOUR_DOMAIN/player/ and the actual
   R2 player path under its own host. These are examples, not configured addresses.
6. Test account activation, login, content, media, session behavior and round
   transitions through those public URLs. Verify backups target the correct DB.
7. Run load tests with isolated test data on the intended server configuration.

Never publish localhost/127.0.0.1 round links for remote participants: those
addresses refer to each visitor's own machine. A public IP may be used for
initial smoke tests, but configure HTTPS before distributing real credentials.
The included Python preview server is for local use, not production hosting.

Exact deployment commands depend on the chosen server OS and both current
round repositories. This ZIP contains no server provisioning or reverse proxy
configuration and has not deployed any application.
