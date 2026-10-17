#!/bin/sh
# check.sh -- what the static job needs that files cannot say: "ok" or "WANTED" per fact. Changes nothing.
# Run by `fcpm check` on any machine whose names this folder's `names` holds. See CREW.md.
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
bad=0
say() {   # say OK WHAT [FIX]
  if [ "$1" = 0 ]; then echo "ok      $2"; else echo "WANTED  $2${3:+  -> $3}"; bad=$((bad + 1)); fi
}
dpkg-query -W -f='${Status}' jekyll 2>/dev/null | grep -q "install ok installed"
say $? "gear jekyll (jekyll)" "sudo apt-get install jekyll"
systemctl is-active -q fcpm-crew@static
say $? "the static job's supervisor, fcpm-crew@static" "sudo sh machines/crew.sh install static"
[ -f "$HOME/.local/state/fcpm/site/current/index.html" ]
say $? "the site built for the LAN" "sh $HERE/site-build (the job's site line, every 5 minutes)"
[ -f "$REPO/wix/site/index.html" ]
say $? "the Wix copy checked out" "git submodule update --init --checkout wix"
port=$(awk '$1 == "port:" { print $2 }' "$HERE/sites.yml")
python3 -I "$HERE/serve.py" list | while read -r name site folder; do
  code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: $name" "http://localhost:$port/")
  [ "$code" = 200 ]; say $? "serve answers $name ($site) on :$port" "the job's serve line (serve.py)"
  code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: $name" http://localhost/)
  [ "$code" = 200 ]; say $? "the door forwards $name" "a door from before static: it bounces on the next commit"
done | { out=$(cat); echo "$out"; case "$out" in *WANTED*) exit 1 ;; esac; }
[ $? = 0 ] || bad=$((bad + 1))
exit $bad
