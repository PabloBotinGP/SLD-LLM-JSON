"""Parse model responses into Pydantic model and save (renamed from 03_extract_parse_wip.py).
"""

from openai import OpenAI
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

class EquipmentEntry(BaseModel):
    found: bool
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    evidence_note: Optional[str] = None
    page_refs: List[int]

class ExtractionResult(BaseModel):
    # Using List[EquipmentEntry] here; original used conlist(..., max_length=1)
    # to constrain length. If you need that validation, reintroduce conlist in
    # the type annotations.
    inverter: Optional[List[EquipmentEntry]] = Field(default=None, alias="Inverter")
    module: Optional[List[EquipmentEntry]] = Field(default=None, alias="Module")
    racking_system: Optional[List[EquipmentEntry]] = Field(default=None, alias="Racking System")

    model_config = ConfigDict(populate_by_name=True)


# ---------- OpenAI client ----------
client = OpenAI()

# If your Prompt (in the Dashboard) already includes the file and all instructions:
response = client.responses.parse(
    model="gpt-5",
    prompt={
        "id": "pmpt_68d3321897f481979180ca9152284cd00a7317fbe81972f1",
        "version": "1"
    },
    # Ask the SDK to enforce and parse into our Pydantic model
    text_format=ExtractionResult
)

# You now get a Pydantic object, not just text
result: ExtractionResult = response.output_parsed

# ----- Save to JSON on disk (using your exact top-level keys via aliases) -----
# Pydantic v2:
json_str = result.model_dump_json(indent=2, by_alias=True, exclude_none=False)
with open("extracted_fields.json", "w", encoding="utf-8") as f:
    f.write(json_str)

print("✅ Saved to extracted_fields.json")
