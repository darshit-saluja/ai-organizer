"""
build_roadmap.py — Takes scanned file data, sends it to an LLM via Gemini API,
and generates a structured ROADMAP.md.

Usage:
    python tools/build_roadmap.py [--input PATH] [--output PATH]

Requires:
    GEMINI_API_KEY in .env
    GEMINI_MODEL in .env (optional, defaults to gemini-flash-latest)
"""

import os
import sys
import json
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv


# ─── LLM Prompt ───────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert project organizer and strategic planner. 
Your job is to take a collection of scattered notes, ideas, plans, and documents 
and transform them into a single, clear, actionable roadmap.

You are ruthlessly practical. No fluff, no filler. Every word you write should 
help the user stop overthinking and start executing."""

USER_PROMPT_TEMPLATE = """I have {file_count} scattered files related to a project. 
They contain various notes, ideas, plans, and thoughts that I've been jumping between. 
I need you to make sense of all of them and create a clear roadmap.

Here are the files:

{files_content}

---

Analyze ALL of the above files and produce a structured ROADMAP in Markdown format. 
Follow this exact structure:

## Project Overview
Write 2-3 sentences summarizing the project. What is it about? What is the end goal?

## Key Themes Identified
Group the content into 3-7 major themes or topic areas. 
For each theme, briefly explain what it covers.

## Roadmap: Execution Phases

Break the project into clear, sequential phases. For each phase:

### Phase N: [Phase Title]
**Goal**: What this phase achieves
**Priority**: High / Medium / Low

**Action Items**:
1. Specific, concrete task
2. Another specific task
3. ...

(Repeat for each phase. Usually 3-6 phases is ideal.)

## Immediate Next Steps
List the top 5 concrete actions the user should take RIGHT NOW to get started. 
These should be specific enough that the user can begin working on them immediately 
without needing to consult any other document.

## Notes & Warnings
- Flag any gaps in the plan (topics mentioned but not detailed)
- Flag any contradictions in the strategy
- Suggest any missing information the user should figure out before proceeding

---

IMPORTANT RULES:
- Be specific and actionable, not vague
- Do NOT mention or list the names of the source files in the output
- If a file is irrelevant or contains noise, say so
- Prioritize clarity over completeness — the user needs to START WORKING, not read more
- Use plain language, avoid jargon unless it's necessary
- Do NOT wrap the output in a markdown code block — just output raw markdown"""


def build_files_content(files_data: list[dict]) -> str:
    """Format all file contents for the prompt."""
    sections = []
    for f in files_data:
        sections.append(
            f"### FILE: {f['filename']}\n"
            f"(Words: {f['metadata']['word_count']}, Lines: {f['metadata']['line_count']})\n\n"
            f"{f['content']}\n"
        )
    return "\n---\n\n".join(sections)


def call_gemini(system_prompt: str, user_prompt: str, api_key: str, model: str) -> str:
    """Call the Gemini REST API with retry logic for overloaded / rate-limited responses."""
    import time

    # Fallback model chain — try primary, then stable fallback
    models_to_try = [model]
    if model != "gemini-flash-latest":
        models_to_try.append("gemini-flash-latest")

    headers = {"Content-Type": "application/json"}
    payload = {
        "contents": [{"parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"temperature": 0.4, "maxOutputTokens": 8000},
    }

    for attempt_model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{attempt_model}:generateContent?key={api_key}"
        max_retries = 4
        wait = 10  # seconds

        for attempt in range(1, max_retries + 1):
            print(f"[build_roadmap] Calling Gemini API (model: {attempt_model}, attempt {attempt}/{max_retries})...")
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=120)

                # Retry on overload or rate limit
                if response.status_code in (429, 503):
                    print(f"[WARN] Model {attempt_model} overloaded (HTTP {response.status_code}). Waiting {wait}s before retry...")
                    time.sleep(wait)
                    wait *= 2  # exponential backoff
                    continue

                response.raise_for_status()

            except requests.exceptions.Timeout:
                print(f"[WARN] Request timed out (attempt {attempt}). Retrying...")
                time.sleep(wait)
                wait *= 2
                continue
            except requests.exceptions.ConnectionError:
                print("[ERROR] Could not connect to Gemini API. Check your internet connection.")
                sys.exit(1)
            except requests.exceptions.HTTPError as e:
                print(f"[ERROR] API returned error: {e}")
                print(f"        Response: {response.text}")
                sys.exit(1)

            result = response.json()
            if "candidates" not in result or not result["candidates"]:
                print(f"[ERROR] Unexpected API response: {json.dumps(result, indent=2)}")
                sys.exit(1)

            if attempt_model != model:
                print(f"[INFO] Used fallback model: {attempt_model}")
            return result["candidates"][0]["content"]["parts"][0]["text"]

        print(f"[WARN] All retries failed for model {attempt_model}. Trying next model...")

    print("[ERROR] All models failed. Please try again in a few minutes.")
    sys.exit(1)


def main():
    # Load environment variables
    project_root = Path(__file__).resolve().parent.parent
    load_dotenv(project_root / ".env")

    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    if not api_key:
        print("[ERROR] GEMINI_API_KEY not found in .env")
        print("        Add your API key to the .env file and try again.")
        sys.exit(1)

    # Parse arguments
    parser = argparse.ArgumentParser(description="Build a roadmap from scanned files using LLM")
    parser.add_argument(
        "--input",
        default=str(project_root / ".tmp" / "scanned_files.json"),
        help="Path to scanned_files.json (default: .tmp/scanned_files.json)",
    )
    parser.add_argument(
        "--output",
        default=str(project_root / "ROADMAP.md"),
        help="Path to output roadmap (default: ROADMAP.md in project root)",
    )
    args = parser.parse_args()

    # Read scanned files
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Scanned files not found: {input_path}")
        print("        Run scan_files.py first.")
        sys.exit(1)

    files_data = json.loads(input_path.read_text(encoding="utf-8"))
    print(f"[build_roadmap] Loaded {len(files_data)} file(s) from {input_path}")

    # Build prompt
    files_content = build_files_content(files_data)
    user_prompt = USER_PROMPT_TEMPLATE.format(
        file_count=len(files_data),
        files_content=files_content,
    )

    # Call LLM
    roadmap_content = call_gemini(SYSTEM_PROMPT, user_prompt, api_key, model)

    # Clean up response — remove markdown code fences if the model wraps output
    if roadmap_content.startswith("```"):
        lines = roadmap_content.split("\n")
        # Remove first line (```markdown or ```) and last line (```)
        if lines[-1].strip() == "```":
            lines = lines[1:-1]
        else:
            lines = lines[1:]
        roadmap_content = "\n".join(lines)

    # Write roadmap
    output_path = Path(args.output)
    header = (
        "# 🗺️ Project Roadmap\n\n"
        "---\n\n"
    )
    output_path.write_text(header + roadmap_content, encoding="utf-8")

    print(f"[build_roadmap] Roadmap written to: {output_path}")
    return str(output_path)


if __name__ == "__main__":
    main()
