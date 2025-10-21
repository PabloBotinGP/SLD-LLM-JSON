"""Laravel / Lambda wrapper for Python extraction scripts

Purpose:
- Dynamically load a target Python script (by filename) and call its
    `run_extraction(prompt_id, file_id, image_ids, dry_run)` function. This
    wrapper is intended to be used both as a CLI during development and as the
    Lambda entrypoint in production.

Usage (CLI):
    python dev_scripts/laravel_lambda_wrapper.py --script dev_scripts/run_extraction.py [--prompt-id <id>] [--file-id <id>] [image_id1 image_id2] [--dry-run]

Usage (Lambda):
    - Deploy your package (or container) with this file and the target script.
    - Configure an OPENAI_API_KEY environment variable or fetch from Secrets
        Manager before calling this wrapper.
    - Invoke Lambda with a JSON payload (API Gateway or direct invoke):
            {"script": "dev_scripts/run_extraction.py", "prompt_id": "pmpt_...", "file_id": "file-...", "image_ids": ["file-a","file-b"], "dry_run": false}

Environment requirements:
- The wrapper imports the target module, so ensure dependencies are installed in
    the runtime (use a venv, conda env, or build a Lambda container image).
- `OPENAI_API_KEY` must be available in the environment before the actual
    API call is made (the OpenAI client is initialized lazily in the target).

Notes:
- The target script MUST expose `run_extraction(...)`. This wrapper no longer
    falls back to running the target as a subprocess.
- For Lambda, prefer storing outputs in S3 and returning a small response with
    the S3 path, rather than embedding large JSON in the Lambda response.
"""

import os
import json
import argparse
import importlib.util
from importlib.machinery import SourceFileLoader
from typing import Any, Dict


def _load_run_extraction_from(path: str):
    if not os.path.isabs(path):
        path = os.path.join(os.getcwd(), path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Target script not found: {path}")

    # Determine a module name based on the file basename. Using the real
    # filename as the module name (rather than a constant like "target_module")
    # lets other introspection utilities (typing.get_type_hints, pydantic,
    # langgraph) resolve references by module name.
    module_name = os.path.splitext(os.path.basename(path))[0]
    loader = SourceFileLoader(module_name, path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)

    # Register the module under the chosen name so that imports and
    # get_type_hints can find it by module name during runtime introspection.
    import sys
    sys.modules[module_name] = module

    # Execute the module in its namespace. Any import-time side effects will
    # run here; ensure the environment is prepared (OPENAI_API_KEY, venv, etc.).
    loader.exec_module(module)

    # If the module defines a `run_extraction` callable, return it. Callers can
    # then invoke that function directly with (prompt_id, file_id, image_ids,
    # dry_run...). If it's not present return None so the caller can fallback to
    # running the script as a subprocess.
    return getattr(module, "run_extraction", None)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        # Lambda events can come in different shapes. For API Gateway proxied
        # requests the JSON body is often in `event['body']` as a string. For
        # other invocations the event may *already* be a dict with the payload.
        payload = event.get("body")
        if isinstance(payload, str):
            # When body is a JSON string, parse it. If it's empty use an empty
            # dict to avoid later attribute errors.
            payload = json.loads(payload) if payload else {}
        elif payload is None:
            # If there's no `body` key assume the event itself contains the
            # payload (common when you invoke the lambda directly with a dict).
            payload = event

        # Extract expected fields from the payload
        script = payload.get("script")
        prompt_id = payload.get("prompt_id")
        file_id = payload.get("file_id")
        image_ids = payload.get("image_ids", [])
        dry_run = bool(payload.get("dry_run", False))

        # Validate required parameters early and return a 400-style response
        if not script:
            return {"statusCode": 400, "body": json.dumps({"error": "script is required"})}

        # Import and call run_extraction directly (in-process). The target
        # script MUST expose `run_extraction(prompt_id, file_id, image_ids, dry_run)`.
        run_extraction = _load_run_extraction_from(script)
        if not run_extraction:
            return {"statusCode": 400, "body": json.dumps({"error": "target script does not expose run_extraction; please export run_extraction(...)"})}

        res = run_extraction(prompt_id, file_id, image_ids=image_ids, dry_run=dry_run)
        return {"statusCode": 200, "body": json.dumps({"status": "ok", "result": str(res)})}

    except Exception as e:
        # Any unexpected exception is returned as a 500 payload. In production
        # you might log the traceback to CloudWatch and return a more generic
        # message instead of exposing internal errors.
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True, help="Path to target python script")
    ap.add_argument("--prompt-id", "--prompt_id", dest="prompt_id", required=False, help="Prompt ID to use (optional)")
    ap.add_argument("--file-id", "--file_id", dest="file_id", required=False, help="File ID for input_file (optional)")
    ap.add_argument("image_ids", nargs="*", help="Optional image file IDs")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    # Import and call run_extraction directly; fail early if the function is
    # missing because we no longer support subprocess fallbacks.
    run_extraction = _load_run_extraction_from(args.script)
    if not run_extraction:
        print("ERROR: target script does not expose run_extraction(prompt_id, file_id, image_ids, dry_run)")
        raise SystemExit(2)

    res = run_extraction(args.prompt_id, args.file_id, image_ids=args.image_ids or [], dry_run=args.dry_run)
    print(res)


if __name__ == "__main__":
    main()
