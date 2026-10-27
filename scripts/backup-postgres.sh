#!/usr/bin/env bash
set -euo pipefail

: "${DATABASE_URL:?Set DATABASE_URL to the PostgreSQL database to back up}"
backup_directory=${BACKUP_DIRECTORY:-./backups}
timestamp=$(date -u +%Y%m%dT%H%M%SZ)
backup_path="$backup_directory/dukkan-$timestamp.dump"

umask 077
mkdir -p -- "$backup_directory"
if [[ -e "$backup_path" ]]; then
  echo "Backup file already exists: $backup_path" >&2
  exit 1
fi

pg_dump --format=custom --no-owner --no-acl --dbname="$DATABASE_URL" --file="$backup_path"
pg_restore --list "$backup_path" >/dev/null
echo "Verified PostgreSQL backup: $backup_path"
