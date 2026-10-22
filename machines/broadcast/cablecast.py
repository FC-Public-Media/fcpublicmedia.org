#!/usr/bin/env python3
"""cablecast — FCPM's hand on the broadcast box (Cablecast, channel 97), through its own API.

    python3 machines/broadcast/cablecast.py fields             each field in fields.yml: on the box or not
    python3 machines/broadcast/cablecast.py fields ensure      create the ones that are missing
    python3 machines/broadcast/cablecast.py snapshot [DATE]    a day of channel 1's schedule, kept as it was

The token is the one made in Cablecast for this work (Settings, API access) and kept in
~/.config/fcpm/cablecast.token, mode 600; nothing here prints it. The box is reached by its LAN
address; its certificate is checked against the public name it carries. Snapshots go to
~/.local/share/fcpm/cablecast/snapshots/. `fields ensure` creates and binds; it never changes or
deletes a field, and says so when one on the box differs from fields.yml. System python and PyYAML.
See PROFILE.md.
"""
import datetime
import http.client
import json
import pathlib
import ssl
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
ADDRESS = "10.1.10.84"
NAME = "fcpublicmedia.cablecast.tv"
API = "/CablecastAPI/v1"
LOCATION = 1
CHANNEL = 1
TOKEN = pathlib.Path.home() / ".config/fcpm/cablecast.token"
SNAPSHOTS = pathlib.Path.home() / ".local/share/fcpm/cablecast/snapshots"


def call(method, path, body=None):
    context = ssl.create_default_context()
    context.check_hostname = False  # reached by address; the name is checked below
    conn = http.client.HTTPSConnection(ADDRESS, context=context, timeout=30)
    headers = {"Authorization": f"Bearer {TOKEN.read_text().strip()}", "Accept": "application/json",
               "Host": NAME}
    if body is not None:
        headers["Content-Type"] = "application/json"
    conn.request(method, API + path, json.dumps(body) if body is not None else None, headers)
    names = [v for k, v in conn.sock.getpeercert().get("subjectAltName", ()) if k == "DNS"]
    if NAME not in names:
        sys.exit(f"the box at {ADDRESS} answered with a certificate for {names}, not {NAME}")
    reply = conn.getresponse()
    data = reply.read()
    if reply.status >= 300:
        sys.exit(f"{method} {path}: HTTP {reply.status} {data[:300]!r}")
    return json.loads(data) if data else {}


def fields(ensure):
    wanted = yaml.safe_load((HERE / "fields.yml").read_text())["fields"]
    box = call("GET", "/showfields")
    definitions = {d["name"]: d for d in box["fieldDefinitions"]}
    bound = {s["fieldDefinition"] for s in box["showFields"]}
    for field in wanted:
        name = field["name"]
        options = [str(o) for o in field.get("options", [])]
        have = definitions.get(name)
        if have is None:
            if not ensure:
                print(f"missing  {name}")
                continue
            have = call("POST", "/fielddefinitions", {"fieldDefinition": {
                "name": name, "type": field["type"], "widget": field["widget"], "location": LOCATION,
                "fieldOptions": [{"option": o, "position": i} for i, o in enumerate(options)]}})["fieldDefinition"]
            print(f"made     {name} (definition {have['id']})")
        else:
            on_box = [o["option"] for o in sorted(have["fieldOptions"], key=lambda o: o["position"])]
            if (have["type"], have["widget"], on_box) != (field["type"], field["widget"], options):
                print(f"differs  {name}: the box has {have['type']}/{have['widget']} {on_box}; left as it is")
            else:
                print(f"ok       {name} (definition {have['id']})")
        if have["id"] not in bound:
            if ensure:
                call("POST", "/showfields", {"showField": {"label": name, "fieldDefinition": have["id"]}})
                print(f"bound    {name} to shows")
            else:
                print(f"unbound  {name}")


def snapshot(day):
    start = datetime.date.fromisoformat(day)
    end = start + datetime.timedelta(days=1)
    items = call("GET", f"/scheduleitems?channel={CHANNEL}&start={start}T00:00:00&end={end}T00:00:00"
                        f"&page_size=1000")["scheduleItems"]
    SNAPSHOTS.mkdir(parents=True, exist_ok=True)
    out = SNAPSHOTS / f"channel{CHANNEL}_{start}_raw.json"
    out.write_text(json.dumps({"scheduleItems": items}, indent=1))
    print(f"{len(items)} airings, {len({i['show'] for i in items})} shows -> {out}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["fields"]:
        fields(args[1:] == ["ensure"])
    elif args[:1] == ["snapshot"]:
        snapshot(args[1] if len(args) > 1 else datetime.date.today().isoformat())
    else:
        sys.exit(__doc__)
