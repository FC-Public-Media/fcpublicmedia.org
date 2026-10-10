# `troves/recorder/gear.yml`

Moved out of the file. Unreviewed.

## 1

Above `version: 1`

gear.yml — the recorder trove's gear. See README.md.

The same fields as ../../machines/gear.yml, which are station-node's. What is
different is the provisioner: this gear is not winget's, it is the bay's.

PRESENCE IS NOT DECLARED HERE. Whether it is installed on a host is
discovered by the procedure's `check`, never written.

## 2

Above `package: OBS-Studio-<version>-Windows-x64.zip`

NOT `winget`, and on purpose. winget's OBSProject.OBSStudio is the
installed OBS in Program Files, which is somebody's: its settings live in
%APPDATA%\obs-studio. The portable zip is the only OBS that keeps its
settings to itself, and nothing installs a zip into a folder of ours
except the bay.

## 3

Above `at: troves\recorder\obs`

%LOCALAPPDATA%\<profile>\troves\recorder\obs\ — the prefix says whose code
this is (../README.md, Rules).
