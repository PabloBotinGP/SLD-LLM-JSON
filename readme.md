# Project README

## 📂 File Index
All scripts demonstrate API communication with the OpenAI GPT-5 language model:

# Script Index

- `dev_scripts/01_upload_pdf_final.py`  
  Upload a PDF via the Files API and run a quick “what’s in the PDF?” probe to confirm ingestion.

- `dev_scripts/02_extract_wip.py`  
  WIP extractor for Inverter/Module/Racking; prompts the model and returns JSON-as-text  
  *(may be slow / occasional NoneType issues).*

- `dev_scripts/03_extract_parse_wip.py`  
  Parses the model’s JSON text into structured Python (e.g., Pydantic/dict) and saves to disk;  
  accuracy depends on prompt.

- `dev_scripts/10_extract_LangGraph_wip.py`  
  LangGraph-based, multi-step extraction pipeline (retry logic, tool calls, selection precedence).

- `dev_scripts/20_extract_elm_tree_final.py`  
  Final ELM decision-tree orchestrator enforcing selection rules and deterministic single-item per type.

- `dev_scripts/extracted_fields.json`  
  Collected/example structured outputs from runs (for regression checks and prompt tuning).


## 📦 Prerequisites
- Python 3.11+
- Conda (recommended for environment management)
- An OpenAI API Key (https://platform.openai.com/api-keys)

---

## ⚙️ Environment Setup

### Install dependencies
Create and activate a fresh Conda environment:

    conda create -n openai-env python=3.11
    conda activate openai-env

Then install the required libraries:

    pip install openai pydantic pyyaml python-dotenv

(You can also use `requirements.txt` or `pyproject.toml` if provided.)

---

## 🔑 OpenAI API Key Setup

This project requires access to the OpenAI API. Each user must provide their own **personal API key**.

1. Go to the [OpenAI Dashboard → API Keys](https://platform.openai.com/account/api-keys).  
2. Create a new key (or copy an existing one). It will look like:  
   sk-********************************  
3. Store this key as an environment variable on your machine. **Do not share your key with anyone and never upload it to GitHub.**

### macOS / Linux (bash / zsh)
export OPENAI_API_KEY=sk-your-key-here  
To make this permanent across terminal sessions, add the line above to your `~/.zshrc` or `~/.bashrc`.

### Windows (PowerShell)
setx OPENAI_API_KEY "sk-your-key-here"  
Then restart your terminal.

### Verify
echo $OPENAI_API_KEY      # macOS/Linux  
echo $Env:OPENAI_API_KEY  # Windows PowerShell  

If you see your key printed, it’s set correctly ✅.

---

⚠️ **Important:**  
- Never hardcode your API key in scripts.  
- Never commit your API key to GitHub.  
- Each user must manage their own key locally.


## ▶️ Running the Scripts

Run on terminal:

    python3 script_name.py

---

