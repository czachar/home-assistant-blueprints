#!/usr/bin/env bash
# Kopia konfiguracji Home Assistant do Git (Forgejo) — uruchamiane na CT111 `claude-lab` (timer raz na dobę).
# Pobiera WYBRANE pliki przez SSH (dodatek „Terminal & SSH”), bez sekretów; przed commitem skanuje treść pod kątem
# haseł/kluczy wpisanych jawnie (nie przez !secret) — przy trafieniu NIE commituje i kończy się błędem.
#   ha_config_sync.sh            — pobranie, skan, commit + push (jeśli są zmiany)
#   ha_config_sync.sh --dry-run  — pobranie i skan, bez commitu
set -euo pipefail

HA_HOST="${HA_HOST:-root@192.168.30.20}"
REPO="${HA_CONFIG_REPO:-$HOME/ha-config}"
DRY=0; [ "${1:-}" = "--dry-run" ] && DRY=1

INCLUDE=(configuration.yaml automations.yaml scenes.yaml scripts.yaml monitoring_reguly.yaml
         custom_templates packages blueprints themes esphome
         .storage/lovelace.lovelace .storage/lovelace.map .storage/lovelace_dashboards .storage/lovelace_resources)
EXCLUDE=(--exclude=secrets.yaml --exclude=esphome/secrets.yaml --exclude=esphome/.esphome --exclude=esphome/archive
         --exclude='*.db' --exclude='*.log' --exclude='__pycache__')

[ -d "$REPO/.git" ] || { echo "brak repozytorium $REPO (git clone z Forgejo)"; exit 1; }
cd "$REPO"
# czyste drzewo robocze = dokładny obraz wybranych plików (usunięcia w HA też trafiają do Gita)
git ls-files -z | grep -zv -E '^(README\.md|\.gitignore)$' | xargs -0 -r rm -f
find . -mindepth 1 -type d -not -path './.git*' -empty -delete 2>/dev/null || true
ssh -o BatchMode=yes "$HA_HOST" "cd /config && tar -czf - ${EXCLUDE[*]} ${INCLUDE[*]} 2>/dev/null" | tar -xzf -

# skan sekretów: klucz: wartość wpisana jawnie (nie !secret), klucze prywatne, długie ciągi base64 przy „key”
hits=$(grep -rnI -E \
  -e '(password|passwd|api_key|apikey|access_token|token|client_secret|psk|ota_password|network_key|encryption_key)[[:space:]]*:[[:space:]]*[^![:space:]#][^#]*$' \
  -e '(^|[^a-z_])key[[:space:]]*:[[:space:]]*["'"'"']?[A-Za-z0-9+/=]{24,}' \
  -e '-----BEGIN [A-Z ]*PRIVATE KEY' \
  --exclude-dir=.git . | grep -v -E ':[[:space:]]*(true|false|null|\[\]|"")[[:space:]]*$' || true)
if [ -n "$hits" ]; then
  echo "SKAN: możliwe sekrety — commit wstrzymany:"
  echo "$hits" | sed -E 's/(:[[:space:]]*).{4,}$/\1<ukryte>/' | cut -c1-160
  git checkout -q -- . 2>/dev/null || true
  exit 2
fi

git add -A
if git diff --cached --quiet; then echo "bez zmian"; exit 0; fi
git diff --cached --stat | tail -3
[ $DRY = 1 ] && { git reset -q; echo "(dry-run — bez commitu)"; exit 0; }
git -c user.name="claude-lab" -c user.email="claude-lab@forgejo.local" commit -q -m "HA config $(date '+%Y-%m-%d %H:%M')"
git push -q
echo "commit $(git rev-parse --short HEAD) wysłany"
