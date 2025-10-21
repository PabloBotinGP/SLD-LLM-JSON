# Dev Scripts Index

This index documents the Python scripts and useful files in this folder and shows example commands to run them from a terminal (zsh). Most scripts assume Python 3.11+ and may rely on packages listed in `requirements.txt`. Some scripts call the OpenAI APIs and require `OPENAI_API_KEY` to be set in the environment.

> Tip: run `python3 -m pip install -r requirements.txt` in a virtual environment before running scripts that need dependencies.

## Environment & general notes

- Activate the right environment before running these, it contains the API Key and other. 

`conda activate openai-env`

- For quick dry-run testing when a script supports it, pass `--dry-run` or use `dry_run=True` if calling the function programmatically.

- File paths below assume your current working directory is this folder:
  `/Users/pbotin/Documents/SolarAPP_Foundation/PT2/API/dev_scripts`

---

## Files and how to run them

### `run_extraction.py`
Purpose: The main extraction module (renamed from `31_run_extraction_wip.py`). Exposes `run_extraction(prompt_id, file_id, image_ids=None, dry_run=False)` and also has a CLI.

How to run (CLI):

```bash
# Dry-run with embedded defaults
python3 run_extraction_branch1_v0.py --dry-run

# Provide explicit prompt and file ids
python3 run_extraction_branch1_v0.py pmpt_XXXXXXXX file-YYYYYYYY file-img1 file-img2
```

How to import and call from Python:

```python
from run_extraction_branch1_v0 import run_extraction
res = run_extraction("pmpt_...", "file-...", image_ids=["file-img1","file-img2"], dry_run=True)
print(res)
```

Notes: When not in dry-run the script will call the OpenAI Responses API and return parsed Pydantic output (`ExtractionResult`). Ensure `OPENAI_API_KEY` is set.

---

### `run_extraction_wip_module.py`
Purpose: Alternative extraction module (renamed from `11_run_extraction_wip.py`). Also exposes `run_extraction()` for programmatic use and includes a CLI for compatibility.

How to run (CLI):

```bash
python3 run_extraction_wip_module.py --dry-run
python3 run_extraction_wip_module.py <prompt_id> <file_id> [image_id1 image_id2]
```

How to import:

```python
from run_extraction_wip_module import run_extraction
run_extraction("pmpt_...", "file-...", image_ids=[...], dry_run=True)
```

---

### `laravel_lambda_wrapper.py`
Purpose: Lambda/CLI wrapper previously provided in `30_Laravel_call.py`. Helps run extraction scripts either by importing them (in-process) or invoking them as subprocesses. Also implements `lambda_handler(event, context)` for AWS Lambda.

How to run (CLI):

```bash
# Use the wrapper to import and run a script in-process
python3 laravel_lambda_wrapper.py --script run_extraction_branch1_v0.py --prompt_id pmpt_... --file_id file-... --dry-run

# Run the target script via a separate python executable (venv)
python3 laravel_lambda_wrapper.py --python-exec /path/to/venv/bin/python --script run_extraction_branch1_v0.py --prompt_id pmpt_... --file_id file-...
```

How to call as a Lambda locally (example payload):

```python
from laravel_lambda_wrapper import lambda_handler
payload = {"script": "run_extraction_branch1_v0.py", "prompt_id": "pmpt_...", "file_id": "file-...", "image_ids": [], "dry_run": True}
resp = lambda_handler(payload, None)
print(resp)
```

---

### `langgraph_workflow_branch1_v0.py`
Purpose: The LangGraph workflow definition extracted from the original LangGraph script. Provides the `app` compiled workflow and the `call_llm` step wiring (used internally by the extraction modules).

How to use:

```python
from langgraph_workflow_branch1_v0 import app
# app.invoke expects the state/prompt/input structure used by LangGraph
```

Usually this module is used indirectly through the `run_extraction_*` modules above.

---

### `env_check_example.py`
Purpose: Small utility to interactively ensure required environment variables (like `OPENAI_API_KEY`) are present. Useful for local development.

Run it:

```bash
python3 env_check_example.py
```

---

### `upload_pdf_tool.py`
Purpose: Script for uploading PDFs (used by earlier workflows). The file likely contains a CLI to upload/prepare files for the extraction pipeline.

Run it (example):

```bash
python3 upload_pdf_tool.py path/to/file.pdf
```

---

### `quick_extract_example.py`
Purpose: Small convenience script demonstrating extraction with fixed defaults (good for quick tests).

Run it:

```bash
python3 quick_extract_example.py
```

---

### `parse_and_save_extraction.py`
Purpose: Utilities to parse extraction results and persist them (for example into `extracted_fields.json`).

Run/Use programmatically:

```python
from parse_and_save_extraction import parse_and_save
# call parse_and_save with the parsed data
```

---

### `elm_tree_extraction.py`
Purpose: Script that performs the ELM tree-based extraction (older approach). Kept for reference.

Run it:

```bash
python3 elm_tree_extraction.py --dry-run
```

---

### `lambda_handler.py`
Purpose: Example Lambda entrypoint. If you deploy to AWS Lambda you may set this as the handler.

Run locally (simple invocation):

```python
from lambda_handler import handler
resp = handler({"some": "event"}, None)
```

---

### `render.py`, `tree.py`, `utils.py`
Purpose: utility modules used by different scripts. Import them as needed.

Examples:

```python
from utils import some_helper
```

---

### `requirements.txt`
Purpose: Python package dependencies required by the scripts (install into a venv using pip).

Install:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

### `README_lambda.md`
Purpose: Notes about deploying or using the Lambda wrapper. Open and read for details specific to Lambda deployment.

---

### `extracted_fields.json`
Purpose: Example output file produced by the extraction scripts when they save parsed JSON results.

---

## Helpful commands

- Run a quick syntax check across all .py files in this folder:

```bash
python3 -m py_compile *.py
```

- Run a single module with dry-run (example):

```bash
OPENAI_API_KEY=test python3 run_extraction_branch1_v0.py --dry-run
```

- Import and call a function from a script in an interactive Python session:

```bash
python3 -c "from run_extraction_branch1_v0 import run_extraction; print(run_extraction('pmpt_x','file_y', dry_run=True))"
```

---

If you'd like, I can:

- generate a shorter printable summary, or
- add example prompt/file IDs used previously (safely redacted), or
- run a smoke import / python -m py_compile across the folder and report results now.

Tell me which of these you'd like next.