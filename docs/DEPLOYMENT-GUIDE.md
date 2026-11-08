# Postiz on Hetzner: Step-by-Step Guide

Goal: Postiz running at **https://postiz.open2x.io**, with LinkedIn connected, and Claude able to schedule posts.

Expect about 1–2 hours for the whole thing. LinkedIn app approval can add waiting time.

---

## Checklist

- [ ] Part 1: Create an SSH key on your computer
- [ ] Part 2: Create a Hetzner account
- [ ] Part 3: Create the Hetzner firewall
- [ ] Part 4: Create the Hetzner server
- [ ] Part 5: Add the DNS record at GoDaddy
- [ ] Part 6: Log in to the server
- [ ] Part 7: Download this repo onto the server
- [ ] Part 8: Run the setup script
- [ ] Part 9: Start Postiz
- [ ] Part 10: Create your Postiz account and close registration
- [ ] Part 11: Create the LinkedIn app
- [ ] Part 12: Connect LinkedIn in Postiz and send a test post
- [ ] Part 13: Connect Postiz to Claude
- [ ] Part 14: Turn on backups
- [ ] Part 15: Monthly updates

---

## Part 1: Create an SSH key on your computer

An SSH key lets you log in to the server securely, without a password. You create it once on your own computer.

### Windows 10/11
1. Press **Start**, type **PowerShell**, and open it.
2. Check whether you already have a key:
   ```powershell
   Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
   ```
   - If it prints a line starting with `ssh-ed25519 ...`, you already have a key. Skip to step 5.
   - If it says the file cannot be found, continue.
3. Create a key:
   ```powershell
   ssh-keygen -t ed25519 -C "postiz-server"
   ```
   - "Enter file in which to save the key": press **Enter** to accept the default.
   - "Enter passphrase": type a passphrase you will remember (recommended), or press Enter for none. Repeat it.
4. Show the public key:
   ```powershell
   Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub
   ```
5. Select the whole line (it starts with `ssh-ed25519`) and copy it. You'll paste it into Hetzner in Part 4.

### macOS / Linux
1. Open **Terminal**.
2. Check for an existing key: `cat ~/.ssh/id_ed25519.pub`. If it prints `ssh-ed25519 ...`, skip to step 4.
3. Create one: `ssh-keygen -t ed25519 -C "postiz-server"`. Press Enter for the default location, then set a passphrase.
4. Copy the output of `cat ~/.ssh/id_ed25519.pub`.

> The file **without** `.pub` (`id_ed25519`) is your private key. Never share it or upload it anywhere.

---

## Part 2: Create a Hetzner account

1. Go to <https://accounts.hetzner.com/signUp> and register with your email.
2. Confirm your email, then fill in your name and address.
3. Add a payment method (credit card or PayPal).
   Hetzner sometimes asks for **identity verification** (an ID photo) for new accounts. This can take from a few minutes to a day.
4. Open <https://console.hetzner.cloud>.
5. Click **+ New project**, name it `postiz`, and click **Add project**. Click the project to open it.

---

## Part 3: Create the Hetzner firewall

This blocks everything except SSH and web traffic, before the server even starts.

1. In the `postiz` project, click **Firewalls** in the left menu, then **Create Firewall**.
2. **Inbound rules.** Two rules already exist (SSH TCP 22 and ICMP). Keep them, then click **Add rule** three times to add:

   | IPs | Protocol | Port | Description |
   |---|---|---|---|
   | Any IPv4, Any IPv6 | TCP | 80 | HTTP (needed for the certificate) |
   | Any IPv4, Any IPv6 | TCP | 443 | HTTPS |
   | Any IPv4, Any IPv6 | UDP | 443 | HTTP/3 (optional) |

3. **Outbound rules:** leave empty. Empty means all outgoing traffic is allowed, which the server needs.
4. **Apply to:** leave empty for now. You'll attach it while creating the server.
5. **Name:** `postiz-firewall`. Click **Create Firewall**.

---

## Part 4: Create the Hetzner server

