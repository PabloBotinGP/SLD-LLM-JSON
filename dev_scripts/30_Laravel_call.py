"""
Generic Laravel/Lambda Python-caller wrapper.

Usage (CLI):
    python 30_Laravel_call.py --script path/to/target.py --prompt_id PMPT --file_id file-... [image_ids ...] [--dry-run]

Lambda payload:
  {
    "script": "dev_scripts/10_extract_LangGraph_wip.py",
    "prompt_id": "pmpt_...",
    "file_id": "file-...",
    "image_ids": ["file-a","file-b"],
    "dry_run": true
  }

The wrapper dynamically loads the target script (supports filenames starting with digits) and calls its `run_extraction` function.
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

    loader = SourceFileLoader("target_module", path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)

    # Load module (assumes environment is prepared, e.g. venv activated and OPENAI_API_KEY set)
    loader.exec_module(module)

    # Return the run_extraction function if present, otherwise return None
    return getattr(module, "run_extraction", None)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        payload = event.get("body")
        if isinstance(payload, str):
            payload = json.loads(payload) if payload else {}
        elif payload is None:
            payload = event

        script = payload.get("script")
        prompt_id = payload.get("prompt_id")
        file_id = payload.get("file_id")
        image_ids = payload.get("image_ids", [])
        dry_run = bool(payload.get("dry_run", False))

        if not script or not prompt_id or not file_id:
            return {"statusCode": 400, "body": json.dumps({"error": "script, prompt_id and file_id are required"})}

        run_extraction = _load_run_extraction_from(script)
        if run_extraction:
            res = run_extraction(prompt_id, file_id, image_ids=image_ids, dry_run=dry_run)
            return {"statusCode": 200, "body": json.dumps({"status": "ok", "result": str(res)})}

        # Fallback: run the target script as a subprocess using the current Python
        import subprocess, sys
        cmd = [sys.executable, script, prompt_id, file_id] + (image_ids or [])
        if dry_run:
            cmd.append("--dry-run")
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            return {"statusCode": 500, "body": json.dumps({"error": proc.stderr})}
        return {"statusCode": 200, "body": json.dumps({"status": "ok", "output": proc.stdout})}

    except Exception as e:
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
        # Run the target script as a subprocess with the provided python executable.
        cmd = [args.python_exec, args.script, args.prompt_id, args.file_id] + (args.image_ids or [])
        if args.pass_flags:
            cmd += args.pass_flags
        subprocess.check_call(cmd)
        return

    # Try importing run_extraction from the target script
    run_extraction = _load_run_extraction_from(args.script)
    if run_extraction:
        res = run_extraction(args.prompt_id, args.file_id, image_ids=args.image_ids or [], dry_run=args.dry_run)
        print(res)
        return

    # Fallback: run using current Python interpreter as subprocess
    cmd = [sys.executable, args.script, args.prompt_id, args.file_id] + (args.image_ids or [])
    if args.pass_flags:
        cmd += args.pass_flags
    subprocess.check_call(cmd)


if __name__ == "__main__":
    main()
