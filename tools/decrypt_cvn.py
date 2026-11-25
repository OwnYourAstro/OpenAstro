#!/usr/bin/env python3
"""Decrypt a Motorola .cvn package by capturing Depot's CryptDecrypt output.

The tool attaches to a running PatPortDepot.exe (or starts one), blocks writes
to the radio serial port, and collects the plaintext XML emitted by Depot while
the user opens the .cvn and starts the firmware update flow.

Usage:
    python tools/decrypt_cvn.py --cvn firmware/xts2500/XTS2500_DVN4228W.cvn
    python tools/decrypt_cvn.py --cvn ... --pid 5764 --out build/r17.xml

Frida must be installed in the Python environment. The tool is read-only with
respect to the radio and does not need a FLASHkey; it stops capturing when the
plaintext filePackage is complete.
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time

try:
    import frida
except ImportError:
    raise SystemExit("Frida is required: python -m pip install frida")

DEPOT_DEFAULT = pathlib.Path(
    r"C:\Program Files (x86)\Motorola\ASTRO 25 Products\ASTRO 25 Portable Depot\PatPortDepot.exe"
)

SCRIPT = r"""
var k32 = Process.getModuleByName('kernel32.dll');
var handles = {};
function label(p) {
  try { return p.readUtf16String(); } catch (e) { return ''; }
}
['CreateFileW', 'CreateFileA'].forEach(function (name) {
  Interceptor.attach(k32.getExportByName(name), {
    onEnter: function (args) {
      this.path = name.endsWith('W') ? args[0].readUtf16String() : args[0].readAnsiString();
    },
    onLeave: function (ret) {
      if (!ret.isNull()) handles[ret.toString()] = this.path;
    }
  });
});
Interceptor.attach(k32.getExportByName('WriteFile'), {
  onEnter: function (args) {
    var h = args[0].toString();
    var path = handles[h] || '';
    if (/COM\d+/i.test(path)) {
      this.block = true;
    }
  },
  onLeave: function (ret) {
    if (this.block) ret.replace(1);
  }
});
var adv = Process.getModuleByName('advapi32.dll');
Interceptor.attach(adv.getExportByName('CryptDecrypt'), {
  onEnter: function (args) {
    this.data = args[4];
    this.lenp = args[5];
  },
  onLeave: function (ret) {
    if (ret.isNull()) return;
    var n = 0;
    try { if (!this.lenp.isNull()) n = this.lenp.readU32(); } catch (e) {}
    if (!this.data.isNull() && n > 0 && n < 65536) {
      var buf = this.data.readByteArray(n);
      send({kind: 'out', len: n}, buf);
    }
  }
});
send({kind: 'ready', pid: Process.id});
"""


def find_depot() -> int | None:
    import frida

    for proc in frida.get_local_device().enumerate_processes():
        if proc.name.lower() == "patportdepot.exe":
            return proc.pid
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cvn", type=pathlib.Path, help="package to open in Depot (for reference)")
    ap.add_argument("--depot", type=pathlib.Path, default=DEPOT_DEFAULT)
    ap.add_argument("--pid", type=int)
    ap.add_argument("--out", type=pathlib.Path)
    ap.add_argument("--timeout", type=float, default=300.0)
    ap.add_argument("--launch", action="store_true")
    args = ap.parse_args()

    if args.out is None:
        stem = args.cvn.stem if args.cvn else "firmware"
        args.out = pathlib.Path("build") / f"{stem}.decrypted.xml"
    args.out.parent.mkdir(parents=True, exist_ok=True)

    pid = args.pid or find_depot()
    if pid is None and args.launch:
        if not args.depot.exists():
            raise SystemExit(f"Depot not found: {args.depot}")
        subprocess.Popen([str(args.depot)], cwd=str(args.depot.parent))
        for _ in range(30):
            time.sleep(0.5)
            pid = find_depot()
            if pid is not None:
                break
    if pid is None:
        raise SystemExit("PatPortDepot.exe is not running; start it or use --launch")

    session = frida.attach(pid)
    script = session.create_script(SCRIPT)
    chunks = bytearray()
    done = False

    def on_message(message, data):
        nonlocal done
        if message.get("type") != "send":
            print(message, file=sys.stderr)
            return
        p = message.get("payload", {})
        if p.get("kind") == "ready":
            print(f"Frida attached to Depot pid={pid}", flush=True)
            return
        if p.get("kind") != "out" or not data:
            return
        chunks.extend(data)
        tail = bytes(chunks[-64:])
        if b"</filePackage>" in chunks:
            done = True

    script.on("message", on_message)
    script.load()

    print("Open the .cvn in Depot and start the firmware update.", flush=True)
    print("Stop when Depot asks for the FLASHkey.", flush=True)
    end = time.time() + args.timeout
    while time.time() < end and not done:
        time.sleep(0.1)

    script.unload()
    session.detach()
    if not chunks:
        raise SystemExit("No CryptDecrypt output captured")

    data = bytes(chunks)
    start = data.find(b"<filePackage")
    if start >= 0:
        data = data[start:]
    end_marker = data.find(b"</filePackage>")
    if end_marker >= 0:
        data = data[: end_marker + len(b"</filePackage>")]
    args.out.write_bytes(data)
    print(f"wrote {args.out} ({len(data)} bytes)")
    if not data.startswith(b"<filePackage") or b"</filePackage>" not in data:
        print("warning: output does not look like a complete filePackage", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
