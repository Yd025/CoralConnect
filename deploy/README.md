# Deploying coralconnectgt.tech

The live site runs three containers from `docker-compose.prod.yml`: the FastAPI engine (`workgate`), the Next.js site (`web`), and Caddy in front of both. Caddy serves `https://coralconnectgt.tech` and gets the certificate itself.

## First time on the server

1. DNS: an `A` record for `coralconnectgt.tech` pointing at the server (144.202.31.116).
2. Open ports 80 and 443 (TCP, plus 443/UDP for HTTP/3) in two places:
   - the server: `sudo ufw allow 80,443/tcp && sudo ufw allow 443/udp` (if ufw is on)
   - the cloud provider's firewall group for the server (Vultr: Network, Firewall)

   HTTPS timing out while plain HTTP works almost always means 443 is closed here.
3. Keys: `cp -n backend/.env.example backend/.env`, then set `XAI_API_KEY`. For a quick booth, set `GROK_MODEL` and `GROK_JUDGE_MODEL` to a fast, non-reasoning Grok model.
4. Start it:

   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

5. Check it:

   ```bash
   curl -sI https://coralconnectgt.tech | head -1        # HTTP/2 200
   curl -s https://coralconnectgt.tech/api/health        # "ok": true, "grokConfigured": true
   ```

If the server already runs Caddy for something else (the plugin installer), don't start a second one on ports 80 and 443. Add the `coralconnectgt.tech { ... }` block from `deploy/Caddyfile` to that Caddy's config instead, and point it at the `workgate` and `web` containers (or at `localhost:8080` and `localhost:3000` if you publish those ports).

## Every update

```bash
git pull
docker compose -f docker-compose.prod.yml up -d --build
```

Games are saved in the `coral-data` volume, so a rebuild keeps them. Run compose from the same folder each time: Docker names volumes after the folder, and a different folder starts with an empty save file.

The frontend build downloads its two fonts from Google Fonts, so the server needs internet while it builds.

## Settings worth knowing (backend/.env)

| Setting | Default | What it does |
| --- | --- | --- |
| `GROK_TIMEOUT` | 15 | Seconds to wait for Grok before one retry without web search. The retry keeps the short reply cap. |
| `GROK_CALLS_PER_MINUTE` | 120 | Spending cap across the server. Past it, turns are still graded and the reply is the round's written answer. |
| `GROK_IMAGES_PER_HOUR` | 40 | Grok Imagine rewards per hour. |
| `GROK_CONCURRENCY` | 8 | Grok calls in flight at once. |
| `SESSIONS_PER_IP` | 30 | New games one address can open in 10 minutes. Venue Wi-Fi can share one address, so keep it generous. |
| `IDLE_SESSION_HOURS` | 6 | Games with no activity this long are dropped from the save file. Result cards and the pair board stay. |

`GET /api/health` shows the values the server is using under `limits`.

## Local development

`docker compose up --build` (the dev file, `docker-compose.yml`) runs the same two apps with hot reload on ports 3000 and 8080, without Caddy. Without Docker, the backend needs Python 3.10 or newer.
