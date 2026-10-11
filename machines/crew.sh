#!/bin/sh
# crew.sh -- put a crew's one service on this Linux machine, or take it off. crew.ps1's twin.
#
#   crew.sh status    [CREW]   the service, and what its supervisor keeps (asked now)
#   crew.sh install   [CREW]   the service: starts with the computer, runs `crew.py serve`
#   crew.sh uninstall [CREW]   take the service away (what it started stops with it)
#
# One systemd instance per crew, fcpm-crew@<crew>, all under fcpm.target. See machines/README.md.
set -eu
REPO=$(cd "$(dirname "$0")/.." && pwd)
VERB=${1:-status}; CREW=${2:-production}
USER_=${SUDO_USER:-$(id -un)}
[ -f "$REPO/machines/$CREW/services" ] || { echo "no crew $CREW (machines/$CREW/services)"; exit 2; }
UNIT=fcpm-crew@$CREW.service

root() { [ "$(id -u)" = 0 ] || { exec sudo "$0" "$VERB" "$CREW"; }; }

case "$VERB" in
  status)
    echo "service   $(systemctl is-active "$UNIT" 2>/dev/null || true), $(systemctl is-enabled "$UNIT" 2>/dev/null || echo 'not installed: crew.sh install')"
    exec /usr/bin/python3 "$REPO/machines/crew.py" status "$CREW" ;;
  install)
    root
    python3 -c 'import yaml' 2>/dev/null || apt-get install -y -q python3-yaml >/dev/null
    sed -e "s|@REPO@|$REPO|g" -e "s|@USER@|$USER_|g" "$REPO/machines/fcpm-crew@.service" \
      > /etc/systemd/system/fcpm-crew@.service
    cp "$REPO/machines/fcpm.target" /etc/systemd/system/fcpm.target
    systemctl daemon-reload
    systemctl enable -q fcpm.target "$UNIT"
    systemctl restart "$UNIT"
    echo "$UNIT: $(systemctl is-active "$UNIT"), as $USER_, from $REPO" ;;
  uninstall)
    root
    systemctl disable -q --now "$UNIT" || true
    echo "$UNIT: removed" ;;
  *) sed -n '2,7p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
