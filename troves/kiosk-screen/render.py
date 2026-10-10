"""render.py -- the wall, written to a folder on this host, for a screen that
cannot reach the depot's copy.

    uv run --no-project --python 3.12 --with pyyaml render.py OUT

see docs/inline/troves/kiosk-screen/render.py.md#1"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DOOR = HERE.parents[1] / "machines" / "kiosk-1" / "door.py"


def main(out):
    spec = importlib.util.spec_from_file_location("door", DOOR)
    door = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(door)
    files = door.wall_files()
    out.mkdir(parents=True, exist_ok=True)
    for name, body in files.items():
        part = out / (name + ".part")
        part.write_bytes(body.encode("utf-8"))
        os.replace(part, out / name)
    for old in out.iterdir():
        if old.is_file() and old.name not in files:
            old.unlink()
    depot = door.wall_target()
    print(json.dumps({"files": sorted(files), "depot": str(depot / "index.html") if depot else None}))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__.split("\n\n")[1])
    main(pathlib.Path(sys.argv[1]))
