#!/usr/bin/env python3
"""
verify_integrity.py

Generate and verify a baseline manifest of file checksums to ensure file integrity
across your Python project.

Commands:
  init    Scan files and write checksums to a JSON manifest.
  check   Recompute checksums and compare against the manifest, reporting any changes.

Usage:
  # Create initial manifest
  python verify_integrity.py init --root ./myapp --manifest integrity.json

  # Later, verify no files were added, removed, or tampered with
  python verify_integrity.py check --root ./myapp --manifest integrity.json
"""

import argparse
import hashlib
import json
import logging
from pathlib import Path

# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------

SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules"}
FILE_PATTERN = "*.py"
DEFAULT_MANIFEST = "integrity_manifest.json"

# ------------------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------------------


def setup_logging():
    """Configure logging for INFO-level output."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# ------------------------------------------------------------------------------
# CORE FUNCTIONS
# ------------------------------------------------------------------------------


def collect_files(root: Path, pattern: str) -> list[Path]:
    """
    Recursively collect all files matching `pattern` under `root`,
    skipping directories in SKIP_DIRS.
    """
    files = []
    for path in root.rglob(pattern):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.is_file():
            files.append(path)
    logging.info(f"Collected {len(files)} files under {root}")
    return sorted(files)


def compute_checksum(path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the hex digest of `path` using the specified hash algorithm.
    """
    h = hashlib.new(algorithm)
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def init_manifest(root: Path, manifest_path: Path, pattern: str):
    """
    Scan all matching files and write their checksums to `manifest_path`.
    """
    files = collect_files(root, pattern)
    manifest = {}
    for file in files:
        checksum = compute_checksum(file)
        manifest[str(file.relative_to(root))] = checksum
        logging.debug(f"Hashed {file}: {checksum}")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    logging.info(f"Integrity manifest written to {manifest_path}")


def check_integrity(root: Path, manifest_path: Path, pattern: str):
    """
    Load `manifest_path`, recompute checksums under `root`, and report:
      - Missing files
      - New files
      - Modified files
    """
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        logging.error(f"Failed to read manifest {manifest_path}: {e}")
        return

    current_files = {str(p.relative_to(root)): p for p in collect_files(root, pattern)}
    baseline_files = set(manifest.keys())
    current_set = set(current_files.keys())

    missing = baseline_files - current_set
    added = current_set - baseline_files
    modified = []

    for rel in baseline_files & current_set:
        path = current_files[rel]
        new_sum = compute_checksum(path)
        if new_sum != manifest[rel]:
            modified.append(rel)
            logging.debug(
                f"Checksum mismatch: {rel} (was {manifest[rel]}, now {new_sum})"
            )

    # Report
    if missing:
        logging.warning(f"Missing files ({len(missing)}):")
        for rel in sorted(missing):
            logging.warning(f"  - {rel}")
    if added:
        logging.warning(f"New files ({len(added)}):")
        for rel in sorted(added):
            logging.warning(f"  + {rel}")
    if modified:
        logging.warning(f"Modified files ({len(modified)}):")
        for rel in sorted(modified):
            logging.warning(f"  * {rel}")

    if not (missing or added or modified):
        logging.info("All files match the integrity manifest. ✅")
    else:
        logging.info("Integrity check complete with issues detected. ❌")


# ------------------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------------------


def main():
    setup_logging()
    parser = argparse.ArgumentParser(
        description="Initialize or verify file integrity manifest."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # init command
    p_init = sub.add_parser("init", help="Create a new integrity manifest")
    p_init.add_argument(
        "--root", "-r", type=Path, required=True, help="Project root directory"
    )
    p_init.add_argument(
        "--manifest",
        "-m",
        type=Path,
        default=Path(DEFAULT_MANIFEST),
        help="Path to write the manifest JSON",
    )
    p_init.add_argument(
        "--pattern",
        "-p",
        type=str,
        default=FILE_PATTERN,
        help="Glob pattern for files (default '*.py')",
    )

    # check command
    p_chk = sub.add_parser("check", help="Verify files against an existing manifest")
    p_chk.add_argument(
        "--root", "-r", type=Path, required=True, help="Project root directory"
    )
    p_chk.add_argument(
        "--manifest",
        "-m",
        type=Path,
        default=Path(DEFAULT_MANIFEST),
        help="Path to read the manifest JSON",
    )
    p_chk.add_argument(
        "--pattern",
        "-p",
        type=str,
        default=FILE_PATTERN,
        help="Glob pattern for files (default '*.py')",
    )

    args = parser.parse_args()

    root = getattr(args, "root")
    manifest = getattr(args, "manifest")
    pattern = getattr(args, "pattern")

    if not root.is_dir():
        logging.error(f"Root path {root} is not a directory.")
        return

    if args.command == "init":
        init_manifest(root, manifest, pattern)
    elif args.command == "check":
        if not manifest.is_file():
            logging.error(f"Manifest file {manifest} not found.")
            return
        check_integrity(root, manifest, pattern)


if __name__ == "__main__":
    main()
