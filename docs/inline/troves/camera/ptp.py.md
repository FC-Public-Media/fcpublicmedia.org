# `troves/camera/ptp.py`

Moved out of the file. Unreviewed.

## 1

Above `import ctypes`

ptp.py -- a camera's USB control, through Windows Portable Devices.

A camera that offers PTP over USB is bound by Windows' own MTP driver
(WUDFWpdMtp). WPD lets a program send it raw PTP operations through the MTP
extension commands, so nothing is installed, no driver is replaced and no
administrator is needed. Measured on the Blackmagic Pocket Cinema Camera 6K Pro,
firmware 7.5.1, 2026-09-28 (docs/troves/camera/README.md, "What it answered").

    cam = Camera.find("pocket")        # by the name Windows shows
    cam.info()                          # firmware, model, operations, properties
    cam.describe(0x500F)                # type, current, default, range or choices
    cam.get(0x500F); cam.set(0x500F, 1000)
    cam.record(True); cam.record(False)

Needs comtypes: uv run --no-project --python 3.12 --with comtypes ...
Windows only. One thread: COM objects are made and used on the thread that
opened the camera.

## 2

Above `for cls in type(obj).__mro__:`

The property-key pointer type obj.meth expects. WPD's two type
libraries each declare their own, and comtypes will not mix them.

## 3

Above `rc, b = self.op_read(0x1014, (code,))`

GetDevicePropDesc: type, writable, current, default, and a range or
a list of choices. Cached, except for the current value.

## 4

Above `if o + 4 <= len(b) and struct.unpack_from("<I", b, o)[0] == n:`

The camera follows the u16 count with a u32 count of its own
(measured: ISO 25/25, frame rates 8/8). Skip it when it's there.

## 5

Above `rc = self.op(0x101C, (0, 0)) if on else self.op(0x1018, (0,))`

Start or stop recording: InitiateOpenCapture / TerminateOpenCapture.
Community-documented for Blackmagic Pocket cameras (tal.org).
