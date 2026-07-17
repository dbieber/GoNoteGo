#!/bin/bash
# Go Note Go self-update with spoken progress and a rollback safety net.
#
# Invoked detached (nohup) by the ':update' command so it survives the
# service restart it performs. Flow:
#   1. Fetch origin/main; exit early if already up to date or if local
#      changes (or a non-main branch) would make updating unsafe.
#   2. Fast-forward to origin/main and install dependencies.
#   3. Verify the new version BEFORE restarting anything: byte-compile the
#      whole package, import the key entry points with the device venv, and
#      parse the supervisord config. Any failure rolls straight back.
#   4. Restart services, then confirm every supervisord program reaches
#      RUNNING. If not, roll back to the previous version and restart again.
# The device is never left stopped on a version that hasn't passed the
# pre-restart checks, and every failure path ends with services running the
# previous version.

set -u

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$REPO_DIR/env/bin/python"
PIP="$REPO_DIR/env/bin/pip"
SUPERVISORCTL="$REPO_DIR/env/bin/supervisorctl -c $REPO_DIR/gonotego/supervisord.conf -u go -p notego"
BRANCH="main"

if [ ! -x "$PYTHON" ]; then
  # Development machines without the device venv.
  PYTHON="$(command -v python3)"
  PIP="$PYTHON -m pip"
fi

speak() {
  echo "[update] $1"
  if command -v espeak >/dev/null 2>&1; then
    echo "$1" | espeak >/dev/null 2>&1 &
  elif command -v say >/dev/null 2>&1; then
    say "$1" >/dev/null 2>&1 &
  fi
}

cd "$REPO_DIR" || { speak "Update failed. Repository not found."; exit 1; }

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
if [ "$CURRENT_BRANCH" != "$BRANCH" ]; then
  speak "Not on the main branch. Update skipped."
  exit 1
fi

if [ -n "$(git status --porcelain --untracked-files=no)" ]; then
  speak "Update skipped. There are local changes."
  exit 1
fi

OLD_SHA="$(git rev-parse HEAD)"

speak "Checking for updates."
if ! git fetch origin "$BRANCH"; then
  speak "Update failed. Could not reach GitHub."
  exit 1
fi

NEW_SHA="$(git rev-parse "origin/$BRANCH")"
if [ "$OLD_SHA" = "$NEW_SHA" ]; then
  speak "Already up to date."
  exit 0
fi

rollback() {
  speak "Rolling back."
  git reset --hard "$OLD_SHA"
  $PIP install -e . >/dev/null 2>&1
}

COMMITS_BEHIND="$(git rev-list --count HEAD..origin/$BRANCH)"
speak "Updating Go Note Go. $COMMITS_BEHIND new commits."

if ! git merge --ff-only "origin/$BRANCH"; then
  speak "Update failed. The local version has diverged from main. No changes made."
  exit 1
fi

speak "Installing dependencies."
if ! $PIP install -e .; then
  rollback
  speak "Update failed while installing dependencies. Still on the previous version."
  exit 1
fi

speak "Verifying the new version."
verify() {
  $PYTHON -m compileall -q gonotego || return 1
  # Import the entry points that don't need root or audio hardware; this
  # exercises most third-party dependencies.
  $PYTHON -c "import gonotego.command_center.commands" || return 1
  $PYTHON -c "import gonotego.uploader.runner" || return 1
  $PYTHON -c "import gonotego.settings.server" || return 1
  $PYTHON -c "import gonotego.settings.network_watchdog" || return 1
  # Make sure the supervisord config at least parses.
  $PYTHON -c "
import configparser
parser = configparser.ConfigParser(strict=False)
assert parser.read('gonotego/supervisord.conf'), 'missing supervisord.conf'
assert any(section.startswith('program:') for section in parser.sections()), 'no programs configured'
" || return 1
  return 0
}

if ! verify; then
  rollback
  if verify; then
    speak "Update failed verification. Rolled back to the previous version. Services were not restarted."
    exit 1
  fi
  speak "Update failed verification, and rollback verification also failed. Not restarting services. Manual attention needed."
  exit 1
fi

speak "Restarting services."
$SUPERVISORCTL restart all

all_running() {
  local status
  status="$($SUPERVISORCTL status 2>/dev/null)"
  [ -n "$status" ] || return 1
  ! echo "$status" | grep -qvE 'RUNNING|STARTING' || return 1
  ! echo "$status" | grep -q 'STARTING' || return 1
  return 0
}

wait_until_running() {
  for _ in $(seq 1 12); do
    sleep 5
    if all_running; then
      return 0
    fi
  done
  return 1
}

if wait_until_running; then
  speak "Update complete. Now $COMMITS_BEHIND commits newer."
  exit 0
fi

speak "Services did not come back up. Rolling back."
rollback
$SUPERVISORCTL restart all
if wait_until_running; then
  speak "Rolled back to the previous version. Services are running."
else
  speak "Rollback restart is still unhealthy. Manual attention needed."
fi
exit 1
