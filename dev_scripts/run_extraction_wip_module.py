"""Renamed from 11_run_extraction_wip.py — a module exposing run_extraction().
"""

# Pull API key. Necessary? Comment for now. 

import os, getpass
from typing import Optional, List, Dict, Any

def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

# Ensure OPENAI_API_KEY is set when run interactively; in Lambda the env var
# should already be present.
_set_env("OPENAI_API_KEY")

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
client = OpenAI()

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

        response = client.responses.parse(
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
def run_extraction(prompt_id: str, file_id: str, image_ids: Optional[List[str]] = None, dry_run: bool = False) -> Dict[str, Any]:
    """
    Run the LangGraph extraction using provided prompt_id and file ids.

    Returns a dict with keys similar to the original script's `response`:
    - "extraction_result": parsed Pydantic object or None
    - "json_output": JSON string of the extraction
    - "error": error details if any
    """
    if dry_run:
        return {"status": "dry-run", "prompt_id": prompt_id, "file_id": file_id, "image_ids": image_ids}

    # For now use embedded prompt and content regardless of the function args.
    # This will call the OpenAI Responses API directly and return the parsed
    # pydantic result. Ensure OPENAI_API_KEY is set in the environment.
    if dry_run:
        return {"status": "dry-run", "prompt_id": prompt_id, "file_id": file_id, "image_ids": image_ids}

    try:
        response = client.responses.parse(
            prompt={"id": HARDCODE_PROMPT_ID},
            input=[{"role": "user", "content": HARDCODE_CONTENT}],
            text_format=ExtractionResult,
        )

        result: ExtractionResult = response.output_parsed
        json_output = result.model_dump_json(indent=2, by_alias=True, exclude_none=False)
        return {"messages": [], "extraction_result": result, "json_output": json_output}
    except Exception as e:
        import traceback
        error_details = f"Extraction failed: {str(e)}\n{traceback.format_exc()}"
        print(f"DEBUG Error: {error_details}")
        return {"messages": [], "extraction_result": None, "json_output": None, "error": error_details}


# Keep CLI entrypoint for backward compatibility
def main():
    ap = argparse.ArgumentParser(description="Process prompt ID and file IDs for LangGraph workflow.")
    ap.add_argument("id", help="Prompt ID to use in the API call")
    ap.add_argument("file_id", help="File ID for the input file")
    ap.add_argument("image_ids", nargs="*", help="Optional file IDs for input images (up to 2)")
    args = ap.parse_args()

    prompt_id = args.id
    file_id = args.file_id
    image_ids = args.image_ids if args.image_ids else []

    print ("Sending file IDs...")
    result = run_extraction(prompt_id, file_id, image_ids=image_ids, dry_run=False)

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
