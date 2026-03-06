# Installing 74LS Series Parts in Fritzing 1.0.6 (Raspberry Pi / Linux)

The [Adr-hyng 74LS-Series-Fritzing-Parts](https://github.com/Adr-hyng/74LS-Series-Fritzing-Parts) collection contains 56 parts covering the full 74LS series plus AT28C EEPROMs, an NE555 timer, and custom breadboard components — everything needed for Ben Eater's 8-bit computer build and similar projects.

The parts were created with an older version of Fritzing and require a fix before they will import into Fritzing 1.0.6. This note documents the problem, the fix, and a script that automates the entire process.

## The Problem

Fritzing 1.0.6 requires a `fritzingVersion` attribute on the `<module>` tag of every `.fzp` part definition file. Parts created with older versions of Fritzing omit this attribute, causing Fritzing to refuse the import with the error:

```
Error reading file .../parts/user/74LSxx_<hash>.fzp: file 'breadboard/<hash>_breadboard.svg'
for title:'74LSxx' and moduleID:'...' not found.
```

The misleading SVG error is a secondary symptom — Fritzing never gets as far as locating the SVGs because the missing `fritzingVersion` causes the part to fail validation first.

## How Fritzing Imports Parts

Understanding the file layout is useful for troubleshooting. When Fritzing imports a `.fzpz` file it:

1. Extracts the `.fzp` metadata file to `~/Documents/Fritzing/parts/user/`
2. Extracts SVGs — stripping the flat `svg.breadboard.`, `svg.schematic.`, `svg.icon.`, `svg.pcb.` prefixes — into the corresponding subdirectories under `~/Documents/Fritzing/parts/svg/user/`
3. Registers the part's `moduleId` in the active bin file

The fix script replicates steps 1 and 2 directly, bypassing the UI entirely, then writes a bin file for step 3.

## The Fix Script

A Python script handles downloading, fixing, installing, and registering all 56 parts in a single command. It requires only the Python standard library — no additional packages needed.

**[fix_fzpz.py]** — link to script here

### Usage

```bash
# Do everything in one command (recommended)
cd ~/Documents/Fritzing/parts/74LS   # or any working directory
python3 fix_fzpz.py --download --install --register
```

**Fritzing must be closed before running.**

Individual steps are also available if needed:

```bash
python3 fix_fzpz.py --download    # Download all 56 parts from GitHub
python3 fix_fzpz.py --install     # Fix and install into Fritzing user directories
python3 fix_fzpz.py --register    # Create the 74LS_series.fzb bin file
python3 fix_fzpz.py 74LS04.fzpz  # Fix a single file only (produces 74LS04_fixed.fzpz)
```

If a download fails partway through, re-running `--download` is safe — already-downloaded files are skipped.

### What the Script Does

**`--download`** fetches each `.fzpz` from the GitHub repository's raw content URL into the working directory.

**`--install`** processes each `.fzpz`:
- Injects `fritzingVersion="0.9.10b.2022-07-01.CD-2134-0-40d23c29"` into the `<module>` tag of the `.fzp`
- Strips any stray control characters from the XML
- Extracts the `.fzp` to `~/Documents/Fritzing/parts/user/`
- Extracts SVGs to the correct subdirectories under `~/Documents/Fritzing/parts/svg/user/`
- Deletes `~/.local/share/fritzing/parts.db` so Fritzing reindexes on next launch

**`--register`** scans `parts/user/` for all installed parts, extracts their `moduleId` values, and writes `~/Documents/Fritzing/bins/74LS_series.fzb` — a bin file that causes Fritzing to display a **74LS Series** bin in the parts panel.

## After Running

Launch Fritzing. On first launch it will rebuild its parts database (this takes a few seconds). The **74LS Series** bin will appear in the parts panel containing all 56 parts, and the parts are also searchable by name.

## Notes

### Bin icon
Fritzing loads bin icons from its compiled Qt resource bundle, not from the filesystem. The bin uses the built-in `Custom1.png` icon. A custom "74LS" icon would require adding a PNG to `resources/bins/icons/` in the source tree and recompiling Fritzing — not worth the effort for a cosmetic change.

### Parts already installed via the UI
If you previously attempted to import any of these parts through the Fritzing UI and got errors, stale `.fzp` files may remain in `parts/user/`. The install script will overwrite them, but if Fritzing is still showing errors after running the script, check for and remove any stale files manually:

```bash
ls ~/Documents/Fritzing/parts/user/
```

Any file not belonging to a successfully installed part can be removed safely while Fritzing is closed.

### Tested on
- Fritzing 1.0.6, built from source
- Raspberry Pi 5, Debian Trixie
