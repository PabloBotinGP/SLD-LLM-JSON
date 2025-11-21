"""
Run extraction module

This module exposes a programmatic function:
    run_extraction(prompt_id: Optional[str] = None,
                                 file_id: Optional[str] = None,
                                 image_ids: Optional[List[str]] = None,
                                 dry_run: bool = False)

Purpose:
- Call the OpenAI Responses API (via LangGraph) to extract structured
    equipment information from provided file/image IDs.
- On success the JSON result is saved next to this module as
    `dev_scripts/extracted_fields.json` and also as a timestamped file
    `dev_scripts/extracted_fields-<timestamp>.json`.

How to run (CLI):
- With explicit IDs (requires OPENAI_API_KEY in environment or active venv):
        python dev_scripts/run_extraction.py --prompt-id <PROMPT_ID> --file-id <FILE_ID> [image_id1 image_id2]
- Using embedded defaults (no IDs):
        python dev_scripts/run_extraction.py --dry-run

Recommended: invoke this from the wrapper which handles Lambda-style payloads:
        python dev_scripts/laravel_lambda_wrapper.py --script dev_scripts/run_extraction.py [--prompt-id ...] [--file-id ...] [--dry-run]

Environment:
- Ensure `OPENAI_API_KEY` is set in the environment or provided via Secrets Manager
    when running in AWS Lambda. This module initializes the OpenAI client lazily,
    so importing the module does not require the key until an API call is made.

Notes:
- For production/AWS Lambda deploy the package or a container image with all
    dependencies installed. Consider storing outputs in S3 for persistence.
"""

import os, getpass
from datetime import datetime
from typing import Optional, List, Dict, Any    
from openai import OpenAI
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
import argparse

# Define the Pydantic models for structured output
class EquipmentEntry(BaseModel):
    found: bool
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    evidence_note: Optional[str] = None

class ExtractionResult(BaseModel):
    inverter: Optional[List[EquipmentEntry]] = Field(default=None, alias="Inverter", max_length=1)
    module: Optional[List[EquipmentEntry]] = Field(default=None, alias="Module", max_length=1)
    racking_system: Optional[List[EquipmentEntry]] = Field(default=None, alias="Racking System", max_length=1)

    model_config = ConfigDict(populate_by_name=True)

# Initialize OpenAI client
# Initialize OpenAI client lazily to avoid import-time requirement for OPENAI_API_KEY
client = None

def get_client():
    """Return a cached OpenAI client, creating it if necessary.

    Raises a RuntimeError if OPENAI_API_KEY is not set.
    """
    global client
    if client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not set in environment. Activate your venv or set the env var before calling the API.")
        # create the OpenAI client
        client = OpenAI()
    return client

# Embedded prompt and input IDs (from original 10_extract_LangGraph_wip.py)
HARDCODE_PROMPT_ID = "pmpt_68d3321897f481979180ca9152284cd00a7317fbe81972f1"
HARDCODE_CONTENT = [
    {"type": "input_image", "file_id": "file-RYMeojcDFBtoDYNwne2XHe"},
    {"type": "input_image", "file_id": "file-91iJcHy825krxoJeR1pRR6"},
    {"type": "input_file", "file_id": "file-2rs6FKsigL6J9LQyf8hDB4"},
]

# Define the extraction function using OpenAI Responses API
def call_llm(state, prompt_id: str, file_id: str, image_ids: Optional[List[str]] = None):
    """
    Calls the OpenAI Responses API with the multimodal prompt for equipment extraction.
    Returns structured JSON parsed into Pydantic models.
    """
    try:
        # Build the content list based on provided file and image ids
        content = [{"type": "input_file", "file_id": file_id}]
        if image_ids:
            for img in image_ids[:2]:
                content.append({"type": "input_image", "file_id": img})

        response = get_client().responses.parse(
            prompt={
                "id": prompt_id
            },
            input=[{
                "role": "user",
                "content": content,
            }],
            # Enforce structured JSON output using Pydantic model
            text_format=ExtractionResult
        )
        
        # Get the parsed Pydantic object
        result: ExtractionResult = response.output_parsed
        
        # Convert to JSON for storage in state
        json_output = result.model_dump_json(indent=2, by_alias=True, exclude_none=False)
        
        return {
            "messages": state.get("messages", []),
            "extraction_result": result,
            "json_output": json_output
        }
        
    except Exception as e:
        import traceback
        error_details = f"Extraction failed: {str(e)}\n{traceback.format_exc()}"
        print(f"DEBUG Error: {error_details}")  # Add debug print
        return {
            "messages": state.get("messages", []),
            "extraction_result": None,
            "json_output": None,
            "error": error_details
        }

# Define state
class State(TypedDict):
    messages: list
    extraction_result: Optional[ExtractionResult]
    json_output: Optional[str]
    error: Optional[str]

# Create a new StateGraph
workflow = StateGraph(State)
# Add the nodes
workflow.add_node("call_llm", call_llm)

# Add the Edges
workflow.add_edge(START, "call_llm")
workflow.add_edge("call_llm", END)

