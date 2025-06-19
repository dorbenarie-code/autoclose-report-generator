#!/usr/bin/env python3
"""
duplicate_finder.py

Scan a Python project for near-duplicate modules (>= threshold similarity),
so you can consolidate into a single source of truth.
"""

import argparse
import logging
import json
from pathlib import Path
from difflib import SequenceMatcher
from importlib.util import find_spec

# ------------------------------------------------------------------------------
# CONFIGURATION / DEFAULTS
# ------------------------------------------------------------------------------

DEFAULT_THRESHOLD = 0.90
MIN_FILE_SIZE_BYTES = 200  # skip tiny files unlikely to contain logic
SKIP_DIRS = {"__pycache__", ".git", ".venv", "venv", "node_modules"}

# ------------------------------------------------------------------------------
# FUNCTIONS
# ------------------------------------------------------------------------------


def setup_logging():
    """Configure root logger to output INFO-level messages."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def collect_python_files(root: Path, pattern: str = "*.py") -> list[Path]:
    """
    Walk `root`, skipping SKIP_DIRS, and return all .py files larger than MIN_FILE_SIZE_BYTES.
    """
    files = []
    for path in root.rglob(pattern):
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        try:
            if path.stat().st_size < MIN_FILE_SIZE_BYTES:
                continue
        except OSError:
            logging.warning(f"Cannot stat file {path}, skipping.")
            continue
        files.append(path)
    logging.info(f"Found {len(files)} candidate .py files under {root}")
    return files


def read_lines(path: Path) -> list[str]:
    """Read all lines from `path`, handling encoding errors gracefully."""
    try:
        return path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except Exception as e:
        logging.warning(f"Failed to read {path}: {e}")
        return []


def extract_imports(lines: list[str]) -> set[str]:
    """
    Extract imported module names and symbols for additional similarity check.
    Simple regex-lite: looks for lines starting with 'import' or 'from'.
    """
    imports = set()
    for ln in lines:
        ln = ln.strip()
        if ln.startswith("import "):
            parts = ln.split()
            # only top-level module
            imports.add(parts[1].split(".")[0])
        elif ln.startswith("from "):
            parts = ln.split()
            imports.add(parts[1].split(".")[0])
    return imports


def similarity_score(lines1: list[str], lines2: list[str]) -> float:
    """Return a float in [0,1] representing how similar the two sequences are."""
    return SequenceMatcher(None, lines1, lines2).ratio()


def compare_pair(path1: Path, path2: Path, threshold: float) -> dict | None:
    """
    Compare two files for content and import similarity.
    Returns a report dict if they exceed `threshold`, else None.
    """
    lines1 = read_lines(path1)
    lines2 = read_lines(path2)
    if not lines1 or not lines2:
        return None

    content_ratio = similarity_score(lines1, lines2)
    if content_ratio < threshold:
        return None

    imports1 = extract_imports(lines1)
    imports2 = extract_imports(lines2)
    common_imports = sorted(imports1 & imports2)

    return {
        "file1": str(path1),
        "file2": str(path2),
        "content_similarity": round(content_ratio, 4),
        "common_imports": common_imports,
    }


def find_duplicates(files: list[Path], threshold: float) -> list[dict]:
    """
    Iterate through all unique pairs and collect those exceeding the similarity threshold.
    """
    results = []
    seen = set()
    total = len(files)
    for idx1 in range(total):
        for idx2 in range(idx1 + 1, total):
            p1, p2 = files[idx1], files[idx2]
            key = tuple(sorted((str(p1), str(p2))))
            if key in seen:
                continue
            report = compare_pair(p1, p2, threshold)
            if report:
                logging.info(
                    f"⚠️  Similar: {report['file1']} ↔️ {report['file2']} "
                    f"{int(report['content_similarity']*100)}% match"
                )
                results.append(report)
            seen.add(key)
    return results


# ------------------------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------------------------


def main():
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Detect near-duplicate Python modules in a project."
    )
    parser.add_argument(
        "--root",
        "-r",
        type=Path,
        required=True,
        help="Project root folder to scan (e.g. path/to/myapp)",
    )
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Content similarity threshold [0–1] (default {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--pattern",
        "-p",
        type=str,
        default="*.py",
        help="Glob pattern to match files (default '*.py')",
    )
    parser.add_argument(
        "--json", action="store_true", help="Also output full results as JSON"
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Exit with code 1 if any duplicates are found (for CI enforcement)",
    )
    args = parser.parse_args()

    if not args.root.is_dir():
        logging.error(f"Root path {args.root} is not a directory.")
        return

    files = collect_python_files(args.root, args.pattern)
    duplicates = find_duplicates(files, args.threshold)

    logging.info(f"Scan complete: found {len(duplicates)} pair(s) over threshold.")
    if args.json:
        print(json.dumps(duplicates, indent=2))
    if args.fail_on_diff and duplicates:
        logging.error(
            "Duplicates found and --fail-on-diff is set. Exiting with code 1."
        )
        exit(1)


if __name__ == "__main__":
    main()
