#!/usr/bin/env python3
"""Probe a Motorola .cvn file: header text, entropy, and common signatures.

This is a diagnostic aid, not a decryptor. It prints enough to tell whether a
file is plaintext, compressed, encrypted, or an S-record container.
"""
from __future__ import annotations

import argparse
import math
import pathlib
from collections import Counter

SIGNATURES = {
    b"\x1f\x8b\x08": "gzip",
    b"BZh": "bzip2",
    b"\xfd7zXZ\x00": "xz",
    b"\x5d\x00\x00": "lzma",
    b"7z\xbc\xaf\x27\x1c": "7z",
    b"PK\x03\x04": "zip",
    b"\x28\xb5\x2f\xfd": "zstd",
    b"\x89PNG\r\n\x1a\n": "png",
    b"%PDF": "pdf",
    b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1": "ole2/cfb",
    b"\x7fELF": "elf",
}


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def print_ascii_run(data: bytes) -> None:
    run = bytearray()
    start = 0
    for i, b in enumerate(data):
        if 32 <= b < 127 or b in (9, 10, 13):
            if not run:
                start = i
            run.append(b)
        else:
            if len(run) >= 4:
                print(f"  text @0x{start:04x}: {bytes(run)!r}")
            run.clear()
    if len(run) >= 4:
        print(f"  text @0x{start:04x}: {bytes(run)!r}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cvn", type=pathlib.Path)
    ap.add_argument("--block", type=int, default=4096)
    args = ap.parse_args()
    data = args.cvn.read_bytes()
    print(f"file    : {args.cvn}")
    print(f"size    : {len(data)}")
    print(f"entropy : {entropy(data[: min(len(data), 65536)]):.3f} bits/byte (first 64 KiB)")
    print("header  :")
    print_ascii_run(data[: min(len(data), 256)])
    print("signatures:")
    for off in range(0, min(len(data), 1 << 20)):
        for sig, name in SIGNATURES.items():
            if data.startswith(sig, off):
                print(f"  0x{off:08x} {name}")
    print("entropy by block:")
    for off in range(0, len(data), args.block):
        block = data[off : off + args.block]
        print(f"  0x{off:08x}  {entropy(block):.3f}")
    srec = sum(data.count(m) for m in (b"S0", b"S1", b"S2", b"S3"))
    print(f"S-record-looking pairs: {srec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
