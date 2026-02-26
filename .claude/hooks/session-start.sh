#!/bin/bash
set -euo pipefail

# Only run in Claude Code remote (web) sessions
if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

echo "==> Installing Python dependencies..."
cd "$CLAUDE_PROJECT_DIR"
# uuid is a Python built-in; the PyPI package is broken — skip it
# --ignore-installed avoids conflicts with Debian-managed system packages
grep -v '^uuid$' requirements.txt | pip install -r /dev/stdin --quiet --ignore-installed

echo "==> Starting PostgreSQL..."
pg_ctlcluster 16 main start || true

# Wait for PostgreSQL to be ready (up to 15 seconds)
for i in {1..15}; do
  if sudo -u postgres psql -c "SELECT 1" > /dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "==> Configuring database..."
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'admin'" > /dev/null 2>&1 || true
sudo -u postgres psql -c "CREATE DATABASE marketplace_db" > /dev/null 2>&1 || true

echo "==> Setting environment variables..."
cat >> "$CLAUDE_ENV_FILE" << 'EOF'
export DJANGO_SETTINGS_MODULE=market_place.settings
export DATABASE_URL=postgres://postgres:admin@localhost:5432/marketplace_db
export RENDER=true
export DJANGO_DEBUG=True
export DJANGO_SECRET_KEY=dev-only-insecure-key-replace-in-production
EOF

echo "==> Session setup complete."
