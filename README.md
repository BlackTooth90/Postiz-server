# Postiz-server

Self-hosted [Postiz](https://postiz.com) on a Hetzner Cloud server, at **https://postiz.open2x.io**.

| File | Purpose |
|---|---|
| `docker-compose.yaml` | The whole stack: Caddy (HTTPS) + Postiz + Postgres + Redis + Temporal |
| `.env.example` | Settings template. Copied to `.env` (secrets, never committed) |
| `Caddyfile` | Reverse proxy; gets the Let's Encrypt certificate automatically |
| `dynamicconfig/` | Temporal config (from the official Postiz compose repo) |
| `scripts/setup-server.sh` | One-time server preparation (Docker, firewall, swap, secrets) |
| `scripts/backup.sh` | Database + uploads backup |

Only ports 22, 80 and 443 are open to the internet. Everything else stays internal.

---

## Step 1: Create the Hetzner server

1. Sign up at <https://console.hetzner.cloud>, then create a **Project** (e.g. `postiz`).
2. **Security → SSH Keys → Add SSH key.** Paste your public key (`~/.ssh/id_ed25519.pub`).
   If you don't have one, run `ssh-keygen -t ed25519` on your computer first.
3. **Add Server**:
   - **Location:** the one closest to you (e.g. Falkenstein/Nuremberg/Helsinki for Europe and the Middle East).
   - **Image:** Ubuntu 24.04.
   - **Type:** Shared vCPU, **x86** (Intel/AMD, not Arm), **4 vCPU / 8 GB RAM** (CX33 or the current equivalent).
   - **Networking:** keep **Public IPv4** on (GitHub and some social APIs need it).
   - **SSH key:** select yours.
   - **Backups:** turn on (+20% cost; daily snapshots of the whole server).
   - **Name:** `postiz`.
4. Optional: in **Firewalls**, create one allowing inbound TCP 22, 80, 443 and UDP 443, and attach it to the server.
   The setup script also enables a firewall on the server itself.
5. Copy the server's **IPv4 address**. You need it in step 2.

## Step 2: GoDaddy DNS (yes, one record is needed)

You keep owning `open2x.io` at GoDaddy. You only add a record that points the `postiz` subdomain at the server.

1. GoDaddy → **My Products → open2x.io → DNS** (Manage DNS).
2. **Add New Record:**

   | Type | Name | Value | TTL |
   |---|---|---|---|
   | `A` | `postiz` | *your Hetzner IPv4* | 600 seconds (or 1 hour) |

3. Save. Nothing else changes: your main site and email on `open2x.io` are not affected.

Notes:
- If the DNS page says your nameservers are **not** GoDaddy's (e.g. Cloudflare), add the record at that provider instead.
  If it's Cloudflare, set the record to **DNS only** (grey cloud), at least for the first start.
- Don't add an `AAAA` (IPv6) record unless you also want IPv6. If you add one, it must be the server's IPv6.
- Check it from your computer: `nslookup postiz.open2x.io` should return the server IP. It usually works within minutes, sometimes up to an hour.

## Step 3: Install Postiz on the server

```bash
ssh root@<SERVER_IP>

git clone https://github.com/BlackTooth90/Postiz-server.git
cd Postiz-server

bash scripts/setup-server.sh     # Docker, firewall, swap, creates .env with random secrets
nano .env                        # check POSTIZ_DOMAIN=postiz.open2x.io (secrets are already filled in)

docker compose up -d             # first start pulls images: ~3-5 minutes
docker compose ps                # wait until postiz shows "healthy"
docker compose logs -f postiz caddy   # Ctrl+C to stop watching
```

> If the repo is private, `git clone` asks for your GitHub username and a
> [personal access token](https://github.com/settings/tokens) (read-only, Contents) as the password.

Open **https://postiz.open2x.io** and **create your account**. The first account is yours.

Then close public sign-up:

```bash
sed -i 's/^DISABLE_REGISTRATION=.*/DISABLE_REGISTRATION=true/' .env
docker compose up -d
```

## Step 4: Connect LinkedIn

1. Go to <https://www.linkedin.com/developers/apps> and click **Create app**. LinkedIn requires a Company Page to attach the app to.
2. **Products** tab: add **Sign In with LinkedIn using OpenID Connect** and **Share on LinkedIn**.
   To post as a *Company Page*, also request **Community Management API**. LinkedIn reviews that one.
3. **Auth** tab, under Authorized redirect URLs, add:
   - `https://postiz.open2x.io/integrations/social/linkedin`
   - `https://postiz.open2x.io/integrations/social/linkedin-page` (only for company pages)
4. Copy the **Client ID** and **Client Secret** into `.env` (`LINKEDIN_CLIENT_ID`, `LINKEDIN_CLIENT_SECRET`), then run:
   ```bash
   docker compose up -d
   ```
5. In Postiz: **Add Channel → LinkedIn**, then log in and approve.

Other networks work the same way: create a developer app, set the callback
`https://postiz.open2x.io/integrations/social/<provider>`, put the keys in `.env` and run `docker compose up -d`.

## Step 5: Connect Postiz to Claude (MCP)

1. In Postiz: **Settings → Public API**. Copy the API key and the MCP URL shown there.
2. On claude.ai: **Settings → Connectors → Add custom connector**. Paste the MCP URL
   (on this server it is under `https://postiz.open2x.io/...`; use exactly what Postiz shows).
3. Start a new Claude session. Postiz tools are then available, the same way Typefully's are.

The API key can post on your behalf. Treat it like a password and only enter it in the connector settings.

## Maintenance

**Update Postiz:**
```bash
cd ~/Postiz-server
git pull
docker compose pull && docker compose up -d
docker image prune -f
```
Before updating, read the [Postiz release notes](https://github.com/gitroomhq/postiz-app/releases).
New versions sometimes add required services or settings. Compare with the
[official compose file](https://github.com/gitroomhq/postiz-docker-compose).
For predictable upgrades, pin `POSTIZ_VERSION` in `.env` instead of `latest`.

**Backups:**
```bash
bash scripts/backup.sh       # writes backups/<date>/ (database, uploads, .env)
# daily at 03:30:
(crontab -l 2>/dev/null; echo "30 3 * * * cd $HOME/Postiz-server && bash scripts/backup.sh >> backups/backup.log 2>&1") | crontab -
```
Also copy `backups/` off the server, e.g. to a Hetzner Storage Box with `rsync`.

**Restore the database:**
```bash
docker exec -i postiz-postgres pg_restore -U postiz-user -d postiz-db-local --clean < backups/<date>/postiz-db.dump
```

**Temporal dashboard** (for scheduled jobs), from your computer:
```bash
ssh -L 8080:localhost:8080 root@<SERVER_IP>    # then open http://localhost:8080
```

## Troubleshooting

| Symptom | Fix |
|---|---|
| Browser shows a certificate error | DNS wasn't pointing at the server when Caddy started. Check `nslookup postiz.open2x.io`, then run `docker compose restart caddy` and `docker compose logs caddy`. |
| `postiz` keeps restarting | Usually Temporal isn't ready. Check `docker compose logs temporal temporal-elasticsearch`. |
| Out of memory / very slow | Run `free -h`. 8 GB RAM is recommended; the setup script adds 4 GB swap. |
| Login works but you get logged out immediately | `POSTIZ_DOMAIN` must match the address you open, and you must use https. |
| Posts aren't published at the scheduled time | Check `docker compose logs postiz` and the Temporal dashboard. |
