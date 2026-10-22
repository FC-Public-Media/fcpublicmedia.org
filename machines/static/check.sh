#!/bin/sh
# check.sh -- what the static job needs that files cannot say: "ok" or "WANTED" per fact. Changes nothing.
# Run by `fcpm check` on any machine whose names this folder's `names` holds. See CREW.md.
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
bad=0
say() {   # say OK WHAT [FIX]
  if [ "$1" = 0 ]; then echo "ok      $2"; else echo "WANTED  $2${3:+  -> $3}"; bad=$((bad + 1)); fi
}
for package in nginx-light jekyll rsync python3-yaml; do
  dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"
  say $? "gear $package" "sudo apt-get install $package"
done
cmp -s "$HERE/nginx.conf" /etc/nginx/sites-available/fcpm && [ -L /etc/nginx/sites-enabled/fcpm ] &&
  [ ! -e /etc/nginx/sites-enabled/default ]
say $? "nginx carries nginx.conf, and nothing else" "sudo sh $HERE/install"
systemctl is-active -q nginx && curl -sI http://localhost/ | grep -qi '^server: nginx'
say $? "nginx holds port 80" "sudo sh $HERE/install"
! systemctl is-active -q fcpm-crew@static
say $? "serve.py's old supervisor is gone" "sudo systemctl disable --now fcpm-crew@static"
[ -f "$REPO/wix/site/index.html" ]
say $? "the Wix copy checked out" "git submodule update --init --checkout wix"
python3 -I "$HERE/publish.py" list | while read -r name site folder; do
  [ -f "$folder/index.html" ]; say $? "$site published, $folder" "python3 $HERE/publish.py"
  code=$(curl -s -o /dev/null -w '%{http_code}' -H "Host: $name" http://localhost/)
  [ "$code" = 200 ]; say $? "nginx serves $name ($site)" "sudo sh $HERE/install"
  code=$(curl -s -o /dev/null -w '%{http_code}' -r 0-0 -H "Host: $name" http://localhost/)
  [ "$code" = 206 ]; say $? "nginx serves $name in pieces (Range), as Safari plays video" "sudo sh $HERE/install"
done | { out=$(cat); echo "$out"; case "$out" in *WANTED*) exit 1 ;; esac; }
[ $? = 0 ] || bad=$((bad + 1))
exit $bad
