#!/usr/bin/env python3
"""cablecast — FCPM's hand on the broadcast box (Cablecast, channel 97), through its own API.

    python3 machines/broadcast/cablecast.py fields             each field in fields.yml: on the box or not
    python3 machines/broadcast/cablecast.py fields ensure      create the ones that are missing
    python3 machines/broadcast/cablecast.py snapshot [DATE]    a day of channel 1's schedule, kept as it was
    python3 machines/broadcast/cablecast.py eject DIR          the box's look, as plain files, into DIR

The token is the one made in Cablecast for this work (Settings, API access) and kept in
~/.config/fcpm/cablecast.token, mode 600; nothing here prints it. The box is reached by its LAN
address; its certificate is checked against the public name it carries. Snapshots go to
~/.local/share/fcpm/cablecast/snapshots/. `fields ensure` creates and binds; it never changes or
deletes a field, and says so when one on the box differs from fields.yml. `eject` writes what the
box shows people into a checkout of the broadcast repository (PROFILE.md, "The look"): the same
files each time for the same box, so git shows only what changed there. System python and PyYAML.
See PROFILE.md.
"""
import datetime
import http.client
import json
import pathlib
import re
import ssl
import sys

import yaml

HERE = pathlib.Path(__file__).resolve().parent
ADDRESS = "10.1.10.84"
NAME = "fcpublicmedia.cablecast.tv"
API = "/CablecastAPI/v1"
LOCATION = 1
CHANNEL = 1
BOARD = 2  # the bulletin board's own channel number, in Cablecast CG
TOKEN = pathlib.Path.home() / ".config/fcpm/cablecast.token"
SNAPSHOTS = pathlib.Path.home() / ".local/share/fcpm/cablecast/snapshots"


def fetch(method, path, body=None):
    """Bytes from the box at `path` (from the server root), after its certificate shows its name."""
    context = ssl.create_default_context()
    context.check_hostname = False  # reached by address; the name is checked below
    conn = http.client.HTTPSConnection(ADDRESS, context=context, timeout=60)
    headers = {"Authorization": f"Bearer {TOKEN.read_text().strip()}", "Host": NAME}
    if body is not None:
        headers["Content-Type"] = "application/json"
    conn.request(method, path, json.dumps(body) if body is not None else None, headers)
    names = [v for k, v in conn.sock.getpeercert().get("subjectAltName", ()) if k == "DNS"]
    if NAME not in names:
        sys.exit(f"the box at {ADDRESS} answered with a certificate for {names}, not {NAME}")
    reply = conn.getresponse()
    data = reply.read()
    if reply.status >= 300:
        sys.exit(f"{method} {path}: HTTP {reply.status} {data[:300]!r}")
    return data


def call(method, path, body=None):
    data = fetch(method, API + path, body)
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

# The bulletin board's zone kinds, as Cablecast names them, in plain words. Pictures and images
# are files; the rest the board draws itself each time.
KINDS = {
    "TRMS.Components.Imaging.TRMSImage": "art",
    "TRMS.Components.Picture.TRMSPicture": "slides",
    "TRMS.Components.Clock.TRMSClock": "clock (drawn by the board)",
    "TRMS.Components.RSSBulletin.TRMSRSSBulletin": "news feed (drawn by the board)",
    "TRMS.Components.CableDisplay.TRMSCableDisplay": "schedule (drawn by the board)",
    "TRMS.Components.Weather.TRMSWeather": "weather (drawn by the board)",
}
SITE = ["siteName", "aboutPageShortDescription", "aboutPageDescription", "contactEmail", "contactPhone",
        "facebookUrl", "twitterUrl", "blogUrl", "customColor1", "customColor2", "customColor3",
        "customColor4", "primaryButtonColor", "secondaryButtonColor", "bodyButtonColor", "customCSS"]


def put(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode()
    if not path.exists() or path.read_bytes() != data:
        path.write_bytes(data)


class Plain(yaml.SafeDumper):
    """Short lists on one line, text with line breaks as a block, so a person can read the file."""


Plain.add_representer(str, lambda d, s: d.represent_scalar(
    "tag:yaml.org,2002:str", s, style="|" if "\n" in s else None))


def written(head, value):
    return head + yaml.dump(value, Dumper=Plain, sort_keys=False, allow_unicode=True, width=100,
                            default_flow_style=None)


def image(path, data):
    """Write a picture under the name its bytes call for (the box serves PNGs as .jpg)."""
    name = path.with_suffix(".png" if data[:8] == b"\x89PNG\r\n\x1a\n" else ".jpg")
    put(name, data)
    return name.name


def keep_only(folder, names):
    for old in folder.glob("*") if folder.is_dir() else ():
        if old.name not in names:
            old.unlink()


def changed(ticks):
    """The date in a board image's ?t= stamp (.NET ticks)."""
    return (datetime.datetime(1, 1, 1) + datetime.timedelta(microseconds=int(ticks) // 10)).date().isoformat()


def eject(into):
    out = pathlib.Path(into)
    site = call("GET", "/publicsites/1")["publicSite"]
    put(out / "website/logo.png", fetch("GET", f"/CablecastAPI/dynamicthumbnails/{site['logo']}"))
    put(out / "website/logo-square.png", fetch("GET", f"/CablecastAPI/dynamicthumbnails/{site['squareLogo']}"))
    put(out / "website/site.yml", written(
        "# The public website (the Internet Channel): its words, links and colours. Colours are hex,\n"
        "# without the #. The logos are logo.png and logo-square.png beside this file. Names are\n"
        "# Cablecast's own, so each line is the setting of the same name on the box.\n",
        {k: site.get(k) for k in SITE} | {"showPageFields": [
            {"label": f["label"].strip(" :"), "field": f["field"] or f"show field {f['showField']}"}
            for f in sorted(site["fieldDisplays"], key=lambda f: f["order"])]}))
    galleries = call("GET", "/sitegalleries?public_site=1")["siteGalleries"]
    put(out / "website/galleries.yml", written(
        "# The rows on the website's home page, top to bottom. Each row is a saved search in\n"
        "# Cablecast (by its number); `shows` is how many it shows.\n",
        [{"title": g["displayName"], "search": g["savedShowSearch"], "shows": g["displayLimit"]}
         for g in sorted(galleries, key=lambda g: g["position"])]))

    channel = call("GET", f"/channels/{CHANNEL}")["channel"]
    status = next(s for s in json.loads(fetch("GET", "/CablecastAPI/v0/channelbrandingstatus"))
                  if s["channelID"] == CHANNEL)
    blocks = json.loads(channel["brandingConfig"] or "{}")
    put(out / "on-air/branding.json", json.dumps(blocks, indent=1, sort_keys=True) + "\n")
    put(out / "on-air/channel.yml", written(
        "# What rides on top of the channel's picture: the corner logo (the bug) and the crawl.\n"
        "# branding.json is Cablecast's own layout of them, kept as the box has it.\n",
        {"channel": channel["name"], "bugShowing": status["bugState"],
         "bugPicture": next((b.get("ImageURL") for b in blocks.get("Blocks", []) if b.get("Name") == "bug"), None),
         "bugText": status["bugText"],
         "crawlText": next((b.get("Text") for b in blocks.get("Blocks", []) if b.get("Name") == "crawl-text"), None),
         "brandingOffDuringFiller": channel["disableChannelBrandingDuringFiller"],
         "blocks": [{"name": b["Name"], "kind": b["BlockType"], "at": [int(b["Left"]), int(b["Top"])],
                     "size": [int(b["Width"]), int(b["Height"])]} for b in blocks.get("Blocks", [])]}))

    page = fetch("GET", f"/CablecastCGWebDisplay/WebDisplay.aspx?ChannelID={BOARD}").decode("utf-8", "replace")
    zones, art, slides = [], set(), set()
    for zone in sorted({int(z) for z in re.findall(r'id="ZoneID-(\d+)"', page)}):
        box = dict(re.findall(r"(width|height|top|left):\s*([\d.]+)%",
                              re.search(r"#ZoneID-%d\s*\{([^}]*)\}" % zone, page).group(1)))
        listing = fetch("GET", f"/CablecastCGWebDisplay/WebDisplay.aspx?op=getLatestBulletins&ZoneID={zone}").decode()
        pages = re.findall(r'dwelltime="(\d+)" objecttype="([^"]+)"[^>]*><img src="([^"?]+)\?t=(\d+)"', listing)
        kind = KINDS.get(pages[0][1], pages[0][1]) if pages else "empty"
        row = {"zone": zone, "kind": kind, "at %": [round(float(box["left"]), 2), round(float(box["top"]), 2)],
               "size %": [round(float(box["width"]), 2), round(float(box["height"]), 2)]}
        if kind == "art":
            name = image(out / f"bulletin-board/zones/zone-{zone:02d}", fetch("GET", pages[0][2]))
            art.add(name)
            row.update(file=f"zones/{name}", changed=changed(pages[0][3]))
        elif kind == "slides":
            row["slides"] = []
            for n, (dwell, _, src, ticks) in enumerate(pages, 1):
                name = image(out / f"bulletin-board/slides/{n:02d}", fetch("GET", src))
                slides.add(name)
                row["slides"].append({"file": f"slides/{name}", "seconds": int(dwell), "changed": changed(ticks)})
        zones.append(row)
    keep_only(out / "bulletin-board/zones", art)
    keep_only(out / "bulletin-board/slides", slides)
    put(out / "bulletin-board/board.yml", written(
        "# The bulletin board: the full-screen page the channel shows between programs and the\n"
        "# website embedded. Each zone is a box on that page, placed in % of the screen. Art and\n"
        "# slides are the files named; the other zones the board draws itself.\n", zones))
    print(f"ejected into {out}: website, on-air, bulletin board ({len(zones)} zones)")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["fields"]:
        fields(args[1:] == ["ensure"])
    elif args[:1] == ["eject"] and len(args) == 2:
        eject(args[1])
    elif args[:1] == ["snapshot"]:
        snapshot(args[1] if len(args) > 1 else datetime.date.today().isoformat())
    else:
        sys.exit(__doc__)
