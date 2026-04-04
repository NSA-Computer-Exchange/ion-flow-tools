from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json
import os

from openai import OpenAI
from tools.ai_infor_genai import ask_infor_genai


class AIDocgenError(Exception):
    pass


def load_normalized_json(json_path: str | Path) -> Dict[str, Any]:
    json_path = Path(json_path)

    if not json_path.exists() or not json_path.is_file():
        raise FileNotFoundError(f"Normalized JSON not found: {json_path}")

    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def build_ai_prompt(data: Dict[str, Any]) -> str:
    flow_name = data.get("name", "Unknown Flow")
    flow_type = data.get("type", "")
    description = data.get("description", "")
    activities = data.get("activities", [])
    dependencies = data.get("dependencies", {})

    trimmed_payload = {
        "name": flow_name,
        "type": flow_type,
        "description": description,
        "activities": activities,
        "dependencies": dependencies,
    }

    return f"""
You are helping document an Infor ION dataflow for technical and semi-technical readers.

Generate concise but useful Markdown for the following sections:

## AI Summary
A short overview of what this flow appears to do.

## AI Functional Overview
Explain the likely purpose of the flow and how it moves/processes data.

## AI Dependency Review
Summarize important dependencies such as workflows, scripts, connection points, mappings, or APIs.

## AI Risks / Observations
Call out possible maintenance risks, missing context, fragile dependencies, unclear naming, or anything worth reviewing.

Rules:
- Be grounded only in the provided JSON.
- Do not invent system behavior that is not reasonably supported by the data.
- If something is unclear, say it appears or likely.
- Keep the tone professional and useful.
- Return Markdown only.
- Do not wrap the response in code fences.

Normalized dataflow JSON:
{json.dumps(trimmed_payload, indent=2)}
""".strip()


def generate_ai_markdown(
    data: Dict[str, Any],
    model: str = "gpt-5.4",
) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise AIDocgenError("OPENAI_API_KEY is not set")

    client = OpenAI(api_key=api_key)

    prompt = build_ai_prompt(data)

    response = client.responses.create(
        model=model,
        input=prompt,
    )

    text = getattr(response, "output_text", None)
    if not text:
        raise AIDocgenError("AI response did not contain output_text")

    return text.strip()


def generate_ai_doc_from_json(
    json_path: str | Path,
    model: str = "gpt-5.4",
    provider: str = "openai",
) -> str:
    data = load_normalized_json(json_path)

    if provider == "openai":
        return generate_ai_markdown(data, model=model)

    elif provider == "infor":
        from tools.ai_infor_genai import ask_infor_genai

        prompt = build_ai_prompt(data)   # reuse same prompt logic
        return ask_infor_genai(prompt)

    else:
        raise ValueError(f"Unsupported AI provider: {provider}")


def append_ai_to_markdown_file(
    markdown_path: str | Path,
    ai_markdown: str,
) -> Path:
    markdown_path = Path(markdown_path)

    if not markdown_path.exists() or not markdown_path.is_file():
        raise FileNotFoundError(f"Markdown file not found: {markdown_path}")

    existing = markdown_path.read_text(encoding="utf-8").rstrip()

    updated = f"{existing}\n\n---\n\n{ai_markdown.strip()}\n"
    markdown_path.write_text(updated, encoding="utf-8")

    return markdown_path