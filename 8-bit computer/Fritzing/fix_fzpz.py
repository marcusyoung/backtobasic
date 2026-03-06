#!/usr/bin/env python3
"""
fix_fzpz.py — Downloads and installs .fzpz files from the Adr-hyng
74LS-Series-Fritzing-Parts collection for use with Fritzing 1.0.6.

Problem fixed:
  Missing fritzingVersion attribute on <module> tag in the .fzp file.
  Fritzing 1.0.6 requires this attribute or it refuses to import the part.
  SVG files are left exactly as-is.

Typical usage (do everything in one command):
  python3 fix_fzpz.py --download --install --register

Individual steps:
  python3 fix_fzpz.py --download    Download all parts from GitHub
  python3 fix_fzpz.py --install     Fix and install into Fritzing user dirs
  python3 fix_fzpz.py --register    Create 74LS_series.fzb bin file

  python3 fix_fzpz.py 74LS00.fzpz  Fix a single file only (produces *_fixed.fzpz)

Fritzing must be closed before running --install or --register.
"""

import sys
import os
import re
import zipfile
import tempfile
import argparse
import urllib.request
import xml.etree.ElementTree as ET

FRITZING_VERSION = '0.9.10b.2022-07-01.CD-2134-0-40d23c29'
CONTROL_CHAR_RE  = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f]')

BASE_URL = (
    'https://raw.githubusercontent.com/'
    'Adr-hyng/74LS-Series-Fritzing-Parts/main/Parts/'
)

FRITZING_PARTS_USER = os.path.expanduser('~/Documents/Fritzing/parts/user')
FRITZING_SVG_USER   = os.path.expanduser('~/Documents/Fritzing/parts/svg/user')
FRITZING_BINS_DIR   = os.path.expanduser('~/Documents/Fritzing/bins')
FRITZING_PARTS_DB   = os.path.expanduser('~/.local/share/fritzing/parts.db')
BIN_NAME            = '74LS_series.fzb'

SVG_PREFIX_MAP = {
    'svg.breadboard.': 'breadboard',
    'svg.schematic.':  'schematic',
    'svg.icon.':       'icon',
    'svg.pcb.':        'pcb',
}

PARTS = [
    '7-SEGMENT-4DIGIT common cathode.fzpz',
    '74LS00.fzpz',
    '74LS02.fzpz',
    '74LS04.fzpz',
    '74LS08.fzpz',
    '74LS126.fzpz',
    '74LS137.fzpz',
    '74LS138.fzpz',
    '74LS139.fzpz',
    '74LS145.fzpz',
    '74LS151.fzpz',
    '74LS153.fzpz',
    '74LS155.fzpz',
    '74LS157.fzpz',
    '74LS160.fzpz',
    '74LS161.fzpz',
    '74LS162.fzpz',
    '74LS169.fzpz',
    '74LS173.fzpz',
    '74LS189.fzpz',
    '74LS190.fzpz',
    '74LS191.fzpz',
    '74LS192.fzpz',
    '74LS194.fzpz',
    '74LS195.fzpz',
    '74LS241.fzpz',
    '74LS245.fzpz',
    '74LS247.fzpz',
    '74LS273.fzpz',
    '74LS283.fzpz',
    '74LS293.fzpz',
    '74LS299.fzpz',
    '74LS32.fzpz',
    '74LS42.fzpz',
    '74LS590.fzpz',
    '74LS595.fzpz',
    '74LS645.fzpz',
    '74LS688.fzpz',
    '74LS73.fzpz',
    '74LS74.fzpz',
    '74LS76.fzpz',
    '74LS83.fzpz',
    '74LS85.fzpz',
    '74LS86.fzpz',
    '74LS90.fzpz',
    '74LS93.fzpz',
    '74LS94.fzpz',
    '74LS95.fzpz',
    'AT28C16.fzpz',
    'AT28C256.fzpz',
    'AT28C64.fzpz',
    'BB_No_Power_Rails.fzpz',
    'BB_Power_Rail_ONLY.fzpz',
    'NE555 Timer.fzpz',
    'SN74LS181.fzpz',
    'SN74LS48.fzpz',
]


