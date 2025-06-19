#!/usr/bin/env python3
"""
Script: log_fixer.py
Purpose: Replace print statements with log calls and enforce a uniform logger initialization.
"""
import sys
import os
import re
from pathlib import Path

# Project root and target configuration
ROOT = Path(__file__).resolve().parents[1] / "myapp"
EXCLUDE_FILES = {"logger_config.py", "__init__.py"}

# Patterns and constants
LOGGER_IMPORT = "from myapp.utils.logger_config import get_logger"
LOGGER_INIT = "log = get_logger(__name__)"
PRINT_PATTERN = re.compile(r"^\s*print\((.*)\)\s*$", flags=re.DOTALL)
GETLOGGER_PATTERN = re.compile(r"^\s*(?:logger|log)\s*=\s*logging\.getLogger\(.*\)")
LOGGER_INIT_PATTERN = re.compile(r"log\s*=\s*get_logger\(__name__\)")


def replace_prints(lines: list[str]) -> list[str]:
    """
    Replace print(...) calls with log.info(...) or log.error(...) based on content.
    Skip commented lines.
    """
    new_lines = []
    for line in lines:
        # Skip commented lines
        if line.lstrip().startswith("#"):
            new_lines.append(line)
            continue
        match = PRINT_PATTERN.match(line)
        if match:
            content = match.group(1)
            indent = line[: line.find("print")]
            # Determine log level
            if "error" in content.lower() or "❌" in content:
                replacement = f"{indent}log.error({content})\n"
            else:
                replacement = f"{indent}log.info({content})\n"
            new_lines.append(replacement)
        else:
            new_lines.append(line)
    return new_lines


def remove_manual_loggers(lines: list[str]) -> list[str]:
    """
    Replace any manual logging.getLogger(...) assignments with our standard LOGGER_INIT.
    """
    new_lines = []
    for line in lines:
        if GETLOGGER_PATTERN.match(line):
            new_lines.append(f"{LOGGER_INIT}\n")
        else:
            new_lines.append(line)
    return new_lines


def ensure_logger(lines: list[str]) -> list[str]:
    """
    Ensure that LOGGER_IMPORT and LOGGER_INIT are present exactly once,
    inserted after any shebang, encoding comment, and module docstring.
    """
    has_import = any("get_logger" in l for l in lines)
    has_init = any(LOGGER_INIT_PATTERN.search(l) for l in lines)
    if has_import and has_init:
        return lines

    new_lines = []
    i = 0
    # Preserve shebang
    if lines and lines[0].startswith("#!"):
        new_lines.append(lines[0])
        i = 1
    # Preserve encoding comment
    if i < len(lines) and lines[i].startswith("#") and "coding" in lines[i]:
        new_lines.append(lines[i])
        i += 1
    # Preserve module docstring
    if i < len(lines) and re.match(r"^\s*[ru]?['\"]{3}", lines[i]):
        new_lines.append(lines[i])
        i += 1
        while i < len(lines) and not re.search(r"['\"]{3}", lines[i]):
            new_lines.append(lines[i])
            i += 1
        if i < len(lines):
            new_lines.append(lines[i])
            i += 1

    # Insert our import and init
    new_lines.append(f"{LOGGER_IMPORT}\n")
    new_lines.append(f"{LOGGER_INIT}\n")

    # Append the rest
    new_lines.extend(lines[i:])
    return new_lines


def process_file(file_path: Path) -> None:
    """
    Read a file, apply replacements, and write back if changes occurred.
    """
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    original = lines.copy()

    lines = replace_prints(lines)
    lines = remove_manual_loggers(lines)
    lines = ensure_logger(lines)

    if lines != original:
        file_path.write_text("".join(lines), encoding="utf-8")
        print(f"✅ Updated: {file_path.relative_to(Path.cwd())}")


def main() -> int:
    """
    Iterate through all Python files under ROOT and process each one.
    """
    for path in ROOT.rglob("*.py"):
        if path.name in EXCLUDE_FILES:
            continue
        process_file(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# To run:
# python scripts/log_fixer.py
