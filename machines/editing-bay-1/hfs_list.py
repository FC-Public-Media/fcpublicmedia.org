"""see docs/inline/machines/editing-bay-1/hfs_list.py.md#1"""
import json, os, struct, sys
from datetime import datetime, timedelta

dev, part_off, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
os.makedirs(out, exist_ok=True)
SECTOR = 512
MAC_EPOCH = datetime(1904, 1, 1)
f = open(dev, "rb", buffering=0)


def read(off, n):
    """Aligned raw read of n bytes at partition-relative off."""
    a = part_off + off
    start = a - a % SECTOR
    end = -(-(a + n) // SECTOR) * SECTOR
    f.seek(start)
    return f.read(end - start)[a - start:a - start + n]


def mac(t):
    return (MAC_EPOCH + timedelta(seconds=t)).strftime("%Y-%m-%d") if t else ""


vh = read(1024, 512)
assert vh[:2] in (b"H+", b"HX"), vh[:2]
block_size, total_blocks, free_blocks = struct.unpack(">III", vh[40:52])
fork = vh[0x110:0x110 + 80]
cat_size = struct.unpack(">Q", fork[:8])[0]
extents = [struct.unpack(">II", fork[16 + 8 * i:24 + 8 * i]) for i in range(8)]
extents = [e for e in extents if e[1]]
mapped = sum(c for _, c in extents) * block_size
if mapped < cat_size:
    print(f"WARNING: catalog continues in the overflow file ({mapped} of {cat_size} bytes mapped)")


def cat_read(off, n):
    for start, count in extents:
        span = count * block_size
        if off < span:
            return read(start * block_size + off, n)
        off -= span
    raise IndexError("catalog offset beyond mapped extents")


node0 = cat_read(0, 512)
depth, root, leaf_records, first_leaf, last_leaf, node_size = struct.unpack(">HIIIIH", node0[14:34])
print(f"catalog: {cat_size // 2**20} MiB, node {node_size}, {leaf_records} leaf records")

folders = {}   # id -> [parent, name, created, modified]
files = []     # (parent, name, size, rsize, modified)
node = first_leaf
seen = 0
while node:
    buf = cat_read(node * node_size, node_size)
    flink, blink, kind, height, nrec = struct.unpack(">IIbBH", buf[:12])
    if kind != -1:
        print(f"WARNING: node {node} kind {kind}, stopping")
        break
    offs = [struct.unpack(">H", buf[node_size - 2 * (i + 1):node_size - 2 * i])[0] for i in range(nrec)]
    for o in offs:
        klen = struct.unpack(">H", buf[o:o + 2])[0]
        parent, nlen = struct.unpack(">IH", buf[o + 2:o + 8])
        name = buf[o + 8:o + 8 + 2 * nlen].decode("utf-16-be", "replace")
        d = o + 2 + klen
        d += d & 1
        rtype = struct.unpack(">h", buf[d:d + 2])[0]
        if rtype == 1:
            fid, cr, md = struct.unpack(">III", buf[d + 8:d + 20])
            folders[fid] = [parent, name, mac(cr), mac(md)]
        elif rtype == 2:
            md = struct.unpack(">I", buf[d + 16:d + 20])[0]
            size = struct.unpack(">Q", buf[d + 88:d + 96])[0]
            rsize = struct.unpack(">Q", buf[d + 168:d + 176])[0]
            files.append((parent, name, size, rsize, mac(md)))
    seen += 1
    node = flink

print(f"walked {seen} leaf nodes: {len(folders)} folders, {len(files)} files")


def path(fid):
    parts = []
    while fid in folders and fid != 2:
        parts.append(folders[fid][1])
        fid = folders[fid][0]
    return "/" + "/".join(reversed(parts))


# roll sizes up every ancestor
agg = {fid: {"bytes": 0, "files": 0, "first": "", "last": ""} for fid in folders}
for parent, name, size, rsize, md in files:
    fid = parent
    while fid in agg:
        a = agg[fid]
        a["bytes"] += size + rsize
        a["files"] += 1
        if md:
            a["first"] = min(a["first"] or md, md)
            a["last"] = max(a["last"], md)
        if fid == 2:
            break
        fid = folders[fid][0]

rows = []
for fid, (parent, name, cr, md) in folders.items():
    p = path(fid)
    rows.append({"path": p, "depth": p.count("/") if p != "/" else 0, **agg[fid]})
rows.sort(key=lambda r: r["path"])
with open(os.path.join(out, "folders.json"), "w", encoding="utf-8") as j:
    json.dump(rows, j, ensure_ascii=False, indent=0)
with open(os.path.join(out, "files.tsv"), "w", encoding="utf-8") as t:
    for parent, name, size, rsize, md in files:
        t.write(f"{path(parent)}/{name}\t{size + rsize}\t{md}\n")

gb = lambda b: f"{b / 1e9:,.1f} GB"
with open(os.path.join(out, "summary.txt"), "w", encoding="utf-8") as s:
    s.write(f"volume: {gb((total_blocks - free_blocks) * block_size)} used of {gb(total_blocks * block_size)}\n")
    s.write(f"catalog: {len(folders)} folders, {len(files)} files\n\n")
    for r in rows:
        if 1 <= r["depth"] <= 2 and r["bytes"] > 1e9 or r["depth"] == 1:
            s.write(f"{'  ' * (r['depth'] - 1)}{r['path']}\t{gb(r['bytes'])}\t{r['files']} files\t{r['first']}..{r['last']}\n")
print("wrote", out)