# ---------------------------------------------------------------------------
# Core fix logic
# ---------------------------------------------------------------------------

def fix_fzp_content(content: str) -> str:
    content = CONTROL_CHAR_RE.sub('', content)
    if 'fritzingVersion' not in content:
        content = content.replace(
            '<module ',
            f'<module fritzingVersion="{FRITZING_VERSION}" ',
            1
        )
    return content


def iter_fzpz_contents(src_path: str):
    """Yield (arcname, bytes) for every file, with .fzp patched."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(src_path, 'r') as zin:
            zin.extractall(tmpdir)
        for root, dirs, files in os.walk(tmpdir):
            for fname in files:
                full    = os.path.join(root, fname)
                arcname = os.path.relpath(full, tmpdir)
                if arcname.endswith('.fzp'):
                    with open(full, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                    yield arcname, fix_fzp_content(content).encode('utf-8')
                else:
                    with open(full, 'rb') as f:
                        yield arcname, f.read()


def make_fixed_fzpz(src_path: str, dst_path: str):
    with zipfile.ZipFile(dst_path, 'w', compression=zipfile.ZIP_DEFLATED) as zout:
        for arcname, data in iter_fzpz_contents(src_path):
            zout.writestr(arcname, data)


def install_fzpz(src_path: str):
    """Extract a .fzpz directly into Fritzing's user parts directories."""
    os.makedirs(FRITZING_PARTS_USER, exist_ok=True)
    for subdir in SVG_PREFIX_MAP.values():
        os.makedirs(os.path.join(FRITZING_SVG_USER, subdir), exist_ok=True)

    for arcname, data in iter_fzpz_contents(src_path):
        if arcname.endswith('.fzp'):
            dest = os.path.join(FRITZING_PARTS_USER, arcname)
            with open(dest, 'wb') as f:
                f.write(data)
        else:
            fname = os.path.basename(arcname)
            placed = False
            for prefix, subdir in SVG_PREFIX_MAP.items():
                if fname.startswith(prefix):
                    svg_name = fname[len(prefix):]
                    dest = os.path.join(FRITZING_SVG_USER, subdir, svg_name)
                    with open(dest, 'wb') as f:
                        f.write(data)
                    placed = True
                    break
            if not placed:
                dest = os.path.join(FRITZING_PARTS_USER, fname)
                with open(dest, 'wb') as f:
                    f.write(data)


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

def download_all(dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    ok = fail = 0
    total = len(PARTS)
    for i, name in enumerate(PARTS, 1):
        dst = os.path.join(dest_dir, name)
        if os.path.exists(dst):
            print(f'  [{i:2}/{total}] EXISTS  {name}')
            ok += 1
            continue
        url = BASE_URL + urllib.request.quote(name)
        try:
            urllib.request.urlretrieve(url, dst)
            print(f'  [{i:2}/{total}] OK      {name}')
            ok += 1
        except Exception as e:
            print(f'  [{i:2}/{total}] FAIL    {name}: {e}')
            fail += 1
    print(f'\nDownload: {ok} ok, {fail} failed.')


# ---------------------------------------------------------------------------
# Bin registration
# ---------------------------------------------------------------------------

def extract_module_id(fzp_path: str) -> str | None:
    """Extract the moduleId attribute from a .fzp file."""
    try:
        # Use regex rather than full XML parse to be robust against malformed files
        with open(fzp_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        m = re.search(r'moduleId="([^"]+)"', content)
        return m.group(1) if m else None
    except Exception:
        return None


def register_bin():
    """
    Scan parts/user for all .fzp files that look like 74LS parts
    (i.e. not the pre-existing dip-switch etc.) and write a fresh
    74LS_series.fzb bin file.
    """
    os.makedirs(FRITZING_BINS_DIR, exist_ok=True)
    bin_path = os.path.join(FRITZING_BINS_DIR, BIN_NAME)

    # Collect all .fzp files in parts/user that are NOT the pre-existing parts
    skip_ids = {'prefix0000_538f2cd9d5af4846561f4b4cfaaa9d5e_1',
                'dip-switch-1-pos_1', 'Dip-Switch-4-Position_1'}

    entries = []
    for fname in sorted(os.listdir(FRITZING_PARTS_USER)):
        if not fname.endswith('.fzp'):
            continue
        fzp_path = os.path.join(FRITZING_PARTS_USER, fname)
        module_id = extract_module_id(fzp_path)
        if not module_id or module_id in skip_ids:
            continue
        entries.append((module_id, fzp_path))

    if not entries:
        print('  No eligible parts found in parts/user — run --install first.')
        return

    # Build the .fzb XML — modelIndex just needs to be a unique integer per entry
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<module fritzingVersion="{FRITZING_VERSION}" icon="Custom1.png">',
        '    <title>74LS Series</title>',
        '    <instances>',
    ]
    for idx, (module_id, fzp_path) in enumerate(entries, start=30000):
        lines.append(
            f'        <instance moduleIdRef="{module_id}" modelIndex="{idx}" '
            f'path="{fzp_path}">'
        )
        lines.append('            <views/>')
        lines.append('        </instance>')
    lines += [
        '    </instances>',
        '</module>',
    ]

    with open(bin_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines) + '\n')

    print(f'  Written {bin_path} with {len(entries)} parts.')
    print('  The "74LS Series" bin will appear in Fritzing on next launch.')


