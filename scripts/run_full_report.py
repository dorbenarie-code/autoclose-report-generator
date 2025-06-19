#!/usr/bin/env python3
from scripts.run import main as run_single
from pathlib import Path

def main():
    for f in Path("uploads").glob("*.csv"):
        run_single([str(f)])

if __name__ == "__main__":
    main() 