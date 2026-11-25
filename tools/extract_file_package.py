#!/usr/bin/env python3
"""Extract fileItem/fileData payloads from a decrypted Depot file package.

The input is the XML produced after Depot/EncatenComponent unwraps a `.cvn`.
No vendor bytes are generated; the payloads come from the caller's local file.
"""
from __future__ import annotations

import argparse
import hashlib
import pathlib
import re


ITEM_RE = re.compile(
    r'<fileItem\s+([^>]*)>\s*<fileData>(.*?)</fileData>\s*</fileItem>',
    re.S,
)


def attr(attrs: str, name: str) -> str:
    match = re.search(rf'{name}="([^"]*)"', attrs)
    return match.group(1) if match else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", type=pathlib.Path)
    parser.add_argument("outdir", type=pathlib.Path)
    parser.add_argument("--keep-duplicates", action="store_true")
    args = parser.parse_args()

    text = args.xml.read_text(errors="replace")
    args.outdir.mkdir(parents=True, exist_ok=True)
    manifest = []
    seen: set[tuple[str, str, str]] = set()

    for item_no, match in enumerate(ITEM_RE.finditer(text), 1):
        attrs, body = match.group(1), match.group(2)
        name = attr(attrs, "fileName")
        version = attr(attrs, "fileVersion")
        destination = attr(attrs, "fileDestinationInfo")
        source = attr(attrs, "fileSourcePath")
        key = (name, version, destination)
        if key in seen and not args.keep_duplicates:
            continue
        seen.add(key)

        stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", f"{name}-{version}-{destination}").strip("_")
        suffix = pathlib.Path(source.split("@@")[0]).suffix.lower()
        if suffix not in (".srec", ".ish", ".bin", ".hex"):
            suffix = ".srec"
        path = args.outdir / (stem + suffix)
        path.write_text(body, encoding="utf-8")
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        manifest.append((item_no, name, version, destination, source, len(body), digest, path.name))
        print(f"{path.name}\t{len(body)} bytes\t{digest[:16]}")

    manifest_path = args.outdir / "extracted_manifest.tsv"
    with manifest_path.open("w", encoding="utf-8", newline="") as f:
        f.write("item\tname\tversion\tdestination\tsource\tchars\tsha256\tfile\n")
        for row in manifest:
            f.write("\t".join(str(x) for x in row) + "\n")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
