# SolarAPP LLM JSON Extraction API

Extracts structured equipment information (inverters, modules, racking systems) from solar installation documentation using OpenAI's GPT-4 vision API with LangGraph orchestration.

## Table of Contents
- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [API Configuration](#api-configuration)
- [Running Scripts](#running-scripts)
- [Fuzzy Matching Utilities](#fuzzy-matching-utilities)

---

## Environment Setup

### Prerequisites
- **macOS/Linux** with Conda installed
- **Python 3.12**
- OpenAI API Key (https://platform.openai.com/api-keys)

### Option 1: Using environment.yml (Recommended)
This method creates an exact replica of the development environment:

```bash
conda env create -f environment.yml
conda activate openai-env
```

### Option 2: Using requirements.txt
If you already have a Python 3.12+ environment:

```bash
conda activate openai-env  # or your env name
pip install -r requirements.txt
```

### Option 3: Manual Setup
```bash
conda create -n openai-env python=3.12
conda activate openai-env
pip install -r requirements.txt
```

---

## 🔑 OpenAI API Key Setup

Each user must provide their own **personal API key**. Never commit keys to GitHub.

### macOS / Linux (bash / zsh)
Add to `~/.zshrc` or `~/.bashrc`:

```bash
export OPENAI_API_KEY=sk-your-key-here
```

Then reload:
```bash
source ~/.zshrc  # or ~/.bashrc
```

### Windows (PowerShell)
```powershell
setx OPENAI_API_KEY "sk-your-key-here"
```
Then restart your terminal.

### Verify Setup
```bash
echo $OPENAI_API_KEY      # macOS/Linux
echo $Env:OPENAI_API_KEY  # Windows
```

---

## 📁 Project Structure

```
API/
├── readme.md                          # This file
├── requirements.txt                   # Python dependencies (pinned versions)
├── environment.yml                    # Conda environment definition
├── .gitignore                         # Git ignore rules
│
├── output files/                      # Extraction results
│   └── extracted_fields-*.json        # Timestamped results
│
├── prompts/                           # OpenAI prompt templates
│   └── prompt1.py                     # Prompt helper script
│
├── scripts/                           # Main execution scripts
│
└── src/                               # Shared libraries
```

---

## Running Scripts Examples

### Main Extraction Script
```bash
cd scripts/
python run_extraction.py
```

Optional flags:
- `--prompt-id <ID>` - Custom prompt ID
- `--file-id <ID>` - Custom file ID for extraction
- `--dry-run` - Test without API calls

### Upload PDF
```bash
python upload_pdf.py <pdf_path>
```

### Fuzzy Matching (PHP)
```bash
php fuzzymatch_Jaro-Winkler.php      # Jaro-Winkler algorithm
php fuzzymatch_combined.php           # Multi-algorithm composite
```

---

## Fuzzy Matching

### Architecture
All fuzzy matching algorithms are centralized in `src/fuzzymatch.php`:

**Matcher Classes:**
- `JaroWinklerMatcher` - Simple Jaro-Winkler matching
- `CompositeMatcher` - Weighted multi-algorithm scoring

**Display Utilities:**
- `FuzzyMatchFunctions::displaySimpleResults()` - Format Jaro-Winkler results
- `FuzzyMatchFunctions::displayCompositeResults()` - Format composite results

### Usage Example
```php

// Simple Jaro-Winkler matching
$matcher = new JaroWinklerMatcher();
$results = $matcher->findMatches('EcoFlow', $companies, 5, 0.6);
FuzzyMatchFunctions::displaySimpleResults('EcoFlow', $results);

// Composite matching
$composite = new CompositeMatcher();
$results = $composite->fuzzyMatch('EcoFlow', $companies, 5, 0.3);
FuzzyMatchFunctions::displayCompositeResults('EcoFlow', $results);
?>
```

---

## 📝 Notes

- All extraction results are saved to `output files/` with timestamps
- API calls are logged for debugging
- Never hardcode API keys in scripts
- Each user manages their own API key locally
- Keep `environment.yml` and `requirements.txt` in sync

---

## Resources

- [OpenAI API Docs](https://platform.openai.com/docs)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Conda Documentation](https://docs.conda.io/)

---

**Last Updated:** November 21, 2025  
