#!/usr/bin/env python3
"""
PimpMyGRC — themes & visual effects for GNURadio Companion 3.10.

Usage:
    ./pimpmygrc.py list                         List available themes
    ./pimpmygrc.py apply <theme>                Apply theme (full file replacement)
    ./pimpmygrc.py apply <theme> --mode colors  Apply colors + block rendering (safer)
    ./pimpmygrc.py restore                      Restore original files
    ./pimpmygrc.py check                        Verify what's installed vs expected
    ./pimpmygrc.py status                       Show current theme state
    ./pimpmygrc.py diff <theme>                 Preview what will change
    ./pimpmygrc.py background-color '#1A2B3C'   Set canvas background color
    ./pimpmygrc.py background-color clear       Remove background color override
"""

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR / "shared"))
THEMES_DIR = SCRIPT_DIR / "themes"
BACKUP_DIR = SCRIPT_DIR / ".backups"
STATE_FILE = SCRIPT_DIR / ".current-theme"

# Background image and color paths (user-level, no sudo)
BG_IMAGE_PATH = Path.home() / ".gnuradio" / "grc_background.png"
BG_COLOR_PATH = Path.home() / ".gnuradio" / "grc_background_color"

# Effects config path
EFFECTS_PATH = Path.home() / ".gnuradio" / "grc_effects.json"

# Shared files installed regardless of theme (patched GRC files)
SHARED_FILES = {
    "gui/DrawingArea.py": "gui/DrawingArea.py",
    "gui/effects.py": "gui/effects.py",
    "gui/sounds.py": "gui/sounds.py",
}

# Theme files mapped: theme-relative-path -> grc-relative-path
THEME_FILES = {
    "gui/canvas/colors.py":      "gui/canvas/colors.py",
    "gui/canvas/block.py":       "gui/canvas/block.py",
    "gui/canvas/connection.py":  "gui/canvas/connection.py",
    "gui/canvas/port.py":        "gui/canvas/port.py",
    "gui/ParamWidgets.py":       "gui/ParamWidgets.py",
    "main.py":                   "main.py",
}

# Subset for colors-only mode.
# Includes block.py because text/disabled readability tuning lives there.
COLORS_ONLY_FILES = {
    "gui/canvas/colors.py": "gui/canvas/colors.py",
    "gui/canvas/block.py":  "gui/canvas/block.py",
    "main.py":              "main.py",
}

THEME_INFO = {
    "neon-hacker":    "Bright green neon on black — the original",
    "phosphor":       "Classic CRT phosphor green terminal",
    "outrun":         "80s synthwave — pink/purple/blue on deep purple",
    "cyberpunk-red":  "Red and gold on dark crimson",
    "arctic":         "Ice blue and white on dark navy",
    "solarized-dark": "Ethan Schoonover's Solarized palette",
    "military":       "Olive drab and amber on dark green",
}


def get_theme_description(theme_name):
    """Get description for a theme. Checks description.txt, then THEME_INFO."""
    desc_file = THEMES_DIR / theme_name / "description.txt"
    if desc_file.is_file():
        return desc_file.read_text().strip().split('\n')[0]
    return THEME_INFO.get(theme_name, "Custom theme")

# Key color constants that MUST exist in colors.py for GRC to work
REQUIRED_COLOR_VARS = [
    "HIGHLIGHT_COLOR", "BORDER_COLOR", "BORDER_COLOR_DISABLED", "FONT_COLOR",
    "MISSING_BLOCK_BACKGROUND_COLOR", "MISSING_BLOCK_BORDER_COLOR",
    "BLOCK_DEPRECATED_BACKGROUND_COLOR", "BLOCK_DEPRECATED_BORDER_COLOR",
    "FLOWGRAPH_BACKGROUND_COLOR", "COMMENT_BACKGROUND_COLOR",
    "FLOWGRAPH_EDGE_COLOR", "BLOCK_ENABLED_COLOR", "BLOCK_DISABLED_COLOR",
    "BLOCK_BYPASSED_COLOR", "CONNECTION_ENABLED_COLOR",
    "CONNECTION_DISABLED_COLOR", "CONNECTION_ERROR_COLOR",
    "DEFAULT_DOMAIN_COLOR", "PORT_TYPE_TO_COLOR",
    "DARK_THEME_STYLES", "LIGHT_THEME_STYLES",
]


def find_grc_dir():
    """Auto-detect the GRC Python package directory."""
    import glob as globmod
    candidates = [
        Path("/usr/lib/python3/dist-packages/gnuradio/grc"),
        Path("/usr/local/lib/python3/dist-packages/gnuradio/grc"),
    ]
    try:
        result = subprocess.run(
            [sys.executable, "-c",
             "import importlib, os; "
             "spec = importlib.util.find_spec('gnuradio.grc'); "
             "print(os.path.dirname(spec.origin))"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            p = Path(result.stdout.strip())
            if p not in candidates:
                candidates.insert(0, p)
    except Exception:
        pass

    for pattern in ["/usr/lib/python*/dist-packages/gnuradio/grc",
                    "/usr/local/lib/python*/dist-packages/gnuradio/grc",
                    "/usr/lib/python*/*-packages/gnuradio/grc"]:
        for match in globmod.glob(pattern):
            p = Path(match)
            if p not in candidates:
                candidates.append(p)

    for c in candidates:
        if (c / "gui" / "canvas" / "colors.py").is_file():
            return c
    return None


def find_grc_conf():
    """Find the grc.conf config file."""
    for p in [Path("/etc/gnuradio/conf.d/grc.conf"),
              Path("/usr/local/etc/gnuradio/conf.d/grc.conf")]:
        if p.is_file():
            return p
    return None


def md5(path):
    """Return MD5 hex digest of a file."""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def needs_sudo(path):
    """Check if we need sudo to write to a path."""
    return not os.access(path.parent, os.W_OK)


def sudo_copy(src, dst):
    """Copy a file, using sudo if necessary."""
    if needs_sudo(dst):
        subprocess.run(["sudo", "cp", str(src), str(dst)], check=True)
    else:
        shutil.copy2(src, dst)


def sudo_read(path):
    """Read a file, using sudo if necessary."""
    if os.access(path, os.R_OK):
        return path.read_text()
    result = subprocess.run(["sudo", "cat", str(path)],
                            capture_output=True, text=True, check=True)
    return result.stdout


def clear_pycache(grc_dir):
    """Remove all __pycache__ dirs and .pyc files under the GRC tree."""
    count = 0
    for root, dirs, files in os.walk(grc_dir):
        for d in list(dirs):
            if d == "__pycache__":
                target = Path(root) / d
                if needs_sudo(target):
                    subprocess.run(["sudo", "rm", "-rf", str(target)],
                                   check=False)
                else:
                    shutil.rmtree(target, ignore_errors=True)
                count += 1
                dirs.remove(d)
        for f in files:
            if f.endswith(".pyc"):
                target = Path(root) / f
                if needs_sudo(target):
                    subprocess.run(["sudo", "rm", "-f", str(target)],
                                   check=False)
                else:
                    target.unlink(missing_ok=True)
                count += 1
    return count


def validate_colors_py(filepath):
    """Check that a colors.py file exports all required variables."""
    content = filepath.read_text()
    missing = []
    for var in REQUIRED_COLOR_VARS:
        # Match "VAR_NAME = " at start of line (not inside comments)
        if not re.search(rf'^{var}\s*=', content, re.MULTILINE):
            missing.append(var)
    return missing


def validate_theme_file(theme_file, grc_file):
    """
    Validate a theme file is compatible with the installed GRC file.
    Returns (ok: bool, issues: list[str])
    """
    issues = []

    if not theme_file.is_file():
        return True, []  # file not in theme, skip

    if not grc_file.is_file():
        issues.append(f"target {grc_file} does not exist")
        return False, issues

    theme_content = theme_file.read_text()
    grc_content = grc_file.read_text()

    # Check imports match (theme shouldn't remove imports the original has)
    orig_imports = set(re.findall(r'^(?:from|import)\s+\S+', grc_content, re.MULTILINE))
    theme_imports = set(re.findall(r'^(?:from|import)\s+\S+', theme_content, re.MULTILINE))
    removed = orig_imports - theme_imports
    for imp in removed:
        issues.append(f"removes import: {imp}")

    # For colors.py specifically, check all required variables
    if theme_file.name == "colors.py":
        missing = validate_colors_py(theme_file)
        for var in missing:
            issues.append(f"missing required variable: {var}")

    return len(issues) == 0, issues


def list_themes():
    """List available themes."""
    if not THEMES_DIR.is_dir():
        print(f"No themes directory at {THEMES_DIR}")
        return
    print("Available GRC themes:\n")
    for d in sorted(THEMES_DIR.iterdir()):
        if d.is_dir():
            desc = get_theme_description(d.name)
            print(f"  {d.name:<18s} {desc}")
    print()


def get_current_theme():
    """Read stored theme name."""
    if STATE_FILE.is_file():
        return STATE_FILE.read_text().strip()
    return None


def backup_originals(grc_dir, grc_conf):
    """Back up original GRC files. Creates backup dir on first run,
    and backs up any newly tracked files on subsequent runs."""
    first_run = not BACKUP_DIR.is_dir()
    if first_run:
        print("Backing up original files (first run)...")
        BACKUP_DIR.mkdir(parents=True)

    checksums = {}
    backed_up_any = False
    all_files = list(THEME_FILES.values()) + list(SHARED_FILES.values())
    for rel_path in all_files:
        src = grc_dir / rel_path
        dst = BACKUP_DIR / rel_path
        if src.is_file() and not dst.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            checksums[rel_path] = md5(src)
            print(f"  backed up {rel_path}")
            backed_up_any = True

    if grc_conf and grc_conf.is_file():
        dst = BACKUP_DIR / "grc.conf"
        if not dst.is_file():
            shutil.copy2(grc_conf, dst)
            checksums["grc.conf"] = md5(grc_conf)
            print(f"  backed up grc.conf")
            backed_up_any = True

    if checksums:
        # Append to existing checksums file
        with open(BACKUP_DIR / "checksums.txt", "a") as f:
            for k, v in sorted(checksums.items()):
                f.write(f"{v}  {k}\n")

    if backed_up_any:
        print(f"  saved to {BACKUP_DIR}\n")
    return True


def apply_theme(theme_name, grc_dir, grc_conf, mode="full"):
    """Apply a theme to the local GRC installation."""
    theme_dir = THEMES_DIR / theme_name
    if not theme_dir.is_dir():
        print(f"Error: theme '{theme_name}' not found\n")
        list_themes()
        return False

    file_map = THEME_FILES if mode == "full" else COLORS_ONLY_FILES
    mode_label = "full (all files)" if mode == "full" else "colors+block (safe)"

    # --- PRE-FLIGHT CHECKS ---
    print(f"Pre-flight checks for '{theme_name}' [{mode_label}]...\n")

    all_ok = True
    for theme_rel, grc_rel in file_map.items():
        src = theme_dir / theme_rel
        dst = grc_dir / grc_rel
        if not src.is_file():
            continue

        ok, issues = validate_theme_file(src, dst)
        if ok:
            print(f"  [OK]   {grc_rel}")
        else:
            all_ok = False
            print(f"  [WARN] {grc_rel}")
            for issue in issues:
                print(f"           {issue}")

    if not all_ok:
        print("\nWarnings detected. Proceeding anyway (issues are non-fatal).\n")
    else:
        print("\nAll checks passed.\n")

    # --- RECORD BEFORE STATE ---
    before_hashes = {}
    for theme_rel, grc_rel in file_map.items():
        dst = grc_dir / grc_rel
        if dst.is_file():
            before_hashes[grc_rel] = md5(dst)

    # --- BACKUP ---
    backup_originals(grc_dir, grc_conf)

    # --- APPLY ---
    print(f"Applying theme: {theme_name} [{mode_label}]\n")

    installed = []
    failed = []
    skipped = []

    for theme_rel, grc_rel in file_map.items():
        src = theme_dir / theme_rel
        dst = grc_dir / grc_rel

        if not src.is_file():
            skipped.append((grc_rel, "not in theme"))
            continue
        if not dst.parent.is_dir():
            skipped.append((grc_rel, "target directory missing"))
            continue

        src_hash = md5(src)

        # Copy
        try:
            sudo_copy(src, dst)
        except subprocess.CalledProcessError as e:
            failed.append((grc_rel, f"copy failed: {e}"))
            continue

        # Verify
        dst_hash = md5(dst)
        before = before_hashes.get(grc_rel, "n/a")

        if dst_hash == src_hash:
            if dst_hash == before:
                print(f"  [OK]   {grc_rel} (unchanged — already themed)")
            else:
                print(f"  [OK]   {grc_rel} (changed: {before[:8]}.. -> {dst_hash[:8]}..)")
            installed.append(grc_rel)
        else:
            print(f"  [FAIL] {grc_rel}")
            print(f"         expected: {src_hash}")
            print(f"         got:      {dst_hash}")
            failed.append((grc_rel, "checksum mismatch after copy"))

    # Install shared patched files (e.g. DrawingArea.py with background image support)
    shared_dir = SCRIPT_DIR / "shared"
    for shared_rel, grc_rel in SHARED_FILES.items():
        src = shared_dir / shared_rel
        dst = grc_dir / grc_rel
        if not src.is_file():
            continue
        if not dst.parent.is_dir():
            continue
        try:
            sudo_copy(src, dst)
            print(f"  [OK]   {grc_rel} (shared patch)")
            installed.append(grc_rel)
        except subprocess.CalledProcessError as e:
            failed.append((grc_rel, f"copy failed: {e}"))

    # Background image/color are user-managed and independent of themes.
    if BG_IMAGE_PATH.is_file():
        print(f"  [INFO] background image preserved: {BG_IMAGE_PATH}")
    if BG_COLOR_PATH.is_file():
        print(f"  [INFO] background color preserved: {BG_COLOR_PATH.read_text().strip()}")

    # Install grc.conf if theme provides one (full mode only)
    if mode == "full":
        theme_conf = theme_dir / "config" / "grc.conf"
        if theme_conf.is_file() and grc_conf:
            try:
                sudo_copy(theme_conf, grc_conf)
                if md5(theme_conf) == md5(grc_conf):
                    installed.append("grc.conf")
                    print(f"  [OK]   grc.conf")
                else:
                    failed.append(("grc.conf", "checksum mismatch"))
                    print(f"  [FAIL] grc.conf")
            except subprocess.CalledProcessError as e:
                failed.append(("grc.conf", str(e)))

    # --- CLEAR CACHE ---
    cleared = clear_pycache(grc_dir)
    print(f"\n  Cleared {cleared} __pycache__/pyc entries")

    # --- SAVE STATE ---
    STATE_FILE.write_text(f"{theme_name}\nmode={mode}\n")

    # --- POST-APPLY VERIFICATION ---
    print(f"\nPost-apply verification:")
    verify_ok = True
    for grc_rel in installed:
        if grc_rel == "grc.conf":
            continue
        dst = grc_dir / grc_rel
        # Find matching source — check theme files, then shared files
        src = None
        for tr, gr in file_map.items():
            if gr == grc_rel:
                src = theme_dir / tr
                break
        if src is None:
            for sr, gr in SHARED_FILES.items():
                if gr == grc_rel:
                    src = (SCRIPT_DIR / "shared") / sr
                    break
        if src is None:
            continue
        if md5(dst) == md5(src):
            print(f"  [PASS] {grc_rel} matches theme file")
        else:
            print(f"  [FAIL] {grc_rel} does NOT match source file!")
            verify_ok = False

    # --- SUMMARY ---
    print(f"\nSummary:")
    print(f"  Applied:  {len(installed)} files")
    if failed:
        print(f"  Failed:   {len(failed)} files")
        for name, reason in failed:
            print(f"    {name}: {reason}")
    if skipped:
        print(f"  Skipped:  {len(skipped)} files")
        for name, reason in skipped:
            print(f"    {name}: {reason}")

    if verify_ok and not failed:
        print(f"\n  Theme '{theme_name}' applied successfully.")
        print(f"  Restart gnuradio-companion to see changes.")
    else:
        print(f"\n  Theme apply had issues — run './pimpmygrc.py check' for details.")

    return verify_ok and not failed


def restore_originals(grc_dir, grc_conf):
    """Restore original GRC files from backup."""
    if not BACKUP_DIR.is_dir():
        print("No backups found — nothing to restore.")
        return False

    print("Restoring original files...\n")
    restored = []
    failed = []

    for rel_path in THEME_FILES.values():
        src = BACKUP_DIR / rel_path
        dst = grc_dir / rel_path
        if not src.is_file():
            continue
        if not dst.parent.is_dir():
            continue

        before_hash = md5(dst) if dst.is_file() else "missing"

        try:
            sudo_copy(src, dst)
        except subprocess.CalledProcessError as e:
            failed.append((rel_path, str(e)))
            continue

        after_hash = md5(dst)
        src_hash = md5(src)

        if after_hash == src_hash:
            if before_hash == after_hash:
                print(f"  [OK] {rel_path} (was already original)")
            else:
                print(f"  [OK] {rel_path} (restored: {before_hash[:8]}.. -> {after_hash[:8]}..)")
            restored.append(rel_path)
        else:
            print(f"  [FAIL] {rel_path} — checksum mismatch!")
            failed.append((rel_path, "checksum mismatch"))

    # Restore shared patched files (DrawingArea.py etc.)
    for rel_path in SHARED_FILES.values():
        backup_file = BACKUP_DIR / rel_path
        dst = grc_dir / rel_path
        if backup_file.is_file():
            try:
                sudo_copy(backup_file, dst)
                print(f"  [OK] {rel_path} (restored shared patch)")
                restored.append(rel_path)
            except subprocess.CalledProcessError as e:
                failed.append((rel_path, str(e)))

    # Background image/color are user-managed — leave them alone on restore
    if BG_IMAGE_PATH.is_file():
        print(f"  [INFO] background image preserved (use 'background clear' to remove)")
    if BG_COLOR_PATH.is_file():
        print(f"  [INFO] background color preserved (use 'background-color clear' to remove)")

    backup_conf = BACKUP_DIR / "grc.conf"
    if backup_conf.is_file() and grc_conf:
        try:
            sudo_copy(backup_conf, grc_conf)
            if md5(backup_conf) == md5(grc_conf):
                restored.append("grc.conf")
                print(f"  [OK] grc.conf")
            else:
                failed.append(("grc.conf", "checksum mismatch"))
        except subprocess.CalledProcessError as e:
            failed.append(("grc.conf", str(e)))

    cleared = clear_pycache(grc_dir)
    print(f"\n  Cleared {cleared} __pycache__/pyc entries")

    STATE_FILE.unlink(missing_ok=True)

    print(f"\n  Restored {len(restored)} files to defaults.")
    if failed:
        print(f"  Failed: {len(failed)} files")
        for name, reason in failed:
            print(f"    {name}: {reason}")
    else:
        print(f"  Restart gnuradio-companion to see changes.")
    return not failed


def run_check(grc_dir, grc_conf):
    """
    Thorough check: compare every file on disk against backup AND theme,
    report exactly what state each file is in.
    """
    current = get_current_theme()

    print("=" * 60)
    print("PimpMyGRC — Theme Check Report")
    print("=" * 60)
    print(f"GRC install:    {grc_dir}")
    print(f"GRC config:     {grc_conf}")
    print(f"Current theme:  {current or 'default (no theme applied)'}")
    print(f"Backups:        {BACKUP_DIR if BACKUP_DIR.is_dir() else 'NONE'}")
    print()

    if not BACKUP_DIR.is_dir():
        print("No backups exist yet. Apply a theme first to create backups.")
        return

    has_issues = False

    print("File-by-file analysis:\n")

    for theme_rel, grc_rel in THEME_FILES.items():
        installed_file = grc_dir / grc_rel
        backup_file = BACKUP_DIR / grc_rel

        print(f"  {grc_rel}:")

        if not installed_file.is_file():
            print(f"    MISSING — not found at {installed_file}")
            has_issues = True
            continue

        inst_hash = md5(installed_file)
        inst_size = installed_file.stat().st_size

        if backup_file.is_file():
            back_hash = md5(backup_file)
            back_size = backup_file.stat().st_size
            matches_original = (inst_hash == back_hash)
        else:
            back_hash = None
            matches_original = None

        # Check against current theme
        matches_theme = None
        theme_hash = None
        if current:
            theme_file = THEMES_DIR / current / theme_rel
            if theme_file.is_file():
                theme_hash = md5(theme_file)
                theme_size = theme_file.stat().st_size
                matches_theme = (inst_hash == theme_hash)

        # Report
        print(f"    installed:  {inst_hash}  ({inst_size} bytes)")
        if back_hash:
            print(f"    backup:     {back_hash}  ({back_size} bytes)")
        if theme_hash:
            print(f"    theme:      {theme_hash}  ({theme_size} bytes)")

        if matches_theme:
            print(f"    status:     THEMED [{current}]")
        elif matches_original:
            if current:
                print(f"    status:     ORIGINAL (theme '{current}' NOT applied to this file)")
                has_issues = True
            else:
                print(f"    status:     ORIGINAL")
        elif matches_original is None:
            print(f"    status:     UNKNOWN (no backup to compare)")
        else:
            print(f"    status:     MODIFIED (doesn't match original or theme)")
            has_issues = True

        # Extra validation for colors.py
        if grc_rel == "gui/canvas/colors.py":
            missing = validate_colors_py(installed_file)
            if missing:
                print(f"    WARNING:    missing required variables: {', '.join(missing)}")
                has_issues = True

        print()

    # Check for stale __pycache__
    pycache_count = 0
    for root, dirs, files in os.walk(grc_dir):
        for d in dirs:
            if d == "__pycache__":
                pycache_count += 1
        for f in files:
            if f.endswith(".pyc"):
                pycache_count += 1

    if pycache_count > 0:
        print(f"  WARNING: {pycache_count} __pycache__/pyc entries found.")
        print(f"           These may serve stale bytecode. Run apply or restore to clear.\n")
        has_issues = True

    # Summary
    print("=" * 60)
    if has_issues:
        print("ISSUES FOUND — see details above.")
    else:
        print("ALL OK — installed files match expected state.")
    print("=" * 60)


def show_status(grc_dir, grc_conf):
    """Quick status overview."""
    current = get_current_theme()
    print(f"Current theme: {current or 'default (no theme applied)'}")
    print(f"GRC install:   {grc_dir}")
    print(f"GRC config:    {grc_conf}")
    print(f"Backups:       {'yes' if BACKUP_DIR.is_dir() else 'none'}")

    if current:
        # Read mode from state file
        state = STATE_FILE.read_text() if STATE_FILE.is_file() else ""
        mode_match = re.search(r'mode=(\w+)', state)
        if mode_match:
            print(f"Apply mode:    {mode_match.group(1)}")

    print(f"\nRun './pimpmygrc.py check' for detailed file verification.")


def show_diff(theme_name, grc_dir):
    """Show a unified diff between installed files and theme files."""
    theme_dir = THEMES_DIR / theme_name
    if not theme_dir.is_dir():
        print(f"Error: theme '{theme_name}' not found\n")
        list_themes()
        return

    print(f"Changes for theme '{theme_name}':\n")

    for theme_rel, grc_rel in THEME_FILES.items():
        src = theme_dir / theme_rel
        dst = grc_dir / grc_rel
        if not src.is_file():
            continue
        if not dst.is_file():
            print(f"--- {grc_rel}: target missing, would create\n")
            continue

        result = subprocess.run(
            ["diff", "-u", "--color=always", str(dst), str(src)],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print(f"--- {grc_rel}: identical\n")
        else:
            lines = result.stdout.strip().split("\n")
            changed = sum(1 for l in lines if l.startswith("+") or l.startswith("-"))
            print(f"--- {grc_rel} ({changed} changed lines) ---")
            print(result.stdout)


def get_themes_list():
    """Return sorted list of (name, description) tuples."""
    themes = []
    if THEMES_DIR.is_dir():
        for d in sorted(THEMES_DIR.iterdir()):
            if d.is_dir():
                desc = get_theme_description(d.name)
                themes.append((d.name, desc))
    return themes


def parse_theme_colors(theme_name):
    """Parse hex color values from a theme's colors.py file."""
    colors_file = THEMES_DIR / theme_name / "gui" / "canvas" / "colors.py"
    if not colors_file.is_file():
        return None

    content = colors_file.read_text()
    colors = {}

    # Extract hex color assignments: VAR_NAME = get_color('#RRGGBB') or parse_color(...)
    for match in re.finditer(
            r'^(\w+)\s*=\s*(?:get_color|parse_color)\([\'"]([#0-9A-Fa-f]+)[\'"]\)',
            content, re.MULTILINE):
        colors[match.group(1)] = match.group(2)

    # Extract DARK_THEME_STYLES port type colors
    port_colors = {}
    dt_match = re.search(r'DARK_THEME_STYLES\s*=\s*["\']([^"\']+)["\']',
                         content, re.DOTALL)
    if dt_match:
        css = dt_match.group(1)
        # Parse .type_color_xxx { color: #HEX; } patterns
        for m in re.finditer(r'\.type_color_(\w+)\s*\{\s*color:\s*([#0-9A-Fa-f]+)',
                             css):
            port_colors[m.group(1)] = m.group(2)
    colors['_port_types'] = port_colors

    # Extract ambient particle settings (plain string assignments)
    for var in ('AMBIENT_PARTICLE_TYPE', 'AMBIENT_PARTICLE_COLOR'):
        m = re.search(rf"^{var}\s*=\s*['\"]([^'\"]+)['\"]",
                      content, re.MULTILINE)
        if m:
            colors[var] = m.group(1)

    return colors


def hex_to_rgb(hex_str):
    """Convert '#RRGGBB' to (r, g, b) floats 0-1."""
    h = hex_str.lstrip('#')
    return (int(h[0:2], 16) / 255.0,
            int(h[2:4], 16) / 255.0,
            int(h[4:6], 16) / 255.0)


def _draw_preview_to_surface(theme_name, colors, ctx, W, H, mode='full'):
    """Draw a mock flowgraph preview onto a Cairo context.

    Args:
        theme_name: Theme name string (used for labels).
        colors: Dict from parse_theme_colors().
        ctx: A cairo.Context to draw on.
        W, H: Width and height of the drawing area.
        mode: 'full' or 'colors' — controls which effects are shown.
    """
    import cairo

    def c(name, fallback='#888888'):
        return hex_to_rgb(colors.get(name, fallback))

    def port_c(dtype, fallback='#888888'):
        pt = colors.get('_port_types', {})
        return hex_to_rgb(pt.get(dtype, fallback))

    # --- Background ---
    bg = c('FLOWGRAPH_BACKGROUND_COLOR', '#1e1e1e')
    ctx.set_source_rgb(*bg)
    ctx.paint()

    # --- Helpers ---
    def rounded_rect(x, y, w, h, r=8):
        ctx.new_sub_path()
        ctx.arc(x + w - r, y + r, r, -0.5 * 3.14159, 0)
        ctx.arc(x + w - r, y + h - r, r, 0, 0.5 * 3.14159)
        ctx.arc(x + r, y + h - r, r, 0.5 * 3.14159, 3.14159)
        ctx.arc(x + r, y + r, r, 3.14159, 1.5 * 3.14159)
        ctx.close_path()

    def draw_block(x, y, w, h, title, state, ports_in, ports_out):
        """Draw a GRC-style block.
        state: 'enabled', 'disabled', 'bypassed'
        ports_in/out: list of (label, dtype) tuples
        """
        # Pick colors based on state
        disabled = (state == 'disabled')
        font_alpha = 0.60 if disabled else 1.0

        if state == 'enabled':
            bg_col = c('BLOCK_ENABLED_COLOR', '#2e2e5e')
            border_col = c('BORDER_COLOR', '#444444')
            font_col = c('FONT_COLOR', '#DDDDDD')
            title_col = (1, 1, 1, 1)
        elif disabled:
            bg_col = c('BLOCK_DISABLED_COLOR', '#2A2A2A')
            border_col = c('BORDER_COLOR_DISABLED', '#888888')
            font_col = c('FONT_COLOR', '#DDDDDD')
            # Dim title: use font color at reduced alpha
            title_col = (*font_col, 0.64)
        elif state == 'bypassed':
            bg_col = c('BLOCK_BYPASSED_COLOR', '#4f4f2f')
            border_col = c('BORDER_COLOR', '#444444')
            font_col = c('FONT_COLOR', '#DDDDDD')
            title_col = (1.0, 0.7, 0.28, 1)
        else:
            bg_col = c('BLOCK_ENABLED_COLOR')
            border_col = c('BORDER_COLOR')
            font_col = c('FONT_COLOR')
            title_col = (1, 1, 1, 1)

        # Drop shadows (3 concentric soft layers) — full mode only
        if mode == 'full':
            for si, off in enumerate([6, 4, 2]):
                s_alpha = 0.08 + si * 0.04
                rounded_rect(x + off, y + off, w, h)
                ctx.set_source_rgba(0, 0, 0, s_alpha)
                ctx.fill()

        # Gradient fill
        grad = cairo.LinearGradient(x, y, x, y + h)
        grad.add_color_stop_rgb(0,
                                min(1, bg_col[0] + 0.10),
                                min(1, bg_col[1] + 0.10),
                                min(1, bg_col[2] + 0.14))
        grad.add_color_stop_rgb(1,
                                max(0, bg_col[0] - 0.06),
                                max(0, bg_col[1] - 0.06),
                                max(0, bg_col[2] - 0.05))

        rounded_rect(x, y, w, h)
        ctx.set_source(grad)
        ctx.fill_preserve()
        ctx.set_source_rgb(*border_col)
        ctx.set_line_width(1.5)
        ctx.stroke()

        # Title
        ctx.set_source_rgba(*title_col)
        ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_BOLD)
        ctx.set_font_size(12)
        ext = ctx.text_extents(title)
        ctx.move_to(x + (w - ext.width) / 2, y + 18)
        ctx.show_text(title)

        # Separator line under title
        ctx.set_source_rgba(*border_col, 0.5)
        ctx.set_line_width(0.5)
        ctx.move_to(x + 4, y + 24)
        ctx.line_to(x + w - 4, y + 24)
        ctx.stroke()

        # Ports
        port_h = 16
        port_w = 18
        port_start_y = y + 30

        port_centers_in = []
        port_centers_out = []

        def mute_port(pc):
            """Mute port color when block is disabled."""
            if disabled:
                return (pc[0] * 0.5, pc[1] * 0.5, pc[2] * 0.5)
            return pc

        for pi, (plabel, pdtype) in enumerate(ports_in):
            py = port_start_y + pi * (port_h + 4)
            pc = mute_port(port_c(pdtype, '#888888'))
            port_alpha = 0.4 if disabled else 1.0
            # Port rectangle (left side, sticking out)
            ctx.rectangle(x - port_w + 2, py, port_w, port_h)
            ctx.set_source_rgba(*pc, port_alpha)
            ctx.fill_preserve()
            # Port border
            ctx.set_source_rgba(max(0, pc[0] - 0.3),
                                max(0, pc[1] - 0.3),
                                max(0, pc[2] - 0.3), port_alpha)
            ctx.set_line_width(1)
            ctx.stroke()
            # Port label
            if disabled:
                ctx.set_source_rgba(0.6, 0.6, 0.6, 0.4)
            else:
                lum = 0.299 * pc[0] + 0.587 * pc[1] + 0.114 * pc[2]
                ctx.set_source_rgb(0, 0, 0) if lum > 0.45 else ctx.set_source_rgb(1, 1, 1)
            ctx.set_font_size(8)
            ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL,
                                 cairo.FONT_WEIGHT_NORMAL)
            ctx.move_to(x - port_w + 4, py + 11)
            ctx.show_text(plabel[:3])
            port_centers_in.append((x - port_w + 2, py + port_h / 2))

        for pi, (plabel, pdtype) in enumerate(ports_out):
            py = port_start_y + pi * (port_h + 4)
            pc = mute_port(port_c(pdtype, '#888888'))
            port_alpha = 0.4 if disabled else 1.0
            ctx.rectangle(x + w - 2, py, port_w, port_h)
            ctx.set_source_rgba(*pc, port_alpha)
            ctx.fill_preserve()
            ctx.set_source_rgba(max(0, pc[0] - 0.3),
                                max(0, pc[1] - 0.3),
                                max(0, pc[2] - 0.3), port_alpha)
            ctx.set_line_width(1)
            ctx.stroke()
            if disabled:
                ctx.set_source_rgba(0.6, 0.6, 0.6, 0.4)
            else:
                lum = 0.299 * pc[0] + 0.587 * pc[1] + 0.114 * pc[2]
                ctx.set_source_rgb(0, 0, 0) if lum > 0.45 else ctx.set_source_rgb(1, 1, 1)
            ctx.set_font_size(8)
            ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL,
                                 cairo.FONT_WEIGHT_NORMAL)
            ctx.move_to(x + w, py + 11)
            ctx.show_text(plabel[:3])
            port_centers_out.append((x + w - 2 + port_w, py + port_h / 2))

        # Param labels inside block
        ctx.set_source_rgb(*font_col)
        ctx.set_font_size(9)
        ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL,
                             cairo.FONT_WEIGHT_NORMAL)
        if state == 'disabled':
            ctx.set_source_rgba(*font_col, 0.4)

        return port_centers_in, port_centers_out

    def draw_connection(x1, y1, x2, y2, state='enabled',
                        src_dtype=None, sink_dtype=None):
        """Draw a bezier connection between two port centers."""
        if state == 'enabled':
            col = c('CONNECTION_ENABLED_COLOR', '#AAAAAA')
        elif state == 'disabled':
            col = c('CONNECTION_DISABLED_COLOR', '#555555')
        else:
            col = c('CONNECTION_ERROR_COLOR', '#FF4444')

        # Get port-type colors for gradient
        src_col = port_c(src_dtype) if src_dtype else None
        sink_col = port_c(sink_dtype) if sink_dtype else None
        use_gradient = (mode == 'full' and state == 'enabled'
                        and src_col and sink_col and src_col != sink_col)

        dx = abs(x2 - x1) * 0.5

        def _draw_bezier():
            ctx.move_to(x1, y1)
            ctx.curve_to(x1 + dx, y1, x2 - dx, y2, x2, y2)

        # Glow
        if use_gradient:
            grad = cairo.LinearGradient(x1, y1, x2, y2)
            grad.add_color_stop_rgba(0, *src_col, 0.2)
            grad.add_color_stop_rgba(1, *sink_col, 0.2)
            ctx.set_source(grad)
        else:
            ctx.set_source_rgba(*col, 0.2)
        ctx.set_line_width(4)
        _draw_bezier()
        ctx.stroke()

        # Wire
        if use_gradient:
            grad = cairo.LinearGradient(x1, y1, x2, y2)
            grad.add_color_stop_rgb(0, *src_col)
            grad.add_color_stop_rgb(1, *sink_col)
            ctx.set_source(grad)
        else:
            ctx.set_source_rgb(*col)
        ctx.set_line_width(1.8)
        _draw_bezier()
        ctx.stroke()

        # Arrow (use sink color when gradient)
        ctx.set_source_rgb(*(sink_col if use_gradient else col))
        arrow_sz = 6
        ctx.move_to(x2, y2)
        ctx.line_to(x2 - arrow_sz, y2 - arrow_sz / 2)
        ctx.line_to(x2 - arrow_sz, y2 + arrow_sz / 2)
        ctx.close_path()
        ctx.fill()

    # --- Layout: define blocks ---
    blocks = [
        # (x, y, w, h, title, state, ports_in, ports_out)
        (60,  50,  140, 80, "Signal Source", "enabled",
         [], [("out", "complex")]),

        (290, 30,  150, 100, "Low Pass Filter", "enabled",
         [("in", "complex")], [("out", "float")]),

        (290, 190, 150, 80, "Throttle", "bypassed",
         [("in", "float")], [("out", "float")]),

        (550, 30,  140, 80, "QT GUI Sink", "enabled",
         [("in", "float")], []),

        (550, 180, 140, 80, "Audio Sink", "disabled",
         [("in", "float"), ("msg", "string")], []),

        (60,  200, 140, 70, "Null Source", "enabled",
         [], [("out", "int")]),
    ]

    # Draw comment box
    cmt = c('COMMENT_BACKGROUND_COLOR', '#2a2a2a')
    ctx.set_source_rgb(*cmt)
    rounded_rect(60, 340, 260, 45, 6)
    ctx.fill()
    ctx.set_source_rgb(*c('FONT_COLOR', '#DDDDDD'))
    ctx.set_font_size(10)
    ctx.select_font_face("monospace", cairo.FONT_SLANT_ITALIC,
                         cairo.FONT_WEIGHT_NORMAL)
    ctx.move_to(72, 358)
    ctx.show_text("# Theme preview - example flowgraph")
    ctx.move_to(72, 373)
    ctx.show_text(f"# {get_theme_description(theme_name)}")

    # Draw missing block
    mb_bg = c('MISSING_BLOCK_BACKGROUND_COLOR', '#4A2A2A')
    mb_border = c('MISSING_BLOCK_BORDER_COLOR', '#AA4444')
    rounded_rect(550, 320, 140, 65, 8)
    grad = cairo.LinearGradient(550, 320, 550, 385)
    grad.add_color_stop_rgb(0, min(1, mb_bg[0] + 0.08),
                            min(1, mb_bg[1] + 0.08),
                            min(1, mb_bg[2] + 0.10))
    grad.add_color_stop_rgb(1, max(0, mb_bg[0] - 0.04),
                            max(0, mb_bg[1] - 0.04),
                            max(0, mb_bg[2] - 0.04))
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.set_source_rgb(*mb_border)
    ctx.set_line_width(1.5)
    ctx.stroke()
    ctx.set_source_rgb(*c('FONT_COLOR', '#DDDDDD'))
    ctx.set_font_size(11)
    ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD)
    ctx.move_to(570, 348)
    ctx.show_text("Missing Block")
    ctx.set_font_size(8)
    ctx.select_font_face("monospace", cairo.FONT_SLANT_ITALIC,
                         cairo.FONT_WEIGHT_NORMAL)
    ctx.move_to(570, 365)
    ctx.show_text("(block not found)")

    # Draw deprecated block
    dep_bg = c('BLOCK_DEPRECATED_BACKGROUND_COLOR', '#554411')
    dep_border = c('BLOCK_DEPRECATED_BORDER_COLOR', '#AA6600')
    rounded_rect(370, 340, 140, 45, 8)
    grad = cairo.LinearGradient(370, 340, 370, 385)
    grad.add_color_stop_rgb(0, min(1, dep_bg[0] + 0.08),
                            min(1, dep_bg[1] + 0.08),
                            min(1, dep_bg[2] + 0.10))
    grad.add_color_stop_rgb(1, max(0, dep_bg[0] - 0.04),
                            max(0, dep_bg[1] - 0.04),
                            max(0, dep_bg[2] - 0.04))
    ctx.set_source(grad)
    ctx.fill_preserve()
    ctx.set_source_rgb(*dep_border)
    ctx.set_line_width(1.5)
    ctx.stroke()
    ctx.set_source_rgb(*c('FONT_COLOR', '#DDDDDD'))
    ctx.set_font_size(11)
    ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_BOLD)
    ctx.move_to(385, 358)
    ctx.show_text("Deprecated Blk")
    ctx.set_font_size(8)
    ctx.move_to(385, 373)
    ctx.show_text("(deprecated)")

    # Draw all blocks and collect port positions
    all_ports = []
    for bx, by, bw, bh, btitle, bstate, bpin, bpout in blocks:
        pins, pouts = draw_block(bx, by, bw, bh, btitle, bstate, bpin, bpout)
        all_ports.append((pins, pouts))

    # Connection definitions: (src_block, src_port, dst_block, dst_port, state, src_dtype, sink_dtype)
    conn_defs = [
        (0, 0, 1, 0, 'enabled', 'complex', 'complex'),   # Signal Source -> LPF
        (1, 0, 3, 0, 'enabled', 'float', 'float'),        # LPF -> QT GUI Sink
        (5, 0, 2, 0, 'enabled', 'int', 'float'),          # Null Source -> Throttle
        (2, 0, 4, 0, 'disabled', 'float', 'float'),       # Throttle -> Audio Sink
    ]
    connections = []  # store endpoints for animated effects
    for sb, sp, db, dp, cstate, sd, dd in conn_defs:
        if all_ports[sb][1] and all_ports[db][0]:
            x1, y1 = all_ports[sb][1][sp]
            x2, y2 = all_ports[db][0][dp]
            draw_connection(x1, y1, x2, y2, cstate, sd, dd)
            connections.append({
                'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2,
                'state': cstate, 'src_dtype': sd, 'sink_dtype': dd,
            })

    # Error connection indicator
    err_col = c('CONNECTION_ERROR_COLOR', '#FF4444')
    ctx.set_source_rgb(*err_col)
    ctx.set_line_width(1.8)
    ex1, ey1 = 745, 345
    ex2, ey2 = 830, 420
    ctx.move_to(ex1, ey1)
    dx = abs(ex2 - ex1) * 0.5
    ctx.curve_to(ex1 + dx, ey1, ex2 - dx, ey2, ex2, ey2)
    ctx.stroke()
    # Small X at end
    ctx.set_line_width(2)
    ctx.move_to(ex2 - 5, ey2 - 5)
    ctx.line_to(ex2 + 5, ey2 + 5)
    ctx.move_to(ex2 + 5, ey2 - 5)
    ctx.line_to(ex2 - 5, ey2 + 5)
    ctx.stroke()
    ctx.set_font_size(8)
    ctx.move_to(ex2 - 15, ey2 + 18)
    ctx.show_text("error")

    # Highlight indicator
    hl = c('HIGHLIGHT_COLOR', '#00FFFF')
    ctx.set_source_rgba(*hl, 0.35)
    ctx.set_line_width(4)
    bx, by, bw, bh = 290, 30, 150, 100
    rounded_rect(bx - 3, by - 3, bw + 6, bh + 6, 10)
    ctx.stroke()

    # Theme name label
    ctx.set_source_rgba(*c('FONT_COLOR', '#DDDDDD'), 0.6)
    ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL,
                         cairo.FONT_WEIGHT_NORMAL)
    ctx.set_font_size(11)
    label = f"{theme_name}  —  {get_theme_description(theme_name)}"
    ctx.move_to(10, H - 10)
    ctx.show_text(label)

    # Legend
    ctx.set_font_size(9)
    ctx.set_source_rgba(*c('FONT_COLOR', '#DDDDDD'), 0.4)
    legend_items = ["enabled", "disabled", "bypassed", "missing", "deprecated",
                    "highlight", "error conn"]
    ctx.move_to(W - 280, H - 10)
    ctx.show_text(" | ".join(legend_items))

    # Return layout metadata for animated effects
    # Collect port rects for hover glow demo (pick one enabled output port)
    # Block 0 (Signal Source) output port at index 0
    glow_port = None
    if all_ports[0][1]:
        px, py = all_ports[0][1][0]
        glow_port = {'x': px - 18, 'y': py - 8, 'w': 18, 'h': 16,
                     'dtype': 'complex'}

    # Highlighted block (LPF) for click ripple
    highlight_block = {'x': 290, 'y': 30, 'w': 150, 'h': 100}

    return {
        'connections': connections,
        'blocks': [(bx, by, bw, bh) for bx, by, bw, bh, *_ in blocks],
        'glow_port': glow_port,
        'highlight_block': highlight_block,
    }


