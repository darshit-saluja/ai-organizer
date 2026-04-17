"""
scan_files.py — Reads all .txt and .md files from the input directory
and outputs structured JSON with filename, content, and metadata.

Usage:
    python tools/scan_files.py [--input-dir PATH]

Output:
    .tmp/scanned_files.json
"""

import os
import sys
import json
import argparse
from pathlib import Path


def scan_directory(input_dir: str) -> list[dict]:
    """
    Scan the input directory for .txt and .md files.
    Returns a list of dicts with file info and content.
    """
    input_path = Path(input_dir)

    if not input_path.exists():
        print(f"[ERROR] Input directory does not exist: {input_path}")
        sys.exit(1)

    supported_extensions = {".txt", ".md"}
    files_data = []

    for file_path in sorted(input_path.iterdir()):
        if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
            try:
                content = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                # Fallback for files with different encoding
                try:
                    content = file_path.read_text(encoding="latin-1")
                except Exception as e:
                    print(f"[WARN] Skipping {file_path.name}: {e}")
                    continue

            word_count = len(content.split())
            line_count = content.count("\n") + 1 if content else 0

            files_data.append({
                "filename": file_path.name,
                "path": str(file_path.resolve()),
                "extension": file_path.suffix.lower(),
                "content": content,
                "metadata": {
                    "word_count": word_count,
                    "line_count": line_count,
                    "size_bytes": file_path.stat().st_size,
                },
            })

    return files_data


def main():
    parser = argparse.ArgumentParser(description="Scan .txt and .md files from input directory")
    parser.add_argument(
        "--input-dir",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".tmp", "input"),
        help="Path to the input directory (default: .tmp/input/)",
    )
    parser.add_argument(
        "--output",
        default=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".tmp", "scanned_files.json"),
        help="Path to the output JSON file (default: .tmp/scanned_files.json)",
    )
    args = parser.parse_args()

    print(f"[scan_files] Scanning: {args.input_dir}")
    files_data = scan_directory(args.input_dir)

    if not files_data:
        print("[ERROR] No .txt or .md files found in the input directory.")
        print(f"        Drop your files into: {os.path.abspath(args.input_dir)}")
        sys.exit(1)

    print(f"[scan_files] Found {len(files_data)} file(s):")
    for f in files_data:
        print(f"  - {f['filename']} ({f['metadata']['word_count']} words, {f['metadata']['line_count']} lines)")

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(files_data, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"[scan_files] Output written to: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    main()
