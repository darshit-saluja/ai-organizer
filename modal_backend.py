import modal
from pydantic import BaseModel
import requests
import json
import time
import os

app = modal.App("ai-organizer-backend")

# We build a simple image with requests and fastapi installed
image = modal.Image.debian_slim().pip_install("requests", "fastapi[standard]")

# -- Pydantic Schemas for the Web API --
class FileInput(BaseModel):
    filename: str
    content: str
    word_count: int
    line_count: int

class ChatMessage(BaseModel):
    role: str # 'user' or 'assistant'
    content: str

class RoadmapRequest(BaseModel):
    files: list[FileInput]
    messages: list[ChatMessage]
    current_roadmap: str | None = None

# -- Prompts --
SYSTEM_PROMPT = """You are an expert project organizer and strategic planner. 
Your job is to take a collection of scattered notes, ideas, plans, and documents 
and transform them into a single, clear, RUTHLESSLY DETAILED actionable roadmap.

CORE BEHAVIOR:
1. ROADMAP QUALITY (HIGHEST PRIORITY): 
   When providing or updating the roadmap, do NOT summarize. You must deliver a LONG, high-density professional document.
   The project roadmap MUST contain:
   - ## Project Overview: 3-5 detailed sentences synthesizing the end-goal.
   - ## Key Themes Identified: 4-7 major topic areas with deep analysis of each.
   - ## Roadmap: Execution Phases: 4-6 sequential phases. Each phase must have:
      - ### Phase N: [Title]
      - **Goal**: Clear outcome
      - **Priority**: Status
      - **Action Items**: A detailed, bulleted checklist of 5-8 specific tasks per phase.
   - ## Immediate Next Steps: 5 concrete actions to take immediately.
   - ## Notes & Warnings: Comprehensive section flagging gaps or contradictions.

2. CHAT & WRAPPING:
   - Wrap the FULL roadmap inside [ROADMAP_START] and [ROADMAP_END] tags.
   - Precede the roadmap with a brief (1-sentence) conversational intro.
   - If the user asks a general question, answer it using RICH MARKDOWN FORMATTING.
   - NEVER provide "bulk text" paragraphs. Use lists, bold headers, and hierarchy for ALL chat responses to ensure they are readable and structured.
   - Example: "Phase 5 was derived from:
     - **Factor A**: Details here...
     - **Factor B**: Details here...
     "

3. CONTEXT:
   - Do NOT mention filenames or citations in the roadmap.
   - Use plain but professional language.
   - Always assume the goal is to stop overthinking and start working."""

USER_PROMPT_TEMPLATE = """CONTEXT: I have {file_count} scattered files related to a project.
{files_content}

CURRENT ROADMAP STATE:
{current_roadmap}

---
Based on the conversation and the files above, fulfill my request.
If I'm asking for a change or if this is the initial request, provide a brief intro and the FULL DETAILED roadmap wrapped in [ROADMAP_START] and [ROADMAP_END].
If I'm just asking a question, answer it directly using RICH MARKDOWN (lists, hierarchy, bolding)."""


def call_gemini(system_prompt: str, user_prompt: str, api_key: str, model: str, history: list[dict] = None) -> str:
    """Call the Gemini REST API with support for conversation history."""
    import time

    models_to_try = [model]
    if model != "gemini-flash-latest":
        models_to_try.append("gemini-flash-latest")

    headers = {"Content-Type": "application/json"}
    
    gemini_history = []
    if history:
        for msg in history[:-1]:
            gemini_history.append({
                "role": "user" if msg['role'] == 'user' else "model",
                "parts": [{"text": msg['content']}]
            })

    payload = {
        "contents": gemini_history + [{"role": "user", "parts": [{"text": user_prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 8000},
    }

    for attempt_model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{attempt_model}:generateContent?key={api_key}"
        max_retries = 3
        wait = 8

        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                if response.status_code in (429, 503):
                    time.sleep(wait)
                    wait *= 2
                    continue
                response.raise_for_status()
            except Exception as e:
                print(f"[RETRY] Model {attempt_model} failed: {e}")
                continue

            result = response.json()
            if "candidates" not in result or not result["candidates"]:
                continue

            return result["candidates"][0]["content"]["parts"][0]["text"]

    raise Exception("All API retries failed.")


@app.function(image=image, secrets=[modal.Secret.from_dotenv(__file__)])
@modal.fastapi_endpoint(method="POST", docs=True)
def generate_roadmap(req: RoadmapRequest):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY missing."}
    
    model = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

    sections = []
    for f in req.files:
        sections.append(f"### FILE: {f.filename}\n{f.content}")
    files_content = "\n---\n\n".join(sections)

    current_roadmap = req.current_roadmap or "None generated yet."
    last_user_msg = req.messages[-1].content if req.messages else "Generate the initial detailed roadmap."
    
    user_prompt = USER_PROMPT_TEMPLATE.format(
        file_count=len(req.files),
        files_content=files_content,
        current_roadmap=current_roadmap
    )
    user_prompt += f"\n\nUSER REQUEST: {last_user_msg}"
    history_json = [{"role": msg.role, "content": msg.content} for msg in req.messages]

    try:
        response_text = call_gemini(SYSTEM_PROMPT, user_prompt, api_key, model, history_json)
    except Exception as e:
        return {"error": str(e)}

    return {"response": response_text}