#Compile the workflow
app = workflow.compile()


# Public run_extraction function so external callers (like wrappers) can
# import and invoke the logic directly.
def run_extraction(prompt_id: Optional[str] = None, file_id: Optional[str] = None, image_ids: Optional[List[str]] = None, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run the LangGraph extraction using provided prompt_id and file ids.

    Returns a dict with keys similar to the original script's `response`:
    - "extraction_result": parsed Pydantic object or None
    - "json_output": JSON string of the extraction
    - "error": error details if any
    """
    # Fall back to embedded prompt/content if caller didn't provide them
    used_prompt = prompt_id or HARDCODE_PROMPT_ID
    used_file_id = file_id or (HARDCODE_CONTENT[-1].get("file_id") if HARDCODE_CONTENT else None)
    if dry_run:
        return {"status": "dry-run", "prompt_id": used_prompt, "file_id": used_file_id, "image_ids": image_ids}

    # For now use embedded prompt and content regardless of the function args.
    # This will call the OpenAI Responses API directly and return the parsed
    # pydantic result. Ensure OPENAI_API_KEY is set in the environment.
    if dry_run:
        return {"status": "dry-run", "prompt_id": prompt_id, "file_id": file_id, "image_ids": image_ids}

    try:
        # If caller didn't pass prompt/file, use the embedded defaults
        if not prompt_id or not file_id:
            response = get_client().responses.parse(
                prompt={"id": HARDCODE_PROMPT_ID},
                input=[{"role": "user", "content": HARDCODE_CONTENT}],
                text_format=ExtractionResult,
            )
        else:
            # Build content using provided IDs
            content = [{"type": "input_file", "file_id": used_file_id}]
            if image_ids:
                for img in image_ids[:2]:
                    if img and img != "":
                        content.append({"type": "input_image", "file_id": img})

            response = get_client().responses.parse(
                prompt={"id": used_prompt},
                input=[{"role": "user", "content": content}],
                text_format=ExtractionResult,
            )

        result: ExtractionResult = response.output_parsed
        json_output = result.model_dump_json(indent=2, by_alias=True, exclude_none=False)
        # Attempt to save JSON to timestamped file next to this module for easier retrieval
        try:
            ts = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
            base_dir = os.path.dirname(__file__)
            timestamped_name = f"extracted_fields-{ts}.json"
            out_path_ts = os.path.join(base_dir, timestamped_name)
            with open(out_path_ts, "w", encoding="utf-8") as f:
                f.write(json_output)

            # Also update a stable/latest filename for quick access
            out_path = os.path.join(base_dir, "extracted_fields.json")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(json_output)
        except Exception as e:
            # If saving fails, include a debug print but don't break the response
            print(f"Warning: failed to write extracted_fields files: {e}")
        return {"messages": [], "extraction_result": result, "json_output": json_output}
    except Exception as e:
        import traceback
        error_details = f"Extraction failed: {str(e)}\n{traceback.format_exc()}"
        print(f"DEBUG Error: {error_details}")
        return {"messages": [], "extraction_result": None, "json_output": None, "error": error_details}


# Keep CLI entrypoint for backward compatibility
def main():
    ap = argparse.ArgumentParser(description="Process prompt ID and file IDs for LangGraph workflow.")
    ap.add_argument("--prompt-id", dest="prompt_id", help="Prompt ID to use in the API call")
    ap.add_argument("--file-id", dest="file_id", help="File ID for the input file")
    ap.add_argument("image_ids", nargs="*", help="Optional file IDs for input images (up to 2)")
    ap.add_argument("--dry-run", action="store_true", help="Do not call OpenAI API; return dry-run result")
    args = ap.parse_args()

    prompt_id = args.prompt_id
    file_id = args.file_id
    image_ids = args.image_ids if args.image_ids else []

    print ("Sending file IDs...")
    result = run_extraction(prompt_id, file_id, image_ids=image_ids, dry_run=args.dry_run)

    if result.get("error"):
        print(f"❌ Error: {result['error']}")
    elif "extraction_result" in result and result["extraction_result"]:
        print("✅ Equipment extraction completed!")
        print("\n📋 Extraction Results:")
        res = result["extraction_result"]
        for equipment_type in ["Inverter", "Module", "Racking System"]:
            field_name = equipment_type.lower().replace(" ", "_")
            equipment_list = getattr(res, field_name, None)
            if equipment_list and len(equipment_list) > 0:
                equipment = equipment_list[0]
                print(f"\n🔧 {equipment_type}:")
                print(f"   Found: {equipment.found}")
                if equipment.manufacturer:
                    print(f"   Manufacturer: {equipment.manufacturer}")
                if equipment.model:
                    print(f"   Model: {equipment.model}")
                if equipment.evidence_note:
                    print(f"   Note: {equipment.evidence_note}")
        if "json_output" in result and result["json_output"]:
            with open("extracted_fields.json", "w", encoding="utf-8") as f:
                f.write(result["json_output"])
            print("\n💾 Saved to extracted_fields.json")
    else:
        print("❓ Unexpected response format")


if __name__ == "__main__":
    main()
