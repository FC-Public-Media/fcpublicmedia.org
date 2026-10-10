"""ptp.py -- raw PTP to a USB camera through Windows' own MTP driver (WPD extension commands).

Camera.find(name), .info(), .describe(code), .get(code), .set(code, v), .record(on). Needs comtypes.
Windows only; use it on the thread that opened the camera. See troves/camera/README.md.
"""
import ctypes
import struct

import comtypes
import comtypes.client
from comtypes import GUID

_types = comtypes.client.GetModule("portabledevicetypes.dll")
_api = comtypes.client.GetModule("portabledeviceapi.dll")

# --- property keys --------------------------------------------------------

def _key(fmtid, pid):
    k = _types._tagpropertykey()
    k.fmtid = GUID(fmtid)
    k.pid = pid
    return k

_DEV = "{26D4979A-E643-4626-9E2B-736DC0C92FDC}"          # WPD_DEVICE_PROPERTIES_V1
_COMMON = "{F0422A9C-5DC8-4440-B5BD-5DF28835658A}"       # WPD_PROPERTY_COMMON_*
_MTPX = "{4D545058-1A2E-4106-A357-771E0819FC56}"         # WPD_CATEGORY_MTP_EXT_VENDOR_OPERATIONS
_CATEGORY, _ID = _key(_COMMON, 1001), _key(_COMMON, 1002)
_X = lambda pid: _key(_MTPX, pid)
_OPCODE, _PARAMS, _RESPONSE = _X(1001), _X(1002), _X(1003)
_CONTEXT, _TOTAL, _TO_READ, _TO_WRITE, _DATA = _X(1006), _X(1007), _X(1008), _X(1010), _X(1012)
_WITH_READ, _WITH_WRITE, _READ, _WRITE, _END = 13, 14, 15, 16, 17

def _kp(obj, meth, k):
    """The key pointer type obj.meth wants: WPD's two typelibs each declare one; comtypes won't mix them."""
    for cls in type(obj).__mro__:
        for spec in getattr(cls, "_methods_", ()):
            if spec.name == meth:
                return ctypes.cast(ctypes.pointer(k), spec.argtypes[0])
    raise AttributeError(meth)

def _call(obj, meth, k, *a):
    return getattr(obj, meth)(_kp(obj, meth, k), *a)

def _new(cls, iface):
    return comtypes.client.CreateObject(cls, interface=iface)

# --- PTP data types ---------------------------------------------------------

_T = {1: ("b", 1), 2: ("B", 1), 3: ("h", 2), 4: ("H", 2), 5: ("i", 4), 6: ("I", 4), 7: ("q", 8), 8: ("Q", 8)}
STRING = 0xFFFF

def _read(b, o, t):
    if t == STRING:
        n = b[o]; o += 1
        return b[o:o + 2 * n].decode("utf-16-le").rstrip("\0"), o + 2 * n
    f, sz = _T[t]
    return struct.unpack_from("<" + f, b, o)[0], o + sz

def _pack(t, v):
    if t == STRING:
        s = str(v) + "\0"
        return bytes([len(s)]) + s.encode("utf-16-le")
    f, _ = _T[t]
    return struct.pack("<" + f, int(v))

class PTPError(Exception):
    pass

OK = 0x2001
RESPONSES = {0x2001: "OK", 0x2002: "general error", 0x2005: "not supported", 0x2019: "device busy",
             0x200A: "property not supported", 0x201C: "invalid value", 0x201B: "invalid parameter"}

# --- the camera -------------------------------------------------------------

