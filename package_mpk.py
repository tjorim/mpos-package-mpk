#!/usr/bin/env python3
"""Build a deterministic .mpk for a MicroPythonOS app folder.

Pure stdlib (zipfile) -- the only requirement is a Python 3 interpreter, no
external zip/find/touch tools, so this runs identically on Linux, macOS, and
native Windows. Follows the layout and reproducibility recipe from
docs.micropythonos.com/apps/bundling-apps/: fixed timestamps, sorted
entries, stored (uncompressed), app folder first.

Usage: package_mpk.py <app-dir>
Prints the absolute path to the built .mpk on stdout; everything else goes
to stderr, so callers can capture the result with `OUT=$(package_mpk.py ...)`.
"""
import json
import os
import sys
import zipfile

FIXED_DATE = (1980, 1, 1, 0, 0, 0)  # zip epoch -> reproducible builds


def _excluded(rel):
    parts = rel.split("/")
    return "__pycache__" in parts or parts[-1].endswith(".pyc")


def main():
    if len(sys.argv) != 2:
        sys.exit(f"Usage: {sys.argv[0]} <app-dir>")

    app_dir = os.path.abspath(sys.argv[1])
    parent_dir = os.path.dirname(app_dir)
    app_name = os.path.basename(app_dir)

    with open(os.path.join(app_dir, "MANIFEST.JSON")) as f:
        manifest = json.load(f)
    fullname = manifest["fullname"]
    version = manifest["version"]

    if fullname != app_name:
        sys.exit(
            f"MANIFEST.JSON fullname '{fullname}' must match the app folder name '{app_name}'"
        )

    out = os.path.join(parent_dir, f"{fullname}_{version}.mpk")
    if os.path.exists(out):
        os.remove(out)

    entries = set()
    for cur, _dirs, files in os.walk(app_dir):
        rel_dir = os.path.relpath(cur, parent_dir).replace(os.sep, "/")
        if "__pycache__" in rel_dir.split("/"):
            continue
        entries.add(rel_dir + "/")
        for fn in files:
            rel = rel_dir + "/" + fn
            if not _excluded(rel):
                entries.add(rel)

    shipped = 0
    with zipfile.ZipFile(out, "w", zipfile.ZIP_STORED) as z:
        for rel in sorted(entries):  # top-level folder sorts first
            full = os.path.join(parent_dir, rel)
            if rel.endswith("/"):
                zi = zipfile.ZipInfo(rel, date_time=FIXED_DATE)
                zi.external_attr = (0o40755 << 16) | 0x10
                z.writestr(zi, b"")
            else:
                zi = zipfile.ZipInfo(rel, date_time=FIXED_DATE)
                zi.external_attr = 0o100644 << 16
                with open(full, "rb") as f:
                    z.writestr(zi, f.read())
                shipped += 1

    print(f"Built {os.path.basename(out)} ({shipped} files)", file=sys.stderr)
    for rel in sorted(entries):
        print(f"  {rel}", file=sys.stderr)
    print(out)


if __name__ == "__main__":
    main()
