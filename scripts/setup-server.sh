#!/usr/bin/env bash
# One-time preparation of a fresh Ubuntu 24.04 Hetzner server for Postiz.
# Run as root from the repo folder:   sudo bash scripts/setup-server.sh
# Safe to re-run: it skips anything already done and never overwrites an existing .env.
set -euo pipefail

if [[ $EUID -ne 0 ]]; then echo "Run as root (sudo)." >&2; exit 1; fi
cd "$(dirname "$0")/.."

echo "==> Updating system packages"
apt-get update -y
DEBIAN_FRONTEND=noninteractive apt-get -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold upgrade -y
DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates curl git ufw unattended-upgrades openssl dnsutils

echo "==> Enabling automatic security updates"
dpkg-reconfigure -f noninteractive unattended-upgrades

echo "==> Installing Docker"
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
systemctl enable --now docker

echo "==> SSH: key-only login (passwords disabled)"
if [[ -s /root/.ssh/authorized_keys ]]; then
  cat > /etc/ssh/sshd_config.d/00-postiz-hardening.conf <<'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
  if sshd -t; then
    systemctl reload ssh 2>/dev/null || systemctl restart ssh 2>/dev/null || true
  else
    rm -f /etc/ssh/sshd_config.d/00-postiz-hardening.conf
    echo "    sshd config test failed - hardening skipped." >&2
  fi
else
  echo "    No SSH key found for root - skipped so you don't get locked out."
fi

echo "==> Firewall: allow SSH, HTTP, HTTPS only"
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw --force enable

echo "==> Adding 4G swap (protects against out-of-memory crashes)"
if ! swapon --show | grep -q /swapfile; then
  fallocate -l 4G /swapfile
  chmod 600 /swapfile
  mkswap /swapfile
  swapon /swapfile
  grep -q '^/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

echo "==> Kernel setting recommended for Elasticsearch"
echo 'vm.max_map_count=262144' > /etc/sysctl.d/99-elasticsearch.conf
sysctl --system >/dev/null

echo "==> Creating .env with random secrets"
if [[ ! -f .env ]]; then
  cp .env.example .env
  # hex secrets: no characters that would break the database URL
  sed -i "s|^JWT_SECRET=.*|JWT_SECRET=$(openssl rand -hex 48)|" .env
  sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(openssl rand -hex 24)|" .env
  sed -i "s|^TEMPORAL_DB_PASSWORD=.*|TEMPORAL_DB_PASSWORD=$(openssl rand -hex 24)|" .env
  chmod 600 .env
  echo "    .env created. Check POSTIZ_DOMAIN in it before starting."
else
  echo "    .env already exists - left untouched."
fi

DOMAIN=$(grep '^POSTIZ_DOMAIN=' .env | cut -d= -f2)
SERVER_IP=$(curl -fsS -4 https://ifconfig.me || true)
DNS_IP=$(dig +short A "$DOMAIN" | tail -n1)
echo
echo "==> DNS check for $DOMAIN"
echo "    This server's IPv4: ${SERVER_IP:-unknown}"
echo "    $DOMAIN resolves to: ${DNS_IP:-nothing yet}"
if [[ -n "$SERVER_IP" && "$SERVER_IP" == "$DNS_IP" ]]; then
  echo "    DNS OK. Start Postiz with:  docker compose up -d"
else
  echo "    DNS not pointing here yet. Add the A record at GoDaddy, wait, then: docker compose up -d"
fi

if [[ -f /var/run/reboot-required ]]; then
  echo
  echo "==> A reboot is required to finish updates. Run: reboot   (then ssh back in)"
fi
