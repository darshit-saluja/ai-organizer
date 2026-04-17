"""
run_organizer.py — Main pipeline entry point.

Orchestrates the full file organization workflow:
1. Scans .tmp/input/ for .txt and .md files
2. Sends content to LLM for analysis
3. Generates ROADMAP.md in project root

Usage:
    python run_organizer.py
    python run_organizer.py --input-dir "path/to/your/files"
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path


def run_step(description: str, command: list[str]) -> None:
    """Run a pipeline step and handle errors."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}\n")

    result = subprocess.run(command, capture_output=False)

    if result.returncode != 0:
        print(f"\n[PIPELINE ERROR] Step failed: {description}")
        print(f"                 Command: {' '.join(command)}")
        sys.exit(1)


def main():
    project_root = Path(__file__).resolve().parent
    tools_dir = project_root / "tools"

    parser = argparse.ArgumentParser(
        description="AI Organizer — Turn messy files into a clear roadmap",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_organizer.py
      Scans .tmp/input/ and generates ROADMAP.md

  python run_organizer.py --input-dir "C:/Users/me/Desktop/project_notes"
      Scans a custom directory instead of .tmp/input/

  python run_organizer.py --output "C:/Users/me/Desktop/ROADMAP.md"
      Saves the roadmap to a custom location
        """,
    )
    parser.add_argument(
        "--input-dir",
        default=str(project_root / ".tmp" / "input"),
        help="Directory containing .txt/.md files to organize",
    )
    parser.add_argument(
        "--output",
        default=str(project_root / "ROADMAP.md"),
        help="Where to save the generated roadmap (default: ROADMAP.md)",
    )
    args = parser.parse_args()

    # ─── Pre-flight checks ─────────────────────────────────────────────
    input_dir = Path(args.input_dir)

    print(f"\nAI Organizer -- File -> Roadmap Pipeline")
    print(f"   Input:  {input_dir}")
    print(f"   Output: {args.output}")

    if not input_dir.exists():
        print(f"\n[ERROR] Input directory does not exist: {input_dir}")
        print(f"        Create it and add your .txt/.md files, then run again.")
        sys.exit(1)

    # Count eligible files
    eligible = [f for f in input_dir.iterdir() if f.suffix.lower() in {".txt", ".md"}]
    if not eligible:
        print(f"\n[ERROR] No .txt or .md files found in: {input_dir}")
        print(f"        Drop your files there and run again.")
        sys.exit(1)

    print(f"   Files:  {len(eligible)} file(s) found\n")

    # ─── Step 1: Scan files ────────────────────────────────────────────
    scanned_output = str(project_root / ".tmp" / "scanned_files.json")

    run_step(
        "Step 1/2 — Scanning files",
        [sys.executable, str(tools_dir / "scan_files.py"),
         "--input-dir", str(input_dir),
         "--output", scanned_output],
    )

    # ─── Step 2: Build roadmap ─────────────────────────────────────────
    run_step(
        "Step 2/2 — Building roadmap with LLM",
        [sys.executable, str(tools_dir / "build_roadmap.py"),
         "--input", scanned_output,
         "--output", args.output],
    )

    # ─── Done ──────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  DONE! Your roadmap is ready.")
    print(f"{'='*60}")
    print(f"\nOpen: {args.output}")
    print(f"\nStop overthinking. Start working.\n")


if __name__ == "__main__":
    main()
