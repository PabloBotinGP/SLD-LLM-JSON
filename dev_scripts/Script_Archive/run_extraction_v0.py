"""Run extraction (branch 1, version 0).

Renamed from `31_run_extraction_wip.py` to a module-name-friendly filename so it
can be imported normally (`import run_extraction_branch1_v0`).
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from openai import OpenAI
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# Define small Pydantic models (copied from the original extraction script)
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

# Initialize minimal client and graph wiring
client = OpenAI()

# LLM caller used by the LangGraph workflow
def call_llm(state, prompt_id: str, file_id: str, image_ids: Optional[List[str]] = None):
    content = [{"type": "input_file", "file_id": file_id}]
    if image_ids:
        for img in image_ids[:2]:
            content.append({"type": "input_image", "file_id": img})

    response = client.responses.parse(
        prompt={"id": prompt_id},
        input=[{"role": "user", "content": content}],
        text_format=ExtractionResult
    )
    result: ExtractionResult = response.output_parsed
    json_output = result.model_dump_json(indent=2, by_alias=True, exclude_none=False)
    return {"messages": state.get("messages", []), "extraction_result": result, "json_output": json_output}

# Define state and graph
class State(TypedDict):
    messages: list
    extraction_result: Optional[ExtractionResult]
    json_output: Optional[str]
    error: Optional[str]

workflow = StateGraph(State)
workflow.add_node("call_llm", call_llm)
workflow.add_edge(START, "call_llm")
workflow.add_edge("call_llm", END)
app = workflow.compile()

# The single exported function
def run_extraction(prompt_id: str, file_id: str, image_ids: Optional[List[str]] = None, dry_run: bool = False) -> Dict[str, Any]:
    if dry_run:
        return {"status": "dry-run", "prompt_id": prompt_id, "file_id": file_id, "image_ids": image_ids}

    state = {"messages": []}
    content = [{"type": "input_file", "file_id": file_id}]
    if image_ids:
        for img in (image_ids or [])[:2]:
            content.append({"type": "input_image", "file_id": img})

    response = app.invoke({
        "messages": state.get("messages", []),
        "prompt": {"id": prompt_id},
        "input": [{"role": "user", "content": content}]
    })

    return response


if __name__ == "__main__":
    # Keep CLI similar to the previous script
    import argparse
    ap = argparse.ArgumentParser(description="Run LangGraph extraction")
    ap.add_argument("prompt_id", nargs="?", help="Prompt ID", default=None)
    ap.add_argument("file_id", nargs="?", help="File ID", default=None)
    ap.add_argument("image_ids", nargs="*", help="Optional image IDs", default=None)
    ap.add_argument("--dry-run", action="store_true", help="Do not call the API; return inputs only")
    args = ap.parse_args()

    DEFAULT_PROMPT = "pmpt_68d3321897f481979180ca9152284cd00a7317fbe81972f1"
    DEFAULT_FILE_IDS = [
        "file-RYMeojcDFBtoDYNwne2XHe",
        "file-91iJcHy825krxoJeR1pRR6",
        "file-2rs6FKsigL6J9LQyf8hDB4",
    ]

    prompt_id = args.prompt_id or DEFAULT_PROMPT
    if args.file_id:
        file_id = args.file_id
        image_ids = args.image_ids or []
    else:
        file_id = DEFAULT_FILE_IDS[2]
        image_ids = DEFAULT_FILE_IDS[:2]

    print(f"Running extraction with prompt={prompt_id}, file_id={file_id}, image_ids={image_ids}, dry_run={args.dry_run}")
    out = run_extraction(prompt_id, file_id, image_ids=image_ids, dry_run=args.dry_run)
    if out.get("error"):
        print("ERROR:", out["error"])
    else:
        jo = out.get("json_output")
        if jo:
            print(jo)
        else:
            print(out)
