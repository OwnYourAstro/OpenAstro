#!/usr/bin/env python3
"""Convert a Motorola S-record file to a flat binary plus load metadata.

No third-party dependencies. Handles S0/S1/S2/S3 data and S5/S7/S8/S9
termination records. Gaps are filled with 0xFF by default.
"""
from __future__ import annotations

import argparse
import pathlib
import sys


def parse_srec(path: pathlib.Path):
    mem: dict[int, int] = {}
    header = ""
    entry = None
    for lineno, raw in enumerate(path.read_text(errors="replace").splitlines(), 1):
        line = raw.strip()
        if not line or not line.startswith("S"):
            continue
        kind = line[1]
        try:
            count = int(line[2:4], 16)
        except ValueError:
            print(f"{path}:{lineno}: bad byte count", file=sys.stderr)
            continue
        body = line[4:]
        if kind == "0":
            # S0 carries a 2-byte address field (normally 0x0000) before the data.
            data = bytes.fromhex(body[4 : max(4, 2 * (count - 1))])
            header = data.decode("ascii", "replace")
        elif kind in "123":
            addr_len = {"1": 2, "2": 3, "3": 4}[kind]
            addr = int(body[: 2 * addr_len], 16)
            data = bytes.fromhex(body[2 * addr_len : 2 * (count - 1)])
            for i, b in enumerate(data):
                mem[addr + i] = b
        elif kind in "789":
            addr_len = {"7": 4, "8": 3, "9": 2}[kind]
            entry = int(body[: 2 * addr_len], 16)
    if not mem:
        raise SystemExit(f"{path}: no data records")
    lo, hi = min(mem), max(mem)
    out = bytearray(b"\xff" * (hi - lo + 1))
    for a, b in mem.items():
        out[a - lo] = b
    return bytes(out), lo, hi + 1, entry, header


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("srec", type=pathlib.Path)
    ap.add_argument("output", type=pathlib.Path)
    ap.add_argument("--base", type=lambda x: int(x, 0), default=None,
                    help="override load base (default: lowest S-record address)")
    args = ap.parse_args()
    data, lo, hi, entry, header = parse_srec(args.srec)
    base = lo if args.base is None else args.base
    args.output.write_bytes(data)
    print(f"header : {header!r}")
    print(f"load   : 0x{base:08x}")
    print(f"end    : 0x{base + len(data):08x}")
    print(f"entry  : {('0x%08x' % entry) if entry is not None else 'none'}")
    print(f"bytes  : {len(data)} -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
