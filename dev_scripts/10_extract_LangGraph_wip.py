# Pull API key. Necessary? Comment for now. 

import os, getpass
def _set_env(var: str):
    if not os.environ.get(var):
        os.environ[var] = getpass.getpass(f"{var}: ")

# Set the OpenAI API key
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

# Define the extraction function using OpenAI Responses API
def call_llm(state):
    """
    Calls the OpenAI Responses API with the multimodal prompt for equipment extraction.
    Returns structured JSON parsed into Pydantic models.
    """
    try:
        # Use the same prompt ID from your working extraction script
        response = client.responses.parse(
            prompt={
                "id": "pmpt_68d3321897f481979180ca9152284cd00a7317fbe81972f1"
            },
            input=[{
                "role": "user",
                "content": [
                    {
                        "type": "input_image",
                        # "file_id": "file-F5VD9dv5sTTeFnZrn4AtHF", # Diagram 1
                        "file_id": "file-RYMeojcDFBtoDYNwne2XHe" # Diagram 2
                    },
                    {
                        "type": "input_image",
                        # "file_id": "file-2WwbeLWasaJtpQNqx88XYq" # Diagram 1
                        "file_id": "file-91iJcHy825krxoJeR1pRR6" # Diagram 2
                    },
                    {
                        "type": "input_file",
                        # "file_id": "file-Btvihbtetzycu5yNUnQ39d" # Diagram 1
                        "file_id": "file-2rs6FKsigL6J9LQyf8hDB4" # Diagram 2
                    }
                ],
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

# Visualize graph (optional - requires graphviz)
# try:
#     from IPython.display import Image, display
#     display(Image(app.get_graph().draw_mermaid_png()))
# except:
#     print("Visualization not available (requires IPython and graphviz)")

# Define the main function to handle command-line arguments
def main():
    ap = argparse.ArgumentParser(description="Process prompt ID and file IDs for LangGraph workflow.")
    ap.add_argument("id", help="Prompt ID to use in the API call")
    ap.add_argument("file_id", help="File ID for the input file")
    ap.add_argument("image_ids", nargs="*", help="Optional file IDs for input images (up to 2)")
    args = ap.parse_args()

    # Extract arguments
    prompt_id = args.id
    file_id = args.file_id
    image_ids = args.image_ids if args.image_ids else []

    # Debug print
    # print(f"Using prompt ID: {prompt_id}")
    # print(f"Using file ID for input file: {file_id}")
    # print(f"Using file IDs for input images: {image_ids}")
    print ("Sending file IDs...")

    # Define the state
    state = {"messages": []}

    # Prepare the input content
    content = [{"type": "input_file", "file_id": file_id}]
    if len(image_ids) > 0:
        content.append({"type": "input_image", "file_id": image_ids[0]})
    if len(image_ids) > 1:
        content.append({"type": "input_image", "file_id": image_ids[1]})

    # Call the LangGraph workflow
    response = app.invoke({
        "messages": state.get("messages", []),
        "prompt": {
            "id": prompt_id
        },
        "input": [
            {"role": "user", "content": content}
        ]
    })

    # Handle the results
    if response.get("error"):
        print(f"❌ Error: {response['error']}")
    elif "extraction_result" in response and response["extraction_result"]:
        print("✅ Equipment extraction completed!")
        print("\n📋 Extraction Results:")
        
        result = response["extraction_result"]
        
        # Print summary
        for equipment_type in ["Inverter", "Module", "Racking System"]:
            field_name = equipment_type.lower().replace(" ", "_")
            equipment_list = getattr(result, field_name, None)
            
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
        
        # Save to JSON file
        if "json_output" in response:
            with open("extracted_fields.json", "w", encoding="utf-8") as f:
                f.write(response["json_output"])
            print("\n💾 Saved to extracted_fields.json")
    else:
        print("❓ Unexpected response format")

if __name__ == "__main__":
    main()