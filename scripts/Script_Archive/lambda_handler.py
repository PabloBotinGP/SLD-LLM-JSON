import os
import json
from typing import Any, Dict
import importlib.util
from importlib.machinery import SourceFileLoader


# Dynamically load the script since its filename starts with a digit and isn't a valid module name
def _load_run_extraction():
    script_path = os.path.join(os.path.dirname(__file__), "10_extract_LangGraph_wip.py")
    loader = SourceFileLoader("lg_extract", script_path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return getattr(module, "run_extraction")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler that expects a JSON payload with keys:
      - prompt_id: string (required)
      - file_id: string (required)
      - image_ids: optional list of up to 2 strings
      - dry_run: optional boolean

    Returns a JSON-serializable dict with the results from run_extraction.
    """
    try:
        body = event.get("body")
        if isinstance(body, str):
            payload = json.loads(body) if body else {}
        elif isinstance(body, dict):
            payload = body
        else:
            payload = event

        prompt_id = payload.get("prompt_id")
        file_id = payload.get("file_id")
        image_ids = payload.get("image_ids", [])
        dry_run = bool(payload.get("dry_run", False))

        if not prompt_id or not file_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "prompt_id and file_id are required"})
            }

        # Load the extraction function from the script and invoke it
        run_extraction = _load_run_extraction()
        result = run_extraction(prompt_id, file_id, image_ids=image_ids, dry_run=dry_run)

        # app.invoke returns objects that may not be JSON-serializable (e.g., Pydantic models).
        # Convert known fields to JSON-safe values. If there's `json_output`, return it.
        body = {
            "status": "ok",
            "result": {}
        }

        if isinstance(result, dict):
            # Try to include the json_output if present
            if result.get("json_output"):
                try:
                    body["result"] = json.loads(result["json_output"]) if isinstance(result["json_output"], str) else result["json_output"]
                except Exception:
                    body["result"] = {"raw": result.get("json_output")}
            else:
                # Copy simple keys
                for k in ["error", "note"]:
                    if result.get(k):
                        body["result"][k] = result.get(k)
        else:
            # If not a dict, return its string representation
            body["result"] = {"raw": str(result)}

        return {"statusCode": 200, "body": json.dumps(body)}

    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
