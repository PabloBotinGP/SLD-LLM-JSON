"""Wrapper to run extraction scripts from Lambda or CLI.

Renamed from `30_Laravel_call.py` to a module-name-friendly filename so it can be
imported normally (e.g. `import laravel_lambda_wrapper`).
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

    # Use SourceFileLoader so we can import a file whose filename might not be
    # a valid Python identifier (for example it might start with digits).
    loader = SourceFileLoader("target_module", path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)

    # Execute the module in its own namespace. This will run top-level code in
    # the target script, so ensure the environment is ready (dependencies,
    # environment variables, etc.). If the target file raises at import time,
    # the exception will bubble up to the caller.
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
        if not script or not prompt_id or not file_id:
            return {"statusCode": 400, "body": json.dumps({"error": "script, prompt_id and file_id are required"})}

        # Try to import and call run_extraction directly (in-process)
        run_extraction = _load_run_extraction_from(script)
        if run_extraction:
            # Most target scripts define run_extraction(prompt_id, file_id,
            # image_ids=..., dry_run=...). Call it and return the result. We
            # stringify the result to keep the Lambda response JSON-friendly.
            res = run_extraction(prompt_id, file_id, image_ids=image_ids, dry_run=dry_run)
            return {"statusCode": 200, "body": json.dumps({"status": "ok", "result": str(res)})}

        # Fallback: run the target script as a subprocess using the current Python
        # interpreter. This path is used when the target script expects argv style
        # invocation rather than exposing a python function.
        import subprocess, sys
        cmd = [sys.executable, script, prompt_id, file_id] + (image_ids or [])
        if dry_run:
            # Many scripts support a `--dry-run` flag; forward it to the script.
            cmd.append("--dry-run")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            # Return a 500-like payload with stderr for debugging.
            return {"statusCode": 500, "body": json.dumps({"error": proc.stderr})}
        # Successful run: return stdout as the output field.
        return {"statusCode": 200, "body": json.dumps({"status": "ok", "output": proc.stdout})}

    except Exception as e:
        # Any unexpected exception is returned as a 500 payload. In production
        # you might log the traceback to CloudWatch and return a more generic
        # message instead of exposing internal errors.
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True, help="Path to target python script")
    ap.add_argument("--prompt_id", required=True)
    ap.add_argument("--file_id", required=True)
    ap.add_argument("image_ids", nargs="*", help="Optional image file IDs")
    ap.add_argument("--python-exec", help="Optional path to python executable (use venv python) to run the target script in a subprocess). If provided, the wrapper will call the target script as a CLI instead of importing it.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--pass-flags", nargs="*", help="Optional flags to forward to the target script when running it as subprocess (e.g. --dry-run)")
    args = ap.parse_args()

    import sys, subprocess

    if args.python_exec:
        # If a specific Python executable is provided (for example the venv's
        # python), run the target script as a subprocess using that interpreter
        # and forward any image ids and flags. This keeps the wrapper from
        # importing the module into the current process and guarantees the
        # target runs in the intended environment.
        cmd = [args.python_exec, args.script, args.prompt_id, args.file_id] + (args.image_ids or [])
        if args.pass_flags:
            cmd += args.pass_flags
        subprocess.check_call(cmd)
        return

    # Prefer importing and calling run_extraction directly when possible. This
    # is convenient during development because it avoids a subprocess spawn and
    # shares the current environment.
    run_extraction = _load_run_extraction_from(args.script)
    if run_extraction:
        res = run_extraction(args.prompt_id, args.file_id, image_ids=args.image_ids or [], dry_run=args.dry_run)
        # Print the result to stdout so CLI users can capture it.
        print(res)
        return

    # Final fallback: run the target script using the same Python interpreter
    # as the wrapper (sys.executable) and forward any flags.
    cmd = [sys.executable, args.script, args.prompt_id, args.file_id] + (args.image_ids or [])
    if args.pass_flags:
        cmd += args.pass_flags
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