def generate_preview(theme_name, output_path=None):
    """Generate a PNG preview image for a theme showing a mock flowgraph."""
    import cairo

    colors = parse_theme_colors(theme_name)
    if not colors:
        print(f"  Could not parse colors for '{theme_name}'")
        return None

    if output_path is None:
        output_path = SCRIPT_DIR / "previews" / f"{theme_name}.png"
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    W, H = 900, 520
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    ctx = cairo.Context(surface)
    _draw_preview_to_surface(theme_name, colors, ctx, W, H)
    surface.write_to_png(str(output_path))
    return output_path


def generate_all_previews():
    """Generate preview images for all themes."""
    themes = get_themes_list()
    if not themes:
        print("No themes found.")
        return

    print(f"Generating previews for {len(themes)} themes...\n")
    for name, desc in themes:
        path = generate_preview(name)
        if path:
            print(f"  {name:<18s} -> {path}")
    print(f"\nDone. Previews saved to {SCRIPT_DIR / 'previews'}/")


def interactive_menu(grc_dir, grc_conf):
    """Interactive GTK4 theme picker with live preview."""
    import gi
    gi.require_version('Gtk', '4.0')
    from gi.repository import Gtk, Gdk, Gio, GLib, Pango

    themes = get_themes_list()
    if not themes:
        print("No themes found.")
        return

    class ThemeSwitcher(Gtk.Application):
        def __init__(self):
            super().__init__(application_id="com.grc.theme-switcher")
            self.current_mode = "full"
            self.status_text = ""

        def do_activate(self):
            win = Gtk.ApplicationWindow(application=self, title="PimpMyGRC")
            win.set_default_size(1200, 820)

            # Dark theme for the app itself
            css = Gtk.CssProvider()
            css.load_from_string("""
                window { background-color: #1a1a2e; }
                .theme-list { background-color: #16213e; border-radius: 8px; }
                .theme-row { padding: 8px 12px; border-radius: 6px; }
                .theme-row:selected { background-color: #0f3460; }
                .theme-name { color: #e94560; font-weight: bold; font-size: 14px; }
                .theme-desc { color: #999999; font-size: 11px; }
                .active-badge { color: #00ff88; font-weight: bold; font-size: 11px; }
                .section-title { color: #e94560; font-weight: bold; font-size: 16px; }
                .status-bar { background-color: #0f3460; padding: 6px 12px;
                              border-radius: 6px; }
                .status-text { color: #00ff88; font-size: 12px; }
                .mode-button { padding: 6px 16px; border-radius: 4px;
                               background-color: #16213e; color: #cccccc;
                               border: 1px solid #333355; }
                .mode-button:checked { background-color: #0f3460;
                                       color: #00ff88; border-color: #00ff88; }
                .action-button { padding: 8px 20px; border-radius: 6px;
                                 font-weight: bold; }
                .apply-button { background-color: #0f3460; color: #00ff88;
                                border: 1px solid #00ff88; }
                .apply-button:hover { background-color: #1a5276; }
                .restore-button { background-color: #16213e; color: #e94560;
                                  border: 1px solid #e94560; }
                .restore-button:hover { background-color: #2a1a2e; }
            """)
            Gtk.StyleContext.add_provider_for_display(
                Gdk.Display.get_default(), css,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

            # Main horizontal layout
            hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            hbox.set_margin_top(12)
            hbox.set_margin_bottom(12)
            hbox.set_margin_start(12)
            hbox.set_margin_end(12)

            # --- Left panel: theme list + controls (fixed width) ---
            left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
            left.set_size_request(320, -1)
            left.set_hexpand(False)

            # Title
            title = Gtk.Label(label="PimpMyGRC")
            title.add_css_class("section-title")
            title.set_halign(Gtk.Align.START)
            left.append(title)

            # Current theme indicator
            current = get_current_theme()
            self.active_label = Gtk.Label(
                label=f"Active: {current or 'default'}")
            self.active_label.add_css_class("active-badge")
            self.active_label.set_halign(Gtk.Align.START)
            left.append(self.active_label)

            # Theme list
            scroll = Gtk.ScrolledWindow()
            scroll.set_vexpand(True)
            scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

            self.listbox = Gtk.ListBox()
            self.listbox.add_css_class("theme-list")
            self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)

            for name, desc in themes:
                row = Gtk.ListBoxRow()
                row.add_css_class("theme-row")
                row.theme_name = name

                vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

                hrow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                lbl_name = Gtk.Label(label=name)
                lbl_name.add_css_class("theme-name")
                lbl_name.set_halign(Gtk.Align.START)
                hrow.append(lbl_name)

                if name == current:
                    badge = Gtk.Label(label="(active)")
                    badge.add_css_class("active-badge")
                    hrow.append(badge)

                vbox.append(hrow)

                lbl_desc = Gtk.Label(label=desc)
                lbl_desc.add_css_class("theme-desc")
                lbl_desc.set_halign(Gtk.Align.START)
                vbox.append(lbl_desc)

                row.set_child(vbox)
                self.listbox.append(row)

            self.listbox.connect("row-selected", self._on_theme_selected)
            scroll.set_child(self.listbox)
            left.append(scroll)

            # Mode toggle
            mode_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            mode_label = Gtk.Label(label="Mode:")
            mode_label.set_margin_end(4)
            mode_box.append(mode_label)

            self.mode_full = Gtk.ToggleButton(label="Full")
            self.mode_full.add_css_class("mode-button")
            self.mode_full.set_active(True)
            self.mode_full.connect("toggled", self._on_mode, "full")

            self.mode_colors = Gtk.ToggleButton(label="Boring")
            self.mode_colors.add_css_class("mode-button")
            self.mode_colors.set_group(self.mode_full)
            self.mode_colors.connect("toggled", self._on_mode, "colors")

            mode_box.append(self.mode_full)
            mode_box.append(self.mode_colors)
            left.append(mode_box)

            # Action buttons
            btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            self.apply_btn = Gtk.Button(label="Apply Theme")
            self.apply_btn.add_css_class("action-button")
            self.apply_btn.add_css_class("apply-button")
            self.apply_btn.set_hexpand(True)
            self.apply_btn.connect("clicked", self._on_apply)

            restore_btn = Gtk.Button(label="Restore")
            restore_btn.add_css_class("action-button")
            restore_btn.add_css_class("restore-button")
            restore_btn.connect("clicked", self._on_restore)

            btn_box.append(self.apply_btn)
            btn_box.append(restore_btn)
            left.append(btn_box)

            # Background image controls
            bg_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            bg_btn = Gtk.Button(label="Background...")
            bg_btn.add_css_class("action-button")
            bg_btn.add_css_class("mode-button")
            bg_btn.set_hexpand(True)
            bg_btn.connect("clicked", self._on_pick_background)

            bg_clear_btn = Gtk.Button(label="Clear BG")
            bg_clear_btn.add_css_class("action-button")
            bg_clear_btn.add_css_class("restore-button")
            bg_clear_btn.connect("clicked", self._on_clear_background)

            bg_box.append(bg_btn)
            bg_box.append(bg_clear_btn)
            left.append(bg_box)

            # Background color controls
            bgc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

            bgc_btn = Gtk.Button(label="BG Color...")
            bgc_btn.add_css_class("action-button")
            bgc_btn.add_css_class("mode-button")
            bgc_btn.set_hexpand(True)
            bgc_btn.connect("clicked", self._on_pick_bg_color)

            bgc_clear_btn = Gtk.Button(label="Clear Color")
            bgc_clear_btn.add_css_class("action-button")
            bgc_clear_btn.add_css_class("restore-button")
            bgc_clear_btn.connect("clicked", self._on_clear_bg_color)

            bgc_box.append(bgc_btn)
            bgc_box.append(bgc_clear_btn)
            left.append(bgc_box)

            # Background status
            self.bg_label = Gtk.Label()
            self.bg_label.add_css_class("theme-desc")
            self.bg_label.set_halign(Gtk.Align.START)
            self.bg_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
            self._update_bg_label()
            left.append(self.bg_label)

            # --- Effects toggles ---
            self._fx_title = Gtk.Label(label="Visual Effects")
            self._fx_title.add_css_class("section-title")
            self._fx_title.set_halign(Gtk.Align.START)
            self._fx_title.set_margin_top(8)
            left.append(self._fx_title)

            self._fx_scroll = Gtk.ScrolledWindow()
            self._fx_scroll.set_vexpand(False)
            self._fx_scroll.set_min_content_height(280)
            self._fx_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)

            fx_grid = Gtk.Grid()
            fx_grid.set_row_spacing(4)
            fx_grid.set_column_spacing(8)

            self._fx_switches = {}
            self._fx_labels = {}
            # Effects requiring full mode (connection.py / port.py)
            self._full_only_fx = {
                'port_hover_glow', 'data_flow_particles', 'connection_gradient',
            }
            fx_items = [
                ("drop_shadows",      "Drop Shadows"),
                ("grid_overlay",      "Grid Overlay"),
                ("port_hover_glow",   "Port Hover Glow"),
                ("data_flow_particles", "Data Flow Dots"),
                ("connection_gradient", "Conn Gradients"),
                ("block_entrance_anim", "Block Fade-In"),
                ("click_ripple",      "Click Ripple"),
                ("toolbar_css",       "Toolbar Theme"),
            ]

            fx_config = self._load_effects_config()
            for i, (key, label) in enumerate(fx_items):
                lbl = Gtk.Label(label=label)
                lbl.add_css_class("theme-desc")
                lbl.set_halign(Gtk.Align.START)
                lbl.set_hexpand(True)
                fx_grid.attach(lbl, 0, i, 1, 1)

                sw = Gtk.Switch()
                sw.set_active(fx_config.get(key, False))
                sw.set_halign(Gtk.Align.END)
                sw.connect("notify::active", self._on_fx_toggle, key)
                fx_grid.attach(sw, 1, i, 1, 1)
                self._fx_switches[key] = sw
                self._fx_labels[key] = lbl

            # Ambient particles — dropdown with all particle types
            row_idx = len(fx_items)
            amb_label = Gtk.Label(label="Ambient")
            amb_label.add_css_class("theme-desc")
            amb_label.set_halign(Gtk.Align.START)
            amb_label.set_hexpand(True)
            fx_grid.attach(amb_label, 0, row_idx, 1, 1)

            self._ambient_types = [
                "off", "matrix_rain", "bubbles", "snow",
                "confetti", "sparks", "dust", "fire",
                "fireflies", "lightning", "starfield",
                "scanline", "glitch",
            ]
            self._ambient_labels = [
                "Off", "Matrix Rain", "Bubbles", "Snow",
                "Confetti", "Sparks", "Dust", "Fire",
                "Fireflies", "Lightning", "Starfield",
                "Scanline", "Glitch",
            ]

            amb_mode = fx_config.get("ambient_particles", "off")
            # Backward compat: old bool True -> "bubbles"
            if amb_mode is True:
                amb_mode = "bubbles"
            elif amb_mode is False:
                amb_mode = "off"
            # Map old "bubbles"/"fire" toggle values
            if amb_mode not in self._ambient_types:
                amb_mode = "off"

            amb_strings = Gtk.StringList.new(self._ambient_labels)
            self._amb_dropdown = Gtk.DropDown(model=amb_strings)
            self._amb_dropdown.set_halign(Gtk.Align.END)
            try:
                active_idx = self._ambient_types.index(amb_mode)
            except ValueError:
                active_idx = 0
            self._amb_dropdown.set_selected(active_idx)
            self._amb_dropdown.connect("notify::selected",
                                       self._on_ambient_mode)
            fx_grid.attach(self._amb_dropdown, 1, row_idx, 1, 1)

            # Click sound — dropdown with sound types
            row_idx += 1
            snd_label = Gtk.Label(label="Click Sound")
            snd_label.add_css_class("theme-desc")
            snd_label.set_halign(Gtk.Align.START)
            snd_label.set_hexpand(True)
            fx_grid.attach(snd_label, 0, row_idx, 1, 1)

            self._sound_types = [
                "off", "sonar", "click", "coin", "laser", "blip",
            ]
            self._sound_labels = [
                "Off", "Sonar", "Click", "Coin", "Laser", "Blip",
            ]

            snd_mode = fx_config.get("click_sound", "off")
            if snd_mode not in self._sound_types:
                snd_mode = "off"

            snd_strings = Gtk.StringList.new(self._sound_labels)
            self._snd_dropdown = Gtk.DropDown(model=snd_strings)
            self._snd_dropdown.set_halign(Gtk.Align.END)
            try:
                snd_idx = self._sound_types.index(snd_mode)
            except ValueError:
                snd_idx = 0
            self._snd_dropdown.set_selected(snd_idx)
            self._snd_dropdown.connect("notify::selected",
                                       self._on_sound_mode)
            fx_grid.attach(self._snd_dropdown, 1, row_idx, 1, 1)

            self._fx_scroll.set_child(fx_grid)
            left.append(self._fx_scroll)

            # Status bar
            self.status_label = Gtk.Label(label="Select a theme to preview")
            self.status_label.add_css_class("status-text")
            self.status_label.set_halign(Gtk.Align.START)
            self.status_label.set_ellipsize(Pango.EllipsizeMode.END)
            status_frame = Gtk.Box()
            status_frame.add_css_class("status-bar")
            status_frame.append(self.status_label)
            left.append(status_frame)

            hbox.append(left)

            # --- Right panel: live animated preview ---
            from gui.effects import AmbientParticleSystem
            import cairo as _cairo

            self._preview_surface = None
            self._preview_colors = None
            self._preview_theme_name = None
            self._preview_layout = None  # layout metadata for animated effects
            self._preview_particles = AmbientParticleSystem()
            self._preview_flow_dots = []  # data flow particle positions
            self._preview_flow_time = 0.0
            self._preview_cairo = _cairo  # keep reference for draw callback
            self._preview_time_start = time.time()

            self.preview_area = Gtk.DrawingArea()
            self.preview_area.set_size_request(700, 500)
            self.preview_area.set_hexpand(True)
            self.preview_area.set_vexpand(True)
            self.preview_area.set_draw_func(self._preview_draw)

            preview_frame = Gtk.Frame()
            preview_frame.set_hexpand(True)
            preview_frame.set_vexpand(True)
            preview_frame.set_child(self.preview_area)
            hbox.append(preview_frame)

            # 30fps animation timer
            def _tick_preview():
                self.preview_area.queue_draw()
                return True  # keep running
            GLib.timeout_add(33, _tick_preview)

            win.set_child(hbox)

            # Select first theme
            first_row = self.listbox.get_row_at_index(0)
            if first_row:
                self.listbox.select_row(first_row)

            # Keyboard navigation
            key_ctrl = Gtk.EventControllerKey()
            key_ctrl.connect("key-pressed", self._on_key)
            win.add_controller(key_ctrl)

            # Apply initial visibility based on mode
            self._update_fx_visibility()

            win.present()

        def _on_theme_selected(self, listbox, row):
            if row is None:
                return
            name = row.theme_name
            colors = parse_theme_colors(name)
            if colors:
                _cairo = self._preview_cairo
                W, H = 900, 520
                surf = _cairo.ImageSurface(_cairo.FORMAT_ARGB32, W, H)
                ctx = _cairo.Context(surf)
                layout = _draw_preview_to_surface(
                    name, colors, ctx, W, H, mode=self.current_mode)
                self._preview_surface = surf
                self._preview_colors = colors
                self._preview_theme_name = name
                self._preview_layout = layout
                # Reset animated state on theme change
                self._preview_particles = self._preview_particles.__class__()
                self._preview_flow_dots = []
                self._preview_time_start = time.time()
                self.preview_area.queue_draw()
            desc = get_theme_description(name)
            self.status_label.set_text(f"Preview: {name} -- {desc}")

        def _preview_draw(self, area, cr, w, h):
            """Draw callback for the live preview DrawingArea."""
            if self._preview_surface is None:
                # Nothing selected yet — draw dark background
                cr.set_source_rgb(0.1, 0.1, 0.18)
                cr.paint()
                cr.set_source_rgba(1, 1, 1, 0.3)
                cr.select_font_face("monospace", 0, 0)
                cr.set_font_size(14)
                cr.move_to(w / 2 - 80, h / 2)
                cr.show_text("Select a theme")
                return

            now = time.time()
            elapsed = now - self._preview_time_start

            # Scale the cached 900x520 surface to fit the DrawingArea
            sw = self._preview_surface.get_width()
            sh = self._preview_surface.get_height()
            scale = min(w / sw, h / sh)
            ox = (w - sw * scale) / 2
            oy = (h - sh * scale) / 2

            cr.save()
            cr.translate(ox, oy)
            cr.scale(scale, scale)

            # Paint cached static content
            cr.set_source_surface(self._preview_surface, 0, 0)
            cr.paint()

            # Boring mode: just the colors, no effects
            if self.current_mode != 'full':
                cr.restore()
                return

            colors = self._preview_colors or {}
            layout = self._preview_layout or {}
            fx_cfg = self._load_effects_config()

            hl_hex = colors.get('HIGHLIGHT_COLOR', '#00FFFF')
            hr, hg, hb = hex_to_rgb(hl_hex)

            # --- Grid overlay ---
            if fx_cfg.get('grid_overlay', False):
                cr.set_source_rgba(hr, hg, hb, 0.08)
                cr.set_line_width(0.5)
                step = 20
                for gx in range(0, sw, step):
                    cr.move_to(gx, 0)
                    cr.line_to(gx, sh)
                for gy in range(0, sh, step):
                    cr.move_to(0, gy)
                    cr.line_to(sw, gy)
                cr.stroke()

            # --- Port hover glow (pulsing on one port) ---
            # Only in full mode (port.py not replaced in colors mode)
            glow_port = layout.get('glow_port')
            if glow_port and self.current_mode == 'full' and fx_cfg.get('port_hover_glow', True):
                pulse = math.sin(now * 5.0)
                spread = 3 + 2 * pulse
                alpha = 0.35 + 0.25 * pulse
                pc = hex_to_rgb(colors.get('_port_types', {}).get(
                    glow_port['dtype'], '#888888'))
                gx = glow_port['x']
                gy = glow_port['y']
                gw = glow_port['w']
                gh = glow_port['h']
                cr.rectangle(gx - spread, gy - spread,
                             gw + spread * 2, gh + spread * 2)
                cr.set_source_rgba(pc[0], pc[1], pc[2], alpha)
                cr.fill()

            # --- Data flow particles (dots along enabled connections) ---
            # Only in full mode (connection.py not replaced in colors mode)
            conns = layout.get('connections', [])
            if conns and self.current_mode == 'full' and fx_cfg.get('data_flow_particles', False):
                for ci, conn in enumerate(conns):
                    if conn['state'] != 'enabled':
                        continue
                    x1, y1, x2, y2 = (conn['x1'], conn['y1'],
                                       conn['x2'], conn['y2'])
                    src_col = hex_to_rgb(colors.get('_port_types', {}).get(
                        conn['src_dtype'], '#888888'))
                    # 3 dots at different phases, speed ~0.4 cycles/sec
                    for di in range(3):
                        t = (elapsed * 0.4 + di / 3.0) % 1.0
                        px = x1 + (x2 - x1) * t
                        py = y1 + (y2 - y1) * t
                        cr.arc(px, py, 3.5, 0, 2 * math.pi)
                        cr.set_source_rgba(src_col[0], src_col[1],
                                           src_col[2], 0.9)
                        cr.fill()

            # --- Click ripple (expanding rings from highlighted block) ---
            hb_info = layout.get('highlight_block')
            if hb_info and fx_cfg.get('click_ripple', True):
                # Repeat ripple every 3 seconds
                ripple_t = (elapsed % 3.0) / 1.0  # 1s animation in 3s cycle
                if ripple_t < 1.0:
                    bx = hb_info['x']
                    by = hb_info['y']
                    bw = hb_info['w']
                    bh = hb_info['h']
                    for ring in range(3):
                        rt = (ripple_t - ring * 0.12)
                        denom = 1.0 - ring * 0.12
                        if denom > 0:
                            rt /= denom
                        if rt < 0 or rt > 1:
                            continue
                        expand = rt * 50
                        alpha = (1.0 - rt) * 0.45
                        lw = 2.5 - rt * 1.5
                        cr.set_source_rgba(hr, hg, hb, alpha)
                        cr.set_line_width(lw)
                        cr.new_sub_path()
                        r = 10
                        rx, ry = bx - expand, by - expand
                        rw, rh = bw + expand * 2, bh + expand * 2
                        cr.arc(rx + rw - r, ry + r, r, -0.5 * math.pi, 0)
                        cr.arc(rx + rw - r, ry + rh - r, r, 0,
                               0.5 * math.pi)
                        cr.arc(rx + r, ry + rh - r, r, 0.5 * math.pi,
                               math.pi)
                        cr.arc(rx + r, ry + r, r, math.pi, 1.5 * math.pi)
                        cr.close_path()
                        cr.stroke()

            # --- Ambient particles ---
            amb_mode = fx_cfg.get('ambient_particles', 'off')
            if amb_mode is True:
                amb_mode = 'bubbles'
            if amb_mode and amb_mode != 'off':
                # Mode is the particle type directly
                ptype = amb_mode
                pcolor = colors.get('AMBIENT_PARTICLE_COLOR', '#00FF88')
                self._preview_particles.tick_and_draw(
                    cr, sw, sh, ptype, pcolor)

            cr.restore()

        def _rerender_preview(self):
            """Re-render the cached static surface for the current theme/mode."""
            name = self._preview_theme_name
            colors = self._preview_colors
            if not name or not colors:
                return
            _cairo = self._preview_cairo
            W, H = 900, 520
            surf = _cairo.ImageSurface(_cairo.FORMAT_ARGB32, W, H)
            ctx = _cairo.Context(surf)
            layout = _draw_preview_to_surface(
                name, colors, ctx, W, H, mode=self.current_mode)
            self._preview_surface = surf
            self._preview_layout = layout
            self.preview_area.queue_draw()

        def _update_fx_visibility(self):
            """Show/hide entire effects section based on mode.
            Boring (colors) mode hides all effects — just colors."""
            is_full = (self.current_mode == 'full')
            self._fx_title.set_visible(is_full)
            self._fx_scroll.set_visible(is_full)

        def _on_mode(self, btn, mode):
            if btn.get_active():
                self.current_mode = mode
                self._update_fx_visibility()
                self._rerender_preview()

        def _on_apply(self, btn):
            row = self.listbox.get_selected_row()
            if not row:
                self.status_label.set_text("No theme selected")
                return
            name = row.theme_name
            mode = self.current_mode
            self.status_label.set_text(f"Applying '{name}' ({mode})...")
            # Run in a thread so the UI doesn't freeze
            import threading
            def do_apply():
                ok = apply_theme(name, grc_dir, grc_conf, mode=mode)
                GLib.idle_add(self._apply_done, name, mode, ok)
            threading.Thread(target=do_apply, daemon=True).start()

        def _apply_done(self, name, mode, ok):
            current = get_current_theme()
            self.active_label.set_text(f"Active: {current or 'default'}")
            if ok:
                self.status_label.set_text(
                    f"Applied '{name}' ({mode}). Restart GRC to see changes.")
            else:
                self.status_label.set_text(
                    f"Issues applying '{name}'. Check terminal output.")
            # Refresh active badges
            for i in range(len(themes)):
                r = self.listbox.get_row_at_index(i)
                if r:
                    vbox = r.get_child()
                    hrow = vbox.get_first_child()
                    # Remove old badge if present
                    badge = hrow.get_first_child()
                    while badge:
                        next_badge = badge.get_next_sibling()
                        if hasattr(badge, 'get_css_classes') and \
                                "active-badge" in badge.get_css_classes():
                            hrow.remove(badge)
                        badge = next_badge
                    # Add badge if this is the active theme
                    if themes[i][0] == current:
                        b = Gtk.Label(label="(active)")
                        b.add_css_class("active-badge")
                        hrow.append(b)
            return False

        def _on_restore(self, btn):
            self.status_label.set_text("Restoring defaults...")
            import threading
            def do_restore():
                ok = restore_originals(grc_dir, grc_conf)
                GLib.idle_add(self._restore_done, ok)
            threading.Thread(target=do_restore, daemon=True).start()

        def _restore_done(self, ok):
            self.active_label.set_text("Active: default")
            if ok:
                self.status_label.set_text(
                    "Restored to defaults. Restart GRC to see changes.")
            else:
                self.status_label.set_text(
                    "Restore had issues. Check terminal output.")
            # Clear all active badges
            for i in range(len(themes)):
                r = self.listbox.get_row_at_index(i)
                if r:
                    vbox = r.get_child()
                    hrow = vbox.get_first_child()
                    badge = hrow.get_first_child()
                    while badge:
                        next_badge = badge.get_next_sibling()
                        if hasattr(badge, 'get_css_classes') and \
                                "active-badge" in badge.get_css_classes():
                            hrow.remove(badge)
                        badge = next_badge
            return False

        def _update_bg_label(self):
            parts = []
            if BG_IMAGE_PATH.is_file():
                parts.append(f"Image: {BG_IMAGE_PATH.name}")
            if BG_COLOR_PATH.is_file():
                try:
                    col = BG_COLOR_PATH.read_text().strip()
                    parts.append(f"Color: {col}")
                except Exception:
                    pass
            if parts:
                self.bg_label.set_text("BG: " + " | ".join(parts))
            else:
                self.bg_label.set_text("BG: none (theme default)")

        def _on_pick_background(self, btn):
            win = self.get_active_window()

            png_filter = Gtk.FileFilter()
            png_filter.set_name("PNG images")
            png_filter.add_mime_type("image/png")

            img_filter = Gtk.FileFilter()
            img_filter.set_name("All images")
            img_filter.add_mime_type("image/png")
            img_filter.add_mime_type("image/jpeg")

            filters = Gio.ListStore.new(Gtk.FileFilter)
            filters.append(png_filter)
            filters.append(img_filter)

            dialog = Gtk.FileDialog()
            dialog.set_title("Choose Background Image")
            dialog.set_filters(filters)
            dialog.open(win, None, self._on_bg_file_chosen)

        def _on_bg_file_chosen(self, dialog, result):
            try:
                gfile = dialog.open_finish(result)
            except GLib.Error:
                return  # user cancelled
            if gfile is None:
                return

            src = Path(gfile.get_path())
            # Convert JPEG to PNG if needed (cairo only loads PNG)
            if src.suffix.lower() in ('.jpg', '.jpeg'):
                from PIL import Image
                img = Image.open(src)
                BG_IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
                img.save(BG_IMAGE_PATH, "PNG")
                self.status_label.set_text(
                    f"Background set: {src.name} (converted to PNG). Restart GRC.")
            else:
                BG_IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, BG_IMAGE_PATH)
                self.status_label.set_text(
                    f"Background set: {src.name}. Restart GRC.")
            self._update_bg_label()

        def _on_clear_background(self, btn):
            if BG_IMAGE_PATH.is_file():
                BG_IMAGE_PATH.unlink()
                self.status_label.set_text(
                    "Background removed. Restart GRC to see changes.")
            else:
                self.status_label.set_text("No background image to remove.")
            self._update_bg_label()

        def _on_pick_bg_color(self, btn):
            win = self.get_active_window()
            dialog = Gtk.ColorDialog()
            dialog.set_title("Choose Background Color")

            # Pre-set the current color if one exists
            initial = Gdk.RGBA()
            if BG_COLOR_PATH.is_file():
                try:
                    initial.parse(BG_COLOR_PATH.read_text().strip())
                except Exception:
                    initial.parse("#000000")
            else:
                initial.parse("#000000")

            dialog.choose_rgba(win, initial, None, self._on_bg_color_chosen)

        def _on_bg_color_chosen(self, dialog, result):
            try:
                rgba = dialog.choose_rgba_finish(result)
            except GLib.Error:
                return  # user cancelled
            if rgba is None:
                return

            hex_color = "#{:02X}{:02X}{:02X}".format(
                int(rgba.red * 255),
                int(rgba.green * 255),
                int(rgba.blue * 255))
            BG_COLOR_PATH.parent.mkdir(parents=True, exist_ok=True)
            BG_COLOR_PATH.write_text(hex_color + "\n")
            self.status_label.set_text(
                f"BG color set: {hex_color}. Restart GRC to see changes.")
            self._update_bg_label()

        def _on_clear_bg_color(self, btn):
            if BG_COLOR_PATH.is_file():
                BG_COLOR_PATH.unlink()
                self.status_label.set_text(
                    "BG color removed. Restart GRC to see changes.")
            else:
                self.status_label.set_text("No background color override set.")
            self._update_bg_label()

        def _load_effects_config(self):
            defaults = {
                "drop_shadows": True, "grid_overlay": False,
                "port_hover_glow": True, "data_flow_particles": False,
                "connection_gradient": True, "block_entrance_anim": True,
                "ambient_particles": "off", "click_sound": "off",
                "click_ripple": True, "toolbar_css": True,
            }
            if EFFECTS_PATH.is_file():
                try:
                    with open(EFFECTS_PATH) as f:
                        user = json.load(f)
                    if isinstance(user, dict):
                        for k in defaults:
                            if k not in user:
                                continue
                            dv = defaults[k]
                            uv = user[k]
                            if isinstance(dv, bool) and isinstance(uv, bool):
                                defaults[k] = uv
                            elif isinstance(dv, str) and isinstance(uv, str):
                                defaults[k] = uv
                            # Backward compat
                            elif k == 'ambient_particles' and uv is True:
                                defaults[k] = "bubbles"
                except Exception:
                    pass
            return defaults

        def _save_effects_config(self, config):
            EFFECTS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(EFFECTS_PATH, "w") as f:
                json.dump(config, f, indent=2)

        def _on_fx_toggle(self, switch, _pspec, key):
            config = self._load_effects_config()
            config[key] = switch.get_active()
            self._save_effects_config(config)
            self.status_label.set_text(
                f"Effect '{key}': {'ON' if switch.get_active() else 'OFF'}. "
                f"Restart GRC to see changes.")

        def _on_ambient_mode(self, dropdown, _pspec):
            idx = dropdown.get_selected()
            mode = self._ambient_types[idx]
            config = self._load_effects_config()
            config["ambient_particles"] = mode
            self._save_effects_config(config)
            # Reset preview particles when type changes
            from gui.effects import AmbientParticleSystem
            self._preview_particles = AmbientParticleSystem()
            label = self._ambient_labels[idx]
            self.status_label.set_text(
                f"Ambient particles: {label}. Restart GRC to see changes.")

        def _on_sound_mode(self, dropdown, _pspec):
            idx = dropdown.get_selected()
            stype = self._sound_types[idx]
            config = self._load_effects_config()
            config["click_sound"] = stype
            self._save_effects_config(config)
            label = self._sound_labels[idx]
            self.status_label.set_text(
                f"Click sound: {label}. Restart GRC to see changes.")
            # Play preview so user can hear it
            if stype != "off":
                try:
                    sys.path.insert(0, str(SCRIPT_DIR / "shared"))
                    from gui.sounds import play
                    play(stype)
                except Exception:
                    pass

        def _on_key(self, ctrl, keyval, keycode, state):
            if keyval == Gdk.KEY_Escape or keyval == Gdk.KEY_q:
                self.quit()
                return True
            if keyval == Gdk.KEY_Return:
                self._on_apply(None)
                return True
            return False

    app = ThemeSwitcher()
    app.run([])


