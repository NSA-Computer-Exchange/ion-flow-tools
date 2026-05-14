from __future__ import annotations

import os
import requests
from security.iontoken import get_token

from dotenv import load_dotenv

load_dotenv()

def build_ai_prompt(data: dict) -> str:
    import json

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
{json.dumps(data, indent=2)}
""".strip()


def ask_infor_genai(prompt: str) -> str:
    """
    Call Infor GenAI prompt endpoint and return generated text.
    """

    base_url = os.getenv("INFOR_GENAI_BASE_URL", "").strip()
    logical_id = os.getenv("INFOR_GENAI_LOGICAL_ID", "infor.genai.genai").strip()
    #token = os.getenv("INFOR_GENAI_TOKEN", "").strip()
    token = get_token()

    if not base_url:
        raise ValueError("INFOR_GENAI_BASE_URL not set")
    if not token:
        raise ValueError("INFOR_GENAI_TOKEN not set")

    url = f"{base_url.rstrip('/')}/GENAI/chatsvc/api/v1/prompt"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "accept": "application/json",
        "x-infor-logicalidprefix": logical_id,
    }

    model = os.getenv("INFOR_GENAI_MODEL", "CLAUDE")
    version = os.getenv("INFOR_GENAI_VERSION", "claude-sonnet-4-6")

    payload = {
        "model": model,
        "version": version,
        "prompt": prompt,
        "config": {
            "temperature": 0.3,
            "max_tokens": int(os.getenv("INFOR_GENAI_MAX_TOKENS", "1500")),
        },
    }

    response = requests.post(url, headers=headers, json=payload, timeout=120)
    response.raise_for_status()

    data = response.json()

    text = (
        data.get("content")
        or data.get("response")
        or data.get("output")
        or data.get("text")
        or data.get("choices", [{}])[0].get("text")
        or ""
    )

    if not text:
        raise ValueError(f"Infor GenAI returned no usable text: {data}")

    return text.strip()