class Camera:
    def __init__(self, pnp_id, name):
        self.id, self.name = pnp_id, name
        client = _new(_types.PortableDeviceValues, _types.IPortableDeviceValues)
        self.dev = _new(_api.PortableDevice, _api.IPortableDevice)
        self.dev.Open(pnp_id, client)
        self._desc = {}

    @staticmethod
    def devices():
        mgr = _new(_api.PortableDeviceManager, _api.IPortableDeviceManager)
        mgr.RefreshDeviceList()
        _, n = mgr.GetDevices(ctypes.POINTER(ctypes.c_wchar_p)(), 0)
        ids = (ctypes.c_wchar_p * n)()
        if n:
            mgr.GetDevices(ctypes.cast(ids, ctypes.POINTER(ctypes.c_wchar_p)), n)
        out = []
        for i in ids:
            _, ln = mgr.GetDeviceFriendlyName(i, ctypes.POINTER(ctypes.c_ushort)(), 0)
            buf = ctypes.create_unicode_buffer(ln)
            mgr.GetDeviceFriendlyName(i, ctypes.cast(buf, ctypes.POINTER(ctypes.c_ushort)), ln)
            out.append((i, buf.value))
        return out

    @classmethod
    def find(cls, name):
        for i, nm in cls.devices():
            if name.lower() in nm.lower():
                return cls(i, nm)
        return None

    def close(self):
        try:
            self.dev.Close()
        except Exception:
            pass

    # WPD commands ------------------------------------------------------------

    def _command(self, pid, setup=None):
        p = _new(_types.PortableDeviceValues, _types.IPortableDeviceValues)
        _call(p, "SetGuidValue", _CATEGORY, GUID(_MTPX))
        _call(p, "SetUnsignedIntegerValue", _ID, pid)
        if setup:
            setup(p)
        return self.dev.SendCommand(0, p)

    def _params(self, p, opcode, params):
        _call(p, "SetUnsignedIntegerValue", _OPCODE, opcode)
        c = _new(_types.PortableDevicePropVariantCollection, _types.IPortableDevicePropVariantCollection)
        add = [s for cls in type(c).__mro__ for s in getattr(cls, "_methods_", ()) if s.name == "Add"][0]
        for v in params:
            raw = (ctypes.c_ubyte * 24)()
            struct.pack_into("<HHHHI", raw, 0, 19, 0, 0, 0, v)       # VT_UI4
            c.Add(ctypes.cast(raw, add.argtypes[0]))
        _call(p, "SetIPortableDevicePropVariantCollectionValue", _PARAMS, c)

    def _end(self, ctx):
        r = self._command(_END, lambda p: _call(p, "SetStringValue", _CONTEXT, ctx))
        return _call(r, "GetUnsignedIntegerValue", _RESPONSE)

    def op_read(self, opcode, params=()):
        """A PTP operation with a data phase from the camera: (response, bytes)."""
        r = self._command(_WITH_READ, lambda p: self._params(p, opcode, params))
        ctx = _call(r, "GetStringValue", _CONTEXT)
        total = _call(r, "GetUnsignedLargeIntegerValue", _TOTAL)
        data = b""
        if total:
            def rd(p):
                _call(p, "SetStringValue", _CONTEXT, ctx)
                _call(p, "SetUnsignedIntegerValue", _TO_READ, total)
                _call(p, "SetBufferValue", _DATA, (ctypes.c_ubyte * total)(), total)
            got = _call(self._command(_READ, rd), "GetBufferValue", _DATA)
            if isinstance(got, (bytes, bytearray)):
                data = bytes(got)
            else:
                ptr, n = got
                data = bytes(ctypes.cast(ptr, ctypes.POINTER(ctypes.c_ubyte * n)).contents)
        return self._end(ctx), data

    def op_write(self, opcode, params, payload):
        """A PTP operation with a data phase to the camera: the response code."""
        def setup(p):
            self._params(p, opcode, params)
            _call(p, "SetUnsignedLargeIntegerValue", _TOTAL, len(payload))
        ctx = _call(self._command(_WITH_WRITE, setup), "GetStringValue", _CONTEXT)
        def wr(p):
            _call(p, "SetStringValue", _CONTEXT, ctx)
            _call(p, "SetUnsignedIntegerValue", _TO_WRITE, len(payload))
            _call(p, "SetBufferValue", _DATA, (ctypes.c_ubyte * len(payload)).from_buffer_copy(payload), len(payload))
        self._command(_WRITE, wr)
        return self._end(ctx)

    def op(self, opcode, params=()):
        """A PTP operation with no data phase: the response code."""
        def setup(p):
            self._params(p, opcode, params)
        return _call(self._command(12, setup), "GetUnsignedIntegerValue", _RESPONSE)

    # PTP ---------------------------------------------------------------------

    def info(self):
        rc, b = self.op_read(0x1001)
        if rc != OK:
            raise PTPError("GetDeviceInfo: %s" % RESPONSES.get(rc, hex(rc)))
        o = 0
        def u16():
            nonlocal o; v = struct.unpack_from("<H", b, o)[0]; o += 2; return v
        def u32():
            nonlocal o; v = struct.unpack_from("<I", b, o)[0]; o += 4; return v
        def s():
            nonlocal o; v, o = _read(b, o, STRING); return v
        def a16():
            return [u16() for _ in range(u32())]
        u16(); u32(); u16(); ext = s(); u16()
        ops, _, props, _, _ = a16(), a16(), a16(), a16(), a16()
        man, model, version, serial = s(), s(), s(), s()
        return {"manufacturer": man, "model": model, "firmware": version, "serial": serial,
                "extension": ext, "operations": ops, "properties": props}

    def describe(self, code):
        """GetDevicePropDesc: type, writable, current, default, and a range or choices. Cached."""
        rc, b = self.op_read(0x1014, (code,))
        if rc != OK:
            raise PTPError("0x%04X: %s" % (code, RESPONSES.get(rc, hex(rc))))
        _, t, rw = struct.unpack_from("<HHB", b, 0); o = 5
        default, o = _read(b, o, t)
        current, o = _read(b, o, t)
        form = b[o]; o += 1
        d = {"code": code, "type": t, "writable": bool(rw), "default": default, "current": current}
        if form == 1:
            d["min"], o = _read(b, o, t)
            d["max"], o = _read(b, o, t)
            d["step"], o = _read(b, o, t)
        elif form == 2:
            n = struct.unpack_from("<H", b, o)[0]; o += 2
            # This camera follows the u16 count with a u32 count of its own; skip it when there.
            if o + 4 <= len(b) and struct.unpack_from("<I", b, o)[0] == n:
                o += 4
            vals = []
            for _ in range(n):
                if o >= len(b):
                    break
                v, o = _read(b, o, t); vals.append(v)
            d["choices"] = vals
        self._desc[code] = d
        return d

    def get(self, code):
        t = self._desc[code]["type"] if code in self._desc else self.describe(code)["type"]
        rc, b = self.op_read(0x1015, (code,))
        if rc != OK:
            raise PTPError("0x%04X: %s" % (code, RESPONSES.get(rc, hex(rc))))
        return _read(b, 0, t)[0]

    def set(self, code, value):
        t = self._desc[code]["type"] if code in self._desc else self.describe(code)["type"]
        rc = self.op_write(0x1016, (code,), _pack(t, value))
        if rc != OK:
            raise PTPError("0x%04X = %r: %s" % (code, value, RESPONSES.get(rc, hex(rc))))

    def record(self, on):
        """InitiateOpenCapture / TerminateOpenCapture, as tal.org documents for Pocket cameras."""
        rc = self.op(0x101C, (0, 0)) if on else self.op(0x1018, (0,))
        if rc != OK:
            raise PTPError("record %s: %s" % ("start" if on else "stop", RESPONSES.get(rc, hex(rc))))