def main():
    # No args = interactive mode, skip argparse entirely
    if len(sys.argv) == 1:
        grc_dir = find_grc_dir()
        if not grc_dir:
            print("Error: Could not find GNURadio GRC installation.")
            sys.exit(1)
        grc_conf = find_grc_conf()
        interactive_menu(grc_dir, grc_conf)
        return

    parser = argparse.ArgumentParser(
        description="PimpMyGRC — themes & visual effects for GNURadio Companion 3.10",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  %(prog)s                              Interactive mode (pick from menu)
  %(prog)s list                         Show available themes
  %(prog)s apply outrun                 Apply outrun theme (full replacement)
  %(prog)s apply outrun --mode colors   Apply colors + block rendering (safer)
  %(prog)s check                        Verify files on disk match expected state
  %(prog)s restore                      Revert to original GRC files
  %(prog)s diff cyberpunk-red           Preview changes before applying
""")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", aliases=["ls"], help="List available themes")
    sub.add_parser("status", help="Show current theme state")
    sub.add_parser("check", help="Verify installed files match expected state")
    sub.add_parser("restore", aliases=["reset", "default"],
                   help="Restore original files")

    p_apply = sub.add_parser("apply", help="Apply a theme")
    p_apply.add_argument("theme", help="Theme name")
    p_apply.add_argument("--mode", choices=["full", "colors"],
                         default="full",
                         help="full = replace all files (default), "
                              "colors = swap colors.py + block.py + main.py (safer)")

    p_diff = sub.add_parser("diff", help="Preview changes for a theme")
    p_diff.add_argument("theme", help="Theme name")

    p_preview = sub.add_parser("preview", help="Generate theme preview images")
    p_preview.add_argument("theme", nargs="?", default=None,
                           help="Theme name (omit for all themes)")
    p_preview.add_argument("--open", action="store_true",
                           help="Open the preview image(s) after generating")

    p_bg = sub.add_parser("background", aliases=["bg"],
                          help="Set or clear the canvas background image")
    p_bg.add_argument("image", nargs="?", default=None,
                      help="Path to a PNG image (omit to show current, "
                           "use 'clear' to remove)")

    p_bgc = sub.add_parser("background-color", aliases=["bgc"],
                           help="Set or clear background color override")
    p_bgc.add_argument("color", nargs="?", default=None,
                       help="Hex color e.g. '#1A2B3C' (omit to show current, "
                            "use 'clear' to remove)")

    args = parser.parse_args()

    # Detect GRC installation
    grc_dir = find_grc_dir()
    if not grc_dir:
        print("Error: Could not find GNURadio GRC installation.")
        print("Searched:")
        print("  /usr/lib/python3/dist-packages/gnuradio/grc")
        print("  /usr/local/lib/python3/dist-packages/gnuradio/grc")
        print("  Python import path for gnuradio.grc")
        sys.exit(1)

    grc_conf = find_grc_conf()

    if args.command in ("list", "ls"):
        list_themes()
        current = get_current_theme()
        print(f"Current theme: {current or 'default'}")

    elif args.command == "apply":
        if not apply_theme(args.theme, grc_dir, grc_conf, mode=args.mode):
            sys.exit(1)

    elif args.command in ("restore", "reset", "default"):
        if not restore_originals(grc_dir, grc_conf):
            sys.exit(1)

    elif args.command == "check":
        run_check(grc_dir, grc_conf)

    elif args.command == "status":
        show_status(grc_dir, grc_conf)

    elif args.command == "diff":
        show_diff(args.theme, grc_dir)

    elif args.command == "preview":
        if args.theme:
            path = generate_preview(args.theme)
            if path:
                print(f"Preview saved to {path}")
                if args.open:
                    subprocess.run(["xdg-open", str(path)], check=False)
        else:
            generate_all_previews()
            if args.open:
                preview_dir = SCRIPT_DIR / "previews"
                for f in sorted(preview_dir.glob("*.png")):
                    subprocess.run(["xdg-open", str(f)], check=False)

    elif args.command in ("background-color", "bgc"):
        if args.color is None:
            # Show current
            if BG_COLOR_PATH.is_file():
                col = BG_COLOR_PATH.read_text().strip()
                print(f"Background color override: {col}")
            else:
                print("Background color: none (using theme default)")
            print(f"\nUsage:")
            print(f"  {sys.argv[0]} background-color '#1A2B3C'  Set color")
            print(f"  {sys.argv[0]} background-color clear       Remove override")
        elif args.color == "clear":
            if BG_COLOR_PATH.is_file():
                BG_COLOR_PATH.unlink()
                print("Background color override removed.")
            else:
                print("No background color override to remove.")
            print("Restart gnuradio-companion to see changes.")
        else:
            h = args.color.strip().lstrip('#')
            if len(h) != 6 or not all(c in '0123456789abcdefABCDEF' for c in h):
                print(f"Error: invalid hex color '{args.color}'")
                print("Expected format: '#RRGGBB' or 'RRGGBB'")
                sys.exit(1)
            hex_color = f"#{h.upper()}"
            BG_COLOR_PATH.parent.mkdir(parents=True, exist_ok=True)
            BG_COLOR_PATH.write_text(hex_color + "\n")
            print(f"Background color set: {hex_color}")
            print(f"  Saved to {BG_COLOR_PATH}")
            print(f"  Restart gnuradio-companion to see changes.")

    elif args.command in ("background", "bg"):
        if args.image is None:
            # Show current background status
            if BG_IMAGE_PATH.is_file():
                import cairo as _cairo
                try:
                    s = _cairo.ImageSurface.create_from_png(str(BG_IMAGE_PATH))
                    print(f"Background image: {BG_IMAGE_PATH}")
                    print(f"  Size: {s.get_width()} x {s.get_height()} px")
                except Exception:
                    print(f"Background image: {BG_IMAGE_PATH} (could not read)")
            else:
                print("Background image: none")
            if BG_COLOR_PATH.is_file():
                print(f"Background color: {BG_COLOR_PATH.read_text().strip()}")
            else:
                print("Background color: none (theme default)")
            print(f"\nUsage:")
            print(f"  {sys.argv[0]} background <image.png>   Set background image")
            print(f"  {sys.argv[0]} background clear          Remove background image")
            print(f"  {sys.argv[0]} background-color '#HEX'   Set background color")
        elif args.image == "clear":
            if BG_IMAGE_PATH.is_file():
                BG_IMAGE_PATH.unlink()
                print("Background image removed.")
            else:
                print("No background image to remove.")
            print("Restart gnuradio-companion to see changes.")
        else:
            src = Path(args.image).resolve()
            if not src.is_file():
                print(f"Error: file not found: {src}")
                sys.exit(1)
            if not src.suffix.lower() == '.png':
                print(f"Error: file must be a PNG image (got {src.suffix})")
                sys.exit(1)
            BG_IMAGE_PATH.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, BG_IMAGE_PATH)
            import cairo as _cairo
            try:
                s = _cairo.ImageSurface.create_from_png(str(BG_IMAGE_PATH))
                print(f"Background set: {src.name} ({s.get_width()}x{s.get_height()} px)")
            except Exception:
                print(f"Background set: {src.name}")
            print(f"  Copied to {BG_IMAGE_PATH}")
            print(f"  Restart gnuradio-companion to see changes.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
