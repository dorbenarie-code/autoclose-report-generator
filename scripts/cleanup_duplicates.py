#!/usr/bin/env python3
"""
cleanup_duplicates.py

Given a JSON report of duplicate file pairs (from duplicate_finder.py),
delete the redundant files and update all imports across the codebase
to point to the remaining “single source of truth” module.

Usage:
    cleanup_duplicates.py \
        --root path/to/myapp \
        --report duplicates.json \
        [--backup-dir backups] \
        [--dry-run]

Examples:
    # Actually delete and patch imports:
    python cleanup_duplicates.py \
        --root ./myapp \
        --report dup_report.json

    # Just simulate what would happen:
    python cleanup_duplicates.py \
        --root ./myapp \
        --report dup_report.json \
        --dry-run
"""

import argparse
import logging
import json
import shutil
import re
from pathlib import Path

# ------------------------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------------------------

SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules"}

# ------------------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------------------


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ------------------------------------------------------------------------------
# CORE FUNCTIONS
# ------------------------------------------------------------------------------


def load_report(path: Path) -> list[dict]:
    """Load the JSON report of duplicates."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logging.error(f"Cannot load JSON report {path}: {e}")
        return []


def determine_keep_delete(pair: dict) -> tuple[Path, Path]:
    """
    Decide which file to keep and which to delete.
    By default, keep the one with the lexicographically smaller path.
    """
    p1 = Path(pair["file1"])
    p2 = Path(pair["file2"])
    keep, delete = sorted([p1, p2], key=lambda p: str(p))
    return keep, delete


def module_names(path: Path, root: Path) -> tuple[str, str]:
    """
    Given a file path and project root, return both:
      - full module import path, e.g. 'myapp.utils.foo'
      - relative module path, e.g. 'utils.foo'
    """
    rel = path.relative_to(root).with_suffix("").as_posix().replace("/", ".")
    full = f"{root.name}.{rel}"
    return full, rel


def backup_file(path: Path, backup_root: Path):
    """Copy `path` to `backup_root` preserving directory structure."""
    dest = backup_root / path.relative_to(backup_root.parent)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    logging.debug(f"Backed up {path} to {dest}")


def delete_file(path: Path, dry_run: bool):
    """Delete the file at `path`, unless in dry-run mode."""
    if dry_run:
        logging.info(f"[DRY RUN] Would delete {path}")
    else:
        try:
            path.unlink()
            logging.info(f"Deleted {path}")
        except Exception as e:
            logging.error(f"Failed to delete {path}: {e}")


def update_imports_in_file(file_path: Path, replacements: dict, dry_run: bool):
    """
    Apply import replacements in a single file.

    `replacements` is dict mapping old_module to new_module.
    """
    text = file_path.read_text(encoding="utf-8", errors="ignore")
    original = text

    for old_mod, new_mod in replacements.items():
        # Patterns: from old_mod import ..., import old_mod
        patterns = [
            rf"(^\s*from\s+){re.escape(old_mod)}(\b)",
            rf"(^\s*import\s+){re.escape(old_mod)}(\b)",
        ]
        for pat in patterns:
            text = re.sub(
                pat,
                lambda m: m.group(1) + new_mod + m.group(2),
                text,
                flags=re.MULTILINE,
            )

    if text != original:
        if dry_run:
            logging.info(f"[DRY RUN] Would update imports in {file_path}")
        else:
            backup = file_path.with_suffix(file_path.suffix + ".bak")
            shutil.copy2(file_path, backup)
            file_path.write_text(text, encoding="utf-8")
            logging.info(f"Updated imports in {file_path}; backup created at {backup}")


def update_imports(root: Path, keep: Path, delete: Path, dry_run: bool):
    """
    Scan all .py files under `root` and replace references
    from the deleted module to the kept module.
    """
    old_full, old_rel = module_names(delete, root)
    new_full, new_rel = module_names(keep, root)

    replacements = {old_full: new_full, old_rel: new_rel}

    for path in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        update_imports_in_file(path, replacements, dry_run=dry_run)


# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------


def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Delete duplicate modules and rewrite imports."
    )
    parser.add_argument(
        "--root",
        "-r",
        type=Path,
        required=True,
        help="Root folder of your project (e.g. path/to/myapp)",
    )
    parser.add_argument(
        "--report",
        "-R",
        type=Path,
        required=True,
        help="JSON report file from duplicate_finder.py",
    )
    parser.add_argument(
        "--backup-dir",
        "-b",
        type=Path,
        default=Path("backups"),
        help="Where to store backups before deletion/patch",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    args = parser.parse_args()

    if not args.root.is_dir():
        logging.error(f"Project root {args.root} does not exist or is not a directory.")
        return
    if not args.report.is_file():
        logging.error(f"Report file {args.report} not found.")
        return

    duplicates = load_report(args.report)
    if not duplicates:
        logging.info("No duplicates to process.")
        return

    # Prepare backup directory
    if not args.dry_run:
        args.backup_dir.mkdir(parents=True, exist_ok=True)

    for pair in duplicates:
        keep, delete = determine_keep_delete(pair)
        logging.info(f"Keeping: {keep}  |  Deleting: {delete}")

        # Backup delete-target and all project files if needed
        if not args.dry_run:
            backup_file(delete, args.backup_dir)

        # Delete the duplicate file
        delete_file(delete, dry_run=args.dry_run)

        # Patch import statements across the project
        update_imports(args.root, keep, delete, dry_run=args.dry_run)

    logging.info("✅ Cleanup complete.")


if __name__ == "__main__":
    main()