# ---------------------------------------------------------------------------
# Batch helpers
# ---------------------------------------------------------------------------

def collect_fzpz(work_dir: str):
    return sorted(
        os.path.join(work_dir, f)
        for f in os.listdir(work_dir)
        if f.endswith('.fzpz') and not f.endswith('_fixed.fzpz')
    )


def run_fix_only(paths: list):
    ok = fail = 0
    for src in paths:
        dst = src.replace('.fzpz', '_fixed.fzpz')
        try:
            make_fixed_fzpz(src, dst)
            print(f'  OK    {os.path.basename(src)}')
            ok += 1
        except Exception as e:
            print(f'  FAIL  {os.path.basename(src)}: {e}')
            fail += 1
    print(f'\nFixed: {ok} ok, {fail} failed.')


def run_install(paths: list):
    ok = fail = 0
    for src in paths:
        try:
            install_fzpz(src)
            print(f'  OK    {os.path.basename(src)}')
            ok += 1
        except Exception as e:
            print(f'  FAIL  {os.path.basename(src)}: {e}')
            fail += 1
    if os.path.exists(FRITZING_PARTS_DB):
        os.remove(FRITZING_PARTS_DB)
        print(f'\nRemoved parts.db — Fritzing will reindex on next launch.')
    print(f'\nInstalled: {ok} ok, {fail} failed.')


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Download, fix, and install 74LS parts for Fritzing 1.0.6'
    )
    parser.add_argument('--download', action='store_true',
                        help='Download all parts from GitHub')
    parser.add_argument('--install', action='store_true',
                        help='Install parts into Fritzing user directories')
    parser.add_argument('--register', action='store_true',
                        help='Create 74LS_series.fzb bin file')
    parser.add_argument('--dir', default=None,
                        help='Directory to work in (default: current directory)')
    parser.add_argument('files', nargs='*',
                        help='Specific .fzpz files to fix (produces *_fixed.fzpz)')
    args = parser.parse_args()

    work_dir = os.path.expanduser(args.dir) if args.dir else os.getcwd()

    if args.download:
        print(f'Downloading {len(PARTS)} parts to {work_dir} ...\n')
        download_all(work_dir)
        print()

    if args.install:
        paths = args.files if args.files else collect_fzpz(work_dir)
        if not paths:
            print(f'No .fzpz files found in {work_dir} — run --download first.')
            sys.exit(1)
        print(f'Installing {len(paths)} parts ...\n')
        run_install(paths)
        print()

    if args.register:
        print('Registering 74LS Series bin ...\n')
        register_bin()
        print()

    if not any([args.download, args.install, args.register]):
        # No flags — fix only mode
        paths = args.files if args.files else collect_fzpz(work_dir)
        if not paths:
            print(f'No .fzpz files found in {work_dir}')
            print('Run with --download --install --register to do everything.')
            sys.exit(1)
        run_fix_only(paths)

    if args.install or args.register:
        print('All done. Launch Fritzing — parts will appear in the "74LS Series" bin.')


if __name__ == '__main__':
    main()