1. In the left menu, click **Servers**, then **Add Server** (on newer layouts: **Create Resource → Servers**).
2. Fill in each section:

   **Location**
   Pick the one closest to you and your audience:
   Falkenstein or Nuremberg (Germany), or Helsinki (Finland), for Europe and the Middle East.
   Ashburn or Hillsboro for the USA; Singapore for Asia.

   **Image**
   **OS Images → Ubuntu → 24.04**.

   **Type**
   - Choose **Shared vCPU**, then **x86 (Intel/AMD)**. Don't choose Arm (CAX).
   - Pick the plan with **4 vCPU / 8 GB RAM** (currently called **CX33**; older accounts may show CX32).
   - The price is shown per month. Expect roughly €7–15.

   **Networking**
   - **Public IPv4:** ✅ on. It costs a small extra, but some services need IPv4.
   - **Public IPv6:** ✅ on (free).

   **SSH keys**
   - Click **Add SSH key**, paste the line you copied in Part 1, name it (e.g. `my-laptop`), and click **Add SSH key**.
   - Make sure it is **selected** (ticked).

   **Volumes:** none.

   **Firewalls:** tick **postiz-firewall**.

   **Backups:** ✅ on. It costs +20% of the server price and keeps 7 daily snapshots of the whole server.

   **Placement groups / Labels / Cloud config:** leave empty.

   **Name:** `postiz`.

3. Click **Create & Buy now**. The server is ready in about 30 seconds.
4. Click the server and **copy the IPv4 address** (e.g. `65.21.x.x`). This guide calls it `<SERVER_IP>`.

> Because you added an SSH key, Hetzner does not email you a root password. That's expected: you log in with the key.

---

## Part 5: Add the DNS record at GoDaddy

This makes `postiz.open2x.io` point at your new server. Your website and email on `open2x.io` keep working as before.

1. Log in at <https://www.godaddy.com>.
2. Click your name (top right), then **My Products**.
3. Under **Domains**, find **open2x.io** and click **DNS** (or click the domain, then the **DNS** tab).
4. **Check who manages DNS.** Scroll to **Nameservers**.
   - If they look like `ns##.domaincontrol.com`, GoDaddy manages DNS. Continue here.
   - If they're something else (e.g. `*.ns.cloudflare.com`), add the same record at that provider instead. On Cloudflare, set **Proxy status = DNS only** (grey cloud).
5. In the records list, check that there is **no existing record named `postiz`**. If there is one (A or CNAME), delete it or edit it instead of adding a new one.
6. Click **Add New Record** (or **Add**) and fill in:
   - **Type:** `A`
   - **Name:** `postiz` (just the word, not the full domain)
   - **Value / Points to:** `<SERVER_IP>`
   - **TTL:** `600 seconds` (choose **Custom** if needed), or `1/2 Hour`
7. Click **Save**.
8. Optional: add an IPv6 record too. **Type** `AAAA`, **Name** `postiz`, **Value** = the server's IPv6 from Hetzner, ending in `::1` (e.g. `2a01:4f8:xxxx:xxxx::1`).
9. **Verify** (it usually works within 5–30 minutes):
   - Windows PowerShell: `nslookup postiz.open2x.io 8.8.8.8`
   - macOS/Linux: `dig +short postiz.open2x.io @8.8.8.8`
   - Or in a browser: <https://dnschecker.org/#A/postiz.open2x.io>

   The answer must be your `<SERVER_IP>`. You can carry on with Parts 6–8 while waiting, but **don't start Postiz (Part 9) until this resolves**.

---

## Part 6: Log in to the server

1. On your computer, open PowerShell (Windows) or Terminal (macOS/Linux).
2. Run:
   ```bash
   ssh root@<SERVER_IP>
   ```
3. The first time, it asks `Are you sure you want to continue connecting (yes/no)?`. Type `yes` and press Enter.
4. If you set a passphrase in Part 1, type it.
5. You're in when the prompt looks like `root@postiz:~#`.

Problems:
- `Permission denied (publickey)`: the key wasn't selected when you created the server. Fix it in Hetzner under **Server → Rescue → Reset root password**, or create the server again with the key ticked.
- Connection timeout: check that the firewall from Part 3 has the SSH rule (TCP 22).

---

## Part 7: Download this repo onto the server

