# Dev Scripts Index

This index documents the Python scripts and useful files in this folder and shows example commands to run them from a terminal (zsh). Most scripts assume Python 3.11+ and may rely on packages listed in `requirements.txt`. Some scripts call the OpenAI APIs and require `OPENAI_API_KEY` to be set in the environment.


## Environment & general notes

- Activate the right environment before running these, it contains the API Key and other. 

`conda activate openai-env`

- For quick dry-run testing when a script supports it, pass `--dry-run` or use `dry_run=True` if calling the function programmatically.

- File paths below assume your current working directory is this folder:
  `/Users/pbotin/Documents/SolarAPP_Foundation/PT2/API/dev_scripts`

---

# Dev Scripts Index

This file documents the active development scripts in `dev_scripts/`, shows simple run examples, and lists older/experimental scripts under the Script Archive section.

Quick environment notes

- Activate the Python environment that contains the project's dependencies and the `OPENAI_API_KEY` before running the scripts:

```bash
conda activate openai-env
```

- Working directory for the examples below is the `dev_scripts` folder:

  /Users/pbotin/Documents/SolarAPP_Foundation/PT2/API/dev_scripts

---

## Active scripts (in this folder)

### 1. `lambda_call.py`
Purpose: Primary wrapper intended to be called by Laravel (via AWS Lambda or directly) to run extraction jobs. It dynamically loads a target extraction script (for example `run_extraction.py`) and calls its `run_extraction(...)` entrypoint. Also exposes `lambda_handler(event, context)` for direct Lambda use.

How to run locally (dry-run example):

```bash
# run the wrapper and import+call run_extraction in-process
python lambda_call.py --script run_extraction.py --dry-run

# provide explicit prompt and file ids (requires OPENAI_API_KEY in env when not dry-run)
python lambda_call.py --script run_extraction.py --prompt-id pmpt_... --file-id file-...
```

How to call from Python (example payload for Lambda-style invocation):

```python
from laravel import lambda_handler
payload = {
    "script": "run_extraction.py",
    "prompt_id": "pmpt_...",
    "file_id": "file-...",
    "image_ids": [],
    "dry_run": True
}
resp = lambda_handler(payload, None)
print(resp)
```

Notes:
- Use `--dry-run` for a fast local check that imports succeed and the wrapper wiring is correct.
- For Lambda deployments, ensure `OPENAI_API_KEY` is available.

---

### 2. `run_extraction.py`
Purpose: Core extraction logic and programmatic entrypoint. Exposes a function `run_extraction(prompt_id, file_id, image_ids=None, dry_run=False)` and a CLI. When run (non-dry-run) it calls the OpenAI API and writes output JSON to `dev_scripts/extracted_fields.json` and a UTC timestamped copy.

How to run (examples):

```bash
# dry-run using embedded defaults
python run_extraction.py --dry-run

# explicit run (requires OPENAI_API_KEY in env)
python run_extraction.py --prompt-id pmpt_... --file-id file-...
```

How to call from Python:

```python
from run_extraction import run_extraction
res = run_extraction("pmpt_...", "file-...", image_ids=["file-img1"], dry_run=True)
print(res)
```

---

### 3. `render.py` 
Rendering functionality used for producing images from PDFs.

---

## Script Archive (in Script_Archive folder)
The following scripts were experimental or earlier variants; they have been moved to `Script_Archive/` at the repository root. Each entry below is a short note about intent so you can find them quickly.

- `run_extraction_wip_module.py` — An earlier work-in-progress extraction module. Kept for reference; superseded by `run_extraction.py`.

- `laravel_lambda_wrapper.py` — Previous (longer) wrapper implementation with subprocess fallbacks. Kept for reference; the active wrapper is `laravel.py`.

- `langgraph_workflow_branch1_v0.py` — LangGraph workflow export used by the extraction code. Useful if you need to inspect or recompile the workflow.

