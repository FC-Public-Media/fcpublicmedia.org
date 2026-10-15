#!/bin/sh
# check.sh -- what digitization needs that files cannot say: "ok" or "WANTED" per fact. Changes nothing.
# Run by `fcpm check` or `machines/sync`. See PROFILE.md.
HERE=$(cd "$(dirname "$0")" && pwd)
bad=0
say() {   # say OK WHAT [FIX]
  if [ "$1" = 0 ]; then echo "ok      $2"; else echo "WANTED  $2${3:+  -> $3}"; bad=$((bad + 1)); fi
}

# Gear, from gear.yml: `package:` is an apt name, `at:` a path.
found=$(awk '/^[[:space:]]*- gear:/ { if (g) print g, p, a; g = $3; p = "-"; a = "-" }
     /^[[:space:]]*package:/ { p = $2 }
     /^[[:space:]]*at:/      { a = $2; gsub(/"/, "", a) }
     END { if (g) print g, p, a }' "$HERE/gear.yml" |
while read -r gear package at; do
  if [ "$package" != "-" ]; then
    dpkg-query -W -f='${Status}' "$package" 2>/dev/null | grep -q "install ok installed"
    say $? "gear $gear ($package)" "sudo apt-get install $package"
  elif [ "$at" != "-" ]; then
    case "$at" in "~/"*) at="$HOME/${at#\~/}" ;; esac
    [ -e "$at" ]; say $? "gear $gear at $at" "installed by hand"
  fi
done)
echo "$found"
case "$found" in *WANTED*) bad=1 ;; esac

# Facts the job runs on.
systemctl is-active -q fcpm-crew@digitization
say $? "the crew's supervisor, fcpm-crew@digitization" "sudo sh machines/crew.sh install digitization"
mountpoint -q /srv/origin
say $? "the origin mounted at /srv/origin"
mountpoint -q /srv/landing
say $? "the landing mounted at /srv/landing" \
  "a disk labelled fcpm-landing, and in /etc/fstab: LABEL=fcpm-landing /srv/landing ext4 defaults,nofail,noatime 0 2"
[ "$(timedatectl show -p NTPSynchronized --value 2>/dev/null)" = yes ]
say $? "the clock synchronized from the network" "sudo timedatectl set-ntp true"
[ -f /etc/ssh/sshd_config.d/10-no-passwords.conf ]
say $? "SSH takes keys only" "/etc/ssh/sshd_config.d/10-no-passwords.conf"
[ "$(cat /proc/sys/net/ipv4/ip_unprivileged_port_start)" -le 80 ]
say $? "the door may take port 80 without root" \
  "echo net.ipv4.ip_unprivileged_port_start=80 | sudo tee /etc/sysctl.d/50-fcpm-door.conf && sudo sysctl --system"
cmp -s "$HERE/fcpm-digitization.desktop" /etc/xdg/autostart/fcpm-digitization.desktop
say $? "the desktop starts the door and its page" "sudo cp $HERE/fcpm-digitization.desktop /etc/xdg/autostart/"
curl -fsS -o /dev/null http://localhost/revision
say $? "the door answers on port 80" "log out and in, or run $HERE/at-login"
exit $bad
