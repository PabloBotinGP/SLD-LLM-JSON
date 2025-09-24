# Project README

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

## 📂 File Index
All scripts demonstrate API communication with the OpenAI GPT-5 language model:

dev_scripts/
- v0.py – Minimal example to verify environment setup and API connectivity.

- v1.py – Upload PDF file via File API. Basic prompt (what's in the PDF?).

- v2_WIP.py – Still a single prompt but more elaborated: Asks for the manufacturer and model of each equipment. Provides a json as an output. But in the form of text. Takes a while to run. 
    Traceback (most recent call last):
        File "/Users/pbotin/Documents/SolarAPP_Foundation/PT2/Test 2/v2.py", line 18, in <module>
    TypeError: 'NoneType' object is not subscriptable

- v3_WIP.py - Parse the json text into a pydantic object and save as a JSON. It works, but the provided info is not accurate, so it needs prompt refinement. Takes a while to run. 