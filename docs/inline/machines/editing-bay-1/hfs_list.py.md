# `machines/editing-bay-1/hfs_list.py`

Moved out of the file. Unreviewed.

## 1

Above `import json, os, struct, sys`

Read-only HFS+ catalog lister. Opens a raw disk for reading only, walks the
catalog B-tree's leaf nodes, and writes a folder tree with sizes. Never writes
to the disk. Usage: hfs_list.py <\\.\PhysicalDriveN> <partition offset> <out dir>