Run these on the server (after `root@postiz:~#`).

### If the GitHub repo is public
```bash
git clone -b claude/exciting-cray-qpcizt https://github.com/BlackTooth90/Postiz-server.git
cd Postiz-server
```
(Once the branch is merged into `main`, you can drop `-b claude/exciting-cray-qpcizt`.)

### If the repo is private
You need a GitHub token, which works like a read-only password:
1. On your computer, open <https://github.com/settings/personal-access-tokens/new>.
2. **Token name:** `postiz-server`. **Expiration:** 1 year (or what you prefer).
3. **Repository access:** **Only select repositories**, then choose **BlackTooth90/Postiz-server**.
4. **Permissions → Repository permissions → Contents:** **Read-only**.
5. Click **Generate token** and copy it. It is shown only once.
6. On the server:
   ```bash
   git clone -b claude/exciting-cray-qpcizt https://github.com/BlackTooth90/Postiz-server.git
   ```
   - Username: `BlackTooth90`
   - Password: **paste the token** (nothing appears while you paste; that's normal) and press Enter.
7. `cd Postiz-server`

---

## Part 8: Run the setup script

```bash
bash scripts/setup-server.sh
```

What it does, step by step (takes 2–5 minutes):
1. Updates Ubuntu and installs basic tools.
2. Turns on automatic security updates.
3. Installs Docker.
4. Disables password login over SSH, so only your key works.
5. Turns on the firewall on the server too (ports 22, 80, 443).
6. Adds 4 GB of swap memory, a safety net against running out of RAM.
7. Applies a kernel setting Elasticsearch needs.
8. Creates `.env` with **random passwords** already filled in.
9. Checks whether `postiz.open2x.io` points to this server.

At the end you'll see either:
- `DNS OK. Start Postiz with: docker compose up -d`, or
- `DNS not pointing here yet...`. Wait and check again later with `dig +short postiz.open2x.io`.

If it says **"A reboot is required"**:
```bash
reboot
```
Wait 30 seconds, reconnect with `ssh root@<SERVER_IP>`, then `cd Postiz-server`.

### Check the settings file
```bash
nano .env
```
- Make sure the first setting reads `POSTIZ_DOMAIN=postiz.open2x.io`.
- `JWT_SECRET`, `POSTGRES_PASSWORD` and `TEMPORAL_DB_PASSWORD` should be long random strings, not `change-me`.
- Save and exit nano: **Ctrl+O**, **Enter**, then **Ctrl+X**.

> Don't change the passwords after the first start. The databases are created with them.

---

## Part 9: Start Postiz

Only do this once Part 5 step 9 shows your server IP.

```bash
docker compose up -d
```
The first run downloads about 3 GB of images (2–5 minutes). Then check the status:

```bash
docker compose ps
```
Run it again every 30 seconds or so. You're waiting for:
- `postiz-postgres`, `postiz-redis`, `temporal-postgresql`, `temporal-elasticsearch`, `temporal`: **healthy**
- `postiz`: **healthy** (this one can take 2–4 minutes)
- `caddy`, `temporal-ui`: **running** / Up

Check that the HTTPS certificate was issued:
```bash
docker compose logs caddy | grep -i "certificate obtained"
```
You should see a line containing `certificate obtained successfully` and `postiz.open2x.io`.

To watch Postiz start (press Ctrl+C to stop watching; Postiz keeps running):
```bash
docker compose logs -f postiz
```

If something is wrong, see **Troubleshooting** at the end of this guide.

---

## Part 10: Create your Postiz account and close registration

1. In your browser, open **https://postiz.open2x.io**. You should see a padlock and the Postiz sign-in page.
2. Click **Sign up** and enter your name, email, password and company name (e.g. `Open2x`).
   No email service is configured, so Postiz should activate the account directly without a confirmation email.
3. You land on the Postiz dashboard.
4. **Close registration** so nobody else can sign up. Back on the server:
   ```bash
   cd ~/Postiz-server
   sed -i 's/^DISABLE_REGISTRATION=.*/DISABLE_REGISTRATION=true/' .env
   docker compose up -d
   ```
   Postiz restarts (about 1–2 minutes).
5. Test it: open https://postiz.open2x.io in a private/incognito window. Sign-up should no longer be possible.

---

## Part 11: Create the LinkedIn app

LinkedIn only lets apps post if the app is linked to a **LinkedIn Company Page** that you administer.

### 11.1 Make sure you have a Company Page
- If you already admin an `Open2x` page, skip ahead.
- Otherwise: on linkedin.com, click **For Business** (top right), then **Create a Company Page**, choose **Company**, and fill in the name, URL and logo.

### 11.2 Create the app
1. Go to <https://www.linkedin.com/developers/apps> and click **Create app**.
2. Fill in:
   - **App name:** `Open2x Postiz`
   - **LinkedIn Page:** search for and select your company page.
   - **Privacy policy URL:** optional (e.g. `https://open2x.io/privacy` if you have one).
   - **App logo:** upload any square image (required).
   - Tick the legal agreement and click **Create app**.

### 11.3 Verify the app with your page
1. In the app, open the **Settings** tab. Next to the company page, click **Verify**.
2. Click **Generate URL**, then open that URL yourself (you're the page admin) and click **Verify**.
3. Back in the app, it should show **Verified**.

### 11.4 Add the products
1. Open the **Products** tab.
2. Find **Share on LinkedIn**, click **Request access**, tick the terms and confirm. It's usually approved instantly.
3. Find **Sign In with LinkedIn using OpenID Connect**, click **Request access** and confirm. Also instant.
4. *(Only if you want to post as the company page, not just your personal profile.)* Request **Community Management API**.
   LinkedIn reviews this manually and may ask you to use a separate app just for it, plus business verification. Start with your personal profile; you can add this later.

### 11.5 Set the redirect URL and copy the keys
1. Open the **Auth** tab.
2. Under **OAuth 2.0 settings → Authorized redirect URLs for your app**, click the pencil, then **+ Add redirect URL**, and add:
   ```
   https://postiz.open2x.io/integrations/social/linkedin
   ```
   (For a company page later, also add `https://postiz.open2x.io/integrations/social/linkedin-page`.)
   Click **Update**.
3. At the top of the **Auth** tab, copy the **Client ID** and **Primary Client Secret** (click the eye icon to reveal it).

### 11.6 Put the keys on the server
```bash
cd ~/Postiz-server
nano .env
```
Fill in:
```
LINKEDIN_CLIENT_ID=paste-client-id
LINKEDIN_CLIENT_SECRET=paste-client-secret
```
Save (**Ctrl+O**, **Enter**, **Ctrl+X**), then apply:
```bash
docker compose up -d
```
Wait until `docker compose ps` shows postiz as **healthy** again.

---

## Part 12: Connect LinkedIn in Postiz and send a test post

1. Open https://postiz.open2x.io.
2. Click **Add Channel**, then **LinkedIn**.
3. LinkedIn opens. Log in if needed and click **Allow**.
4. You return to Postiz, with your LinkedIn profile listed as a channel.
5. **Test:** click **Create Post**, choose the LinkedIn channel, write `Test post from Postiz`, set the time to 5 minutes from now, and click **Add to calendar** / **Schedule**.
6. After 5 minutes, check your LinkedIn profile. The post should be there. Delete it on LinkedIn afterwards if you like.

> LinkedIn logins expire after about **60 days**. When Postiz shows the channel as disconnected, click it and reconnect. It takes 10 seconds.

---

## Part 13: Connect Postiz to Claude

1. In Postiz, open **Settings** and find the **Public API** section.
2. Copy the **API key** and the **MCP URL** shown there. On this server it should start with `https://postiz.open2x.io/`.
3. Go to <https://claude.ai> and open **Settings → Connectors**.
4. Click **Add custom connector**:
   - **Name:** `Postiz`
   - **Remote MCP server URL:** paste the MCP URL from Postiz.
   - If there's an **advanced / header** option and Postiz offers the Bearer method: use the URL ending in `/mcp` and set `Authorization: Bearer <API key>`.
   - Click **Add**.
5. Start a **new** Claude conversation or Claude Code session and ask: *"List my Postiz channels."* You should see LinkedIn.
6. From then on you can say things like: *"Draft a LinkedIn post about X and schedule it for Tuesday 9:00."*

> The API key can post on your behalf. Only paste it into the connector settings, never into a chat. If it leaks, generate a new one in Postiz Settings.

---

## Part 14: Turn on backups

The Hetzner backups from Part 4 protect the whole server. This adds an app-level backup that is easier to restore.

```bash
cd ~/Postiz-server
bash scripts/backup.sh            # first test run
ls backups/                        # you should see a dated folder
```

Run it automatically every night at 03:30:
```bash
(crontab -l 2>/dev/null; echo "30 3 * * * cd $HOME/Postiz-server && bash scripts/backup.sh >> backups/backup.log 2>&1") | crontab -
crontab -l                         # confirm the line is there
```

### Optional: off-server copies (recommended)
1. In Hetzner, order a **Storage Box** (smallest size, ~€3–4/month) and enable **SSH support** in its settings.
2. On the server:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/storagebox -N ""
   cat ~/.ssh/storagebox.pub
   ```
   Add that key to the Storage Box: Hetzner Console → Storage Box → **SSH keys**, or follow Hetzner's Storage Box SSH key guide.
3. Copy the backups there each night, 30 minutes after the backup (replace `uXXXXX` with your Storage Box user):
   ```bash
   (crontab -l; echo "0 4 * * * rsync -az -e 'ssh -p 23 -i /root/.ssh/storagebox' $HOME/Postiz-server/backups/ uXXXXX@uXXXXX.your-storagebox.de:postiz-backups/") | crontab -
   ```

### Restoring the database
```bash
cd ~/Postiz-server
docker exec -i postiz-postgres pg_restore -U postiz-user -d postiz-db-local --clean < backups/<date>/postiz-db.dump
docker compose restart postiz
```

---

## Part 15: Monthly updates

1. Read what changed: <https://github.com/gitroomhq/postiz-app/releases>. Look for "breaking" or "migration".
2. Make a backup first:
   ```bash
   cd ~/Postiz-server
   bash scripts/backup.sh
   ```
3. Update:
   ```bash
   git pull
   docker compose pull
   docker compose up -d
   docker image prune -f
   ```
4. Check `docker compose ps` until postiz is **healthy**, then open the site.

Ubuntu security updates install automatically. If `ls /var/run/reboot-required` ever exists, run `reboot` at a quiet time.

---

## Troubleshooting

| Problem | What to run / do |
|---|---|
| Browser: "connection not private" / certificate error | DNS wasn't ready when Caddy started. Check `dig +short postiz.open2x.io` shows the server IP, then `docker compose restart caddy` and `docker compose logs caddy`. |
| Browser: site can't be reached | `docker compose ps`: is caddy up? Check that the Hetzner firewall has TCP 80 and 443. |
| `postiz` keeps restarting or stays "starting" | `docker compose logs --tail=100 postiz` and `docker compose logs --tail=100 temporal`. Temporal must be healthy first. |
| `temporal-elasticsearch` unhealthy | `docker compose logs temporal-elasticsearch`. Often a lack of disk space (`df -h`) or memory (`free -h`). |
| Logged out right after logging in | Make sure you open exactly `https://postiz.open2x.io` and `POSTIZ_DOMAIN` in `.env` matches. |
| LinkedIn: "redirect_uri does not match" | The redirect URL in the LinkedIn **Auth** tab must be exactly `https://postiz.open2x.io/integrations/social/linkedin`. |
| LinkedIn connected but the post failed | Check the **Share on LinkedIn** product is approved, and look at `docker compose logs postiz`. |
| Scheduled post didn't go out | Check the Temporal dashboard: on your computer run `ssh -L 8080:localhost:8080 root@<SERVER_IP>`, then open http://localhost:8080. |
| Server very slow | `free -h` and `docker stats`. Upgrade the server size in Hetzner (Server → Rescale) if needed. |

**Restart everything:** `cd ~/Postiz-server && docker compose restart`

**Stop everything:** `docker compose down`. This keeps your data. Never add `-v`, because that **deletes all data**.
