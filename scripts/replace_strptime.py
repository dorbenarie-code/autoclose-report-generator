import os
import re
from pathlib import Path

# הגדרות
BASE_DIR = Path(__file__).resolve().parents[1] / "myapp"
TARGET_PATTERN = r"datetime\.strptime\(([^)]+)\)"
IMPORT_LINE = "from myapp.utils.date_utils import parse_date_flex"

def find_py_files(root: Path):
    return list(root.rglob("*.py"))

def process_file(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    changed = False
    modified_lines = []
    replaced_count = 0
    import_already = any(IMPORT_LINE in line for line in lines)

    for line in lines:
        if "datetime.strptime" in line:
            matches = list(re.finditer(TARGET_PATTERN, line))
            if matches:
                for match in matches:
                    args = match.group(1).strip()
                    new_expr = f"parse_date_flex({args.split(',')[0].strip()})"
                    line = line.replace(match.group(0), new_expr)
                    replaced_count += 1
                    changed = True
        modified_lines.append(line)

    if changed:
        backup_path = file_path.with_suffix(".bak")
        os.rename(file_path, backup_path)

        # הוספת import אם חסר
        if not import_already:
            for i, line in enumerate(modified_lines):
                if line.strip().startswith("from") or line.strip().startswith("import"):
                    continue
                modified_lines.insert(i, IMPORT_LINE + "\n")
                break

        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(modified_lines)

    return changed, replaced_count

def main():
    print(f"🔍 Scanning Python files under: {BASE_DIR}")
    files = find_py_files(BASE_DIR)
    total_replacements = 0
    changed_files = []

    for file_path in files:
        changed, count = process_file(file_path)
        if changed:
            print(f"✅ {file_path} — replaced {count} instance(s)")
            changed_files.append(file_path)
            total_replacements += count

    print(f"\n📦 Done: {len(changed_files)} file(s) changed, {total_replacements} total replacements")

if __name__ == "__main__":
    main()
