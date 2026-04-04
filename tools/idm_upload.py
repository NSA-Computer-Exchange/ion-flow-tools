from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
import json
import os
import base64
import requests
from dotenv import load_dotenv
from security.iontoken import get_token

load_dotenv()


class IDMUploadError(Exception):
    pass


def file_to_base64(file_path: str | Path) -> str:
    file_path = Path(file_path)

    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def build_idm_metadata(
    attr_name: str,
    attr_type: str = "Dataflow",
    res_filename: str = "document.pdf",
    res_base64: str = "",
    acl: str = "Public",
    entity_name: str = "IONFlowDocumentation",
) -> Dict[str, Any]:
    return {
        "item": {
            "attrs": {
                "attr": [
                    {"name": "Name", "value": attr_name},
                    {"name": "Type", "value": attr_type},
                ]
            },
            "resrs": {
                "res": [
                    {
                        "filename": res_filename,
                        "base64": res_base64,
                    }
                ]
            },
            "acl": {
                "name": acl,
            },
            "entityName": entity_name,
            "pid": "",
        }
    }


def upload_file_to_idm(
    file_path: str | Path,
    attr_name: str,
    attr_type: str = "Dataflow",
    acl: str = "Public",
    entity_name: str = "IONFlowDocumentation",
) -> Dict[str, Any]:
    file_path = Path(file_path)

    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"Resource file not found: {file_path}")

    idm_base_url = os.environ.get("ION_TENANT_URL")
    if not idm_base_url:
        raise IDMUploadError("ION_TENANT_URL is not set")

    access_token = get_token()
    url = f"{idm_base_url.rstrip('/')}/IDM/api/items"

    payload = build_idm_metadata(
        attr_name=attr_name,
        attr_type=attr_type,
        res_filename=file_path.name,
        res_base64=file_to_base64(file_path),
        acl=acl,
        entity_name=entity_name,
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "accept": "application/json",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url=url,
        headers=headers,
        data=json.dumps(payload),
        timeout=60,
    )

    try:
        response_json = response.json()
    except Exception:
        response_json = {"raw_text": response.text}

    if not response.ok:
        raise IDMUploadError(
            f"IDM upload failed. Status={response.status_code}. Response={response_json}"
        )

    return {
        "success": True,
        "status_code": response.status_code,
        "response_json": response_json,
    }