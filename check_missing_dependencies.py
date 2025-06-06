import os
import ast
import sys
import argparse
from typing import Set

# מודולי סטנדרט פייתון – הרחבה לפי הצורך
STDLIB_MODULES = {
    "os",
    "sys",
    "re",
    "math",
    "datetime",
    "pathlib",
    "logging",
    "json",
    "typing",
    "base64",
    "collections",
    "csv",
    "time",
    "itertools",
    "threading",
    "subprocess",
    "shutil",
    "unittest",
    "random",
    "string",
    "functools",
    "copy",
    "http",
    "email",
    "socket",
    "asyncio",
    "io",
    "enum",
    "traceback",
    "ast",
    "argparse",
    "pickle",
    "inspect",
    "platform",
    "pprint",
    "queue",
    "statistics",
    "tempfile",
    "warnings",
}


def extract_imports(path: str) -> Set[str]:
    """
    Extract all imported top-level modules from all .py files in a directory tree.
    Ignores syntax errors and non-Python files.
    """
    imports = set()
    for root, _, files in os.walk(path):
        for file in files:
            if not file.endswith(".py"):
                continue
            full_path = os.path.join(root, file)
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                tree = ast.parse(content, filename=full_path)
            except (SyntaxError, UnicodeDecodeError) as e:
                print(
                    f"⚠️ Warning: Could not parse {full_path} ({e.__class__.__name__}): {e}",
                    file=sys.stderr,
                )
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        imports.add(name.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])
    return imports


def load_requirements(path: str) -> Set[str]:
    """
    Load package names from requirements.txt, ignoring comments and versions.
    """
    modules = set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                package = (
                    line.split("==")[0]
                    .split(">=")[0]
                    .split("<")[0]
                    .split(";")[0]
                    .strip()
                )
                if package:
                    modules.add(package.lower())
    except FileNotFoundError:
        print(f"❌ Error: requirements file '{path}' not found.", file=sys.stderr)
        sys.exit(1)
    return modules


def main(project_dir: str, requirements_file: str):
    all_imports = extract_imports(project_dir)
    declared = load_requirements(requirements_file)

    missing = sorted(
        [
            mod
            for mod in all_imports
            if mod.lower() not in declared and mod.lower() not in STDLIB_MODULES
        ]
    )

    if missing:
        print("⚠️ Missing dependencies not declared in requirements.txt:")
        for mod in missing:
            print(f" - {mod}")
        print("\n💡 Suggested pip install command:")
        print(f"pip install {' '.join(missing)}")
        sys.exit(2)
    else:
        print("✅ All dependencies are declared.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Check missing dependencies compared to requirements.txt"
    )
    parser.add_argument(
        "--dir",
        default=".",
        help="Project directory to scan for imports (default: current directory)",
    )
    parser.add_argument(
        "--requirements",
        default="requirements.txt",
        help="Path to requirements.txt file (default: requirements.txt)",
    )
    args = parser.parse_args()

    main(args.dir, args.requirements)
