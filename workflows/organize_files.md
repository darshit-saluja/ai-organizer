# Organize Files → Roadmap

## Purpose
Turn a collection of scattered `.txt` and `.md` files into a single, clear, actionable roadmap.

## When to Use
- You have a pile of notes, ideas, plans, and brainstorms spread across multiple files
- You're stuck jumping between documents and can't figure out where to start
- You want a structured plan extracted from your existing thinking

## Required Inputs
- **Files**: Drop `.txt` and/or `.md` files into `.tmp/input/`
- **API Key**: `GEMINI_API_KEY` must be set in `.env`

## How to Run

```bash
# Default: reads from .tmp/input/, writes to ROADMAP.md
python run_organizer.py

# Custom input directory
python run_organizer.py --input-dir "C:/path/to/your/files"

# Custom output location
python run_organizer.py --output "C:/path/to/ROADMAP.md"
```

## Pipeline Steps

| Step | Tool | What It Does |
|------|------|-------------|
| 1 | `tools/scan_files.py` | Reads all .txt/.md files, extracts content, writes `.tmp/scanned_files.json` |
| 2 | `tools/build_roadmap.py` | Sends content to LLM, analyzes relationships, generates `ROADMAP.md` |

## Expected Output

A `ROADMAP.md` file containing:
- **Project Overview** — What the files collectively point toward
- **Key Themes** — Major topic areas grouped from across all files
- **File Relationship Map** — How files connect, overlap, or contradict
- **Execution Phases** — Ordered phases with concrete action items
- **Immediate Next Steps** — Top 5 things to do right now

## Edge Cases & Notes

- **Large files**: If total content exceeds the model's context window, the LLM may truncate or miss details. Consider splitting very large files or summarizing them first.
- **Non-English content**: The LLM handles multiple languages but roadmap output will match the dominant language of the input files.
- **Encoding issues**: The scanner tries UTF-8 first, then Latin-1. Files with other encodings may be skipped with a warning.
- **Empty files**: Files with no content are scanned but won't contribute to the roadmap.
- **Previous roadmaps**: Running the pipeline again will overwrite the existing `ROADMAP.md`. Archive manually if needed.

## Customization

### Changing the LLM Model
Set `GEMINI_MODEL` in `.env` to any valid Gemini model:
```
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MODEL=gemini-2.5-pro
```

### Adjusting the Prompt
The analysis prompt lives in `tools/build_roadmap.py` in the `USER_PROMPT_TEMPLATE` variable. Modify it to:
- Focus on specific aspects (e.g., "prioritize technical architecture decisions")
- Change the output structure
- Add domain-specific context

## Lessons Learned
*(Updated as the system evolves)*

- None yet — this is the initial version.
