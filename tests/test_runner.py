import subprocess
import sys
from pathlib import Path

def test_cli_report_exit_code(tmp_path):
    script = Path(__file__).parent.parent / "scripts" / "run.py"
    result = subprocess.run([sys.executable, str(script), str(tmp_path/"dummy.csv")])
    assert result.returncode == 0 