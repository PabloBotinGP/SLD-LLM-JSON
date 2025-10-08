# Project README

## 📂 File Index
All scripts demonstrate API communication with the OpenAI GPT-5 language model:

## dev_scripts/

00_env_check_final.py – Minimal example to verify environment setup and API connectivity.

01_pdf_upload_final.py – Upload PDF via File API and run a simple “what’s in the PDF?” prompt.

02_extract_equipment_wip.py – Prompt for manufacturer and model of each equipment; outputs JSON as text. (Currently slow, raises NoneType error.)

03_validate_equipment_pydantic_wip.py – Parses JSON text into a Pydantic object and saves as structured JSON. Works, but output accuracy needs prompt refinement. (Also slow.)

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

