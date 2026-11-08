#!/usr/bin/env bash
# Backs up the Postiz database and uploaded media into ./backups/<timestamp>/.
# Keeps the last 14 backups. Schedule daily with:
#   (crontab -l 2>/dev/null; echo "30 3 * * * cd $PWD && bash scripts/backup.sh >> backups/backup.log 2>&1") | crontab -
# Copy ./backups off the server too (e.g. Hetzner Storage Box) - a backup on the same disk is not enough.
set -euo pipefail
cd "$(dirname "$0")/.."

STAMP=$(date +%Y-%m-%d_%H%M)
DEST="backups/$STAMP"
mkdir -p "$DEST"

echo "[$STAMP] Dumping Postiz database"
docker exec postiz-postgres pg_dump -U postiz-user -d postiz-db-local -Fc > "$DEST/postiz-db.dump"

echo "[$STAMP] Archiving uploads"
docker run --rm -v postiz_postiz-uploads:/uploads:ro -v "$PWD/$DEST":/out alpine \
  tar czf /out/uploads.tar.gz -C /uploads .

cp .env "$DEST/env.backup"
chmod -R go-rwx "$DEST"

ls -1dt backups/20* | tail -n +15 | xargs -r rm -rf
echo "[$STAMP] Done: $DEST"
