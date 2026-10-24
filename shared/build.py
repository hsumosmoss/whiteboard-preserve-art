#!/usr/bin/env python3
"""Sync shared files into both skill folders. Run from anywhere:
python shared/build.py
Edit files in shared/ only; this script overwrites the copies in skill folders."""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (source in shared/, destinations relative to repo root)
JOBS = [
    ('media-ebook.md', [
        'whiteboard-preserve-art/references/media-ebook.md',
        'whiteboard-stroke-drawing/references/media-ebook.md',
    ]),
    ('check_project.py', [
        'whiteboard-preserve-art/scripts/check_project.py',
        'whiteboard-stroke-drawing/scripts/check_project.py',
    ]),
]

def main():
    updated = 0
    for src_name, dests in JOBS:
        src = ROOT / 'shared' / src_name
        if not src.is_file():
            print(f'MISSING source: shared/{src_name}', file=sys.stderr)
            return 1
        for rel in dests:
            dst = ROOT / rel
            if not dst.parent.is_dir():
                print(f'MISSING dest dir: {rel}', file=sys.stderr)
                return 1
            shutil.copyfile(src, dst)
            print(f'synced -> {rel}')
            updated += 1
    print(f'[build] {updated} files updated')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
