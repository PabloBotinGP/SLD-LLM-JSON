from openai import OpenAI
client = OpenAI()

response = client.responses.create(
  model="gpt-5",
  input=[
    {
      "role": "developer",
      "content": [
        {
          "type": "input_text",
          "text": "Extract manufacturer, model, and equipment details for Inverter, Module, and Racking System from the provided document, following these structured rules:\n\n- Use only manufacturer, model, and equipment names explicitly present in the document (PDF or image pages). Do not invent, infer, or correct names.\n- Preserve exact casing and string as seen in the document (e.g., “240V”, “IQ7HS-66-M-US”, “SPR‑MAX6‑435”).\n- Include a field page_refs for every item, listing all 1-based page numbers where supporting evidence appears.\n- If a field is uncertain, unreadable, or unavailable, set its value to null and briefly explain in evidence_note (≤160 chars).\n- If multiple pages support an item, include all relevant page_refs.\n- If fields or values for the same equipment type differ across pages, select the item from the latest revision or equipment schedule and mention the conflict briefly in evidence_note.\n- Allowed equipment types are strictly: Inverter, Module, Racking System. Use these names as top-level keys in the results.\n- Maximum one array element per equipment type: \n    - If multiple candidates exist, select the single “primary” instance for each type using this precedence:\n        1. Equipment schedule or “PV Equipment” tables.\n        2. Dedicated specification blocks on SLD (e.g., “INVERTER SPECIFICATION”).\n        3. Data sheet pages for that equipment type.\n        4. Labels/symbols on the single line diagram.\n    - For Racking System: select the rail/structural mounting system only (e.g., Unirac rail); do not add a second instance for attachment hardware. If attachment hardware is mentioned, note it in evidence_note.\n- For each equipment type, here’s where to search:\n    - **Inverter**: “Inverter Make/Model”, equipment schedule/table, SLD callouts, inverter spec blocks, or inverter datasheets.\n    - **Module**: “Modules” row in schedule, module spec block, datasheet/UL pages, roof plan annotation.\n    - **Racking System**: roof mounting plan, roof calcs, “mount”, racking data sheets, etc. Use known systems such as ‘Unirac - Solar Mount Flush’, ‘IronRidge - XR Flush Mount’ etc. Mention attachments in evidence_note if present.\n\nIf you cannot comply with all instructions, reply exactly with:\n{\"error\":\"schema_not_met\"}\n\n# Steps\n\n1. Identify explicit manufacturer/model/equipment names for Inverter, Module, Racking System in the document.\n2. For each equipment type, follow the precedence order to select the primary instance. Do not create more than one item per type.\n3. Extract required fields, including the exact string and casing, and attach page_refs (array of all 1-based source page numbers).\n4. If any field is missing, unreadable, or uncertain, set it to null and provide a concise reason in evidence_note (≤160 chars).\n5. If equipment type is absent, omit its key from the output or set as [].\n6. Ensure Racking System represents the rail/mount system only (not hardware), mentioning any attachment in evidence_note.\n7. Output must be strictly JSON: valid, with no prose, comments, markdown, or trailing commas.\n8. If any constraint is not met, return only: {\"error\":\"schema_not_met\"}\n\n# Output Format\n\n- Top-level object with only the present equipment types (Inverter, Module, Racking System), each mapping to an array (≤1 item) or omitted/[].\n- Each equipment object includes required fields, page_refs array, and evidence_note as needed.\n- Response must be valid JSON; no text, markdown, or comments.\n\n# Examples\n\n**Example (with one item per type):**\n{\n  \"Inverter\": [\n    {\n      \"manufacturer\": \"Enphase Energy\",\n      \"model\": \"IQ7HS-66-M-US\",\n      \"page_refs\": [3, 7],\n      \"evidence_note\": \"Latest revision preferred; earlier version showed 'IQ7H-60-US'.\"\n    }\n  ],\n  \"Module\": [\n    {\n      \"manufacturer\": \"SunPower\",\n      \"model\": \"SPR-MAX6-435\",\n      \"page_refs\": [4],\n      \"evidence_note\": null\n    }\n  ],\n  \"Racking System\": [\n    {\n      \"manufacturer\": \"Unirac\",\n      \"model\": \"SolarMount Flush\",\n      \"page_refs\": [10, 11],\n      \"evidence_note\": \"Attachment hardware (Pegasus mounts) noted on p11.\"\n    }\n  ]\n}\n\n**Example (if a value is unreadable):**\n{\n  \"Inverter\": [\n    {\n      \"manufacturer\": null,\n      \"model\": \"SE6000H-US\",\n      \"page_refs\": [2],\n      \"evidence_note\": \"Manufacturer name illegible on datasheet.\"\n    }\n  ]\n}\n\n**Example (if a type is not present):**\n{\n  \"Inverter\": [...],\n  \"Module\": [...],\n  // Racking System key omitted, as not found\n}\n\n# Notes\n\n- Never invent or infer missing manufacturer/model names.\n- If information is missing or ambiguous, use null and evidence_note.\n- One item per equipment type maximum.\n- Output must be valid JSON (no prose, comments, or trailing commas).\n- Return exactly {\"error\":\"schema_not_met\"} if any condition cannot be met.\n\nReminder: Carefully follow the rules for equipment selection, null assignment, evidence notes, and output formatting. Only output valid JSON per instructions."
        }
      ]
    },
    {
      "role": "user",
      "content": [
        {
          "type": "input_text",
          "text": "Analyze the attached electrical single-line diagram (PDF). Extract the equipment details for Inverter, Module, and Racking System as specified. Return the results strictly in JSON following the defined schema, with exact strings and page references.\n"
        }
      ]
    }
  ],
  text={
    "format": {
      "type": "json_schema",
      "name": "equipment_summary",
      "strict": True,
      "schema": {
        "type": "object",
        "properties": {
          "Inverter": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "found": {
                  "type": "boolean",
                  "description": "Whether the inverter was found"
                },
                "manufacturer": {
                  "type": "string",
                  "description": "The inverter manufacturer, or empty if unavailable",
                  "minLength": 0
                },
                "model": {
                  "type": "string",
                  "description": "The inverter model, or empty if unavailable",
                  "minLength": 0
                },
                "evidence_note": {
                  "type": "string",
                  "description": "A textual note citing the evidence for this inverter"
                },
                "page_refs": {
                  "type": "array",
                  "items": {
                    "type": "integer",
                    "description": "Page number of relevant evidence"
                  },
                  "description": "Pages where supporting evidence was found"
                }
              },
              "required": [
                "found",
                "manufacturer",
                "model",
                "evidence_note",
                "page_refs"
              ],
              "additionalProperties": False
            },
            "description": "List of inverter search results"
          },
          "Module": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "found": {
                  "type": "boolean",
                  "description": "Whether the module was found"
                },
                "manufacturer": {
                  "type": "string",
                  "description": "The module manufacturer, or empty if unavailable",
                  "minLength": 0
                },
                "model": {
                  "type": "string",
                  "description": "The module model, or empty if unavailable",
                  "minLength": 0
                },
                "evidence_note": {
                  "type": "string",
                  "description": "A textual note citing the evidence for this module"
                },
                "page_refs": {
                  "type": "array",
                  "items": {
                    "type": "integer",
                    "description": "Page number of relevant evidence"
                  },
                  "description": "Pages where supporting evidence was found"
                }
              },
              "required": [
                "found",
                "manufacturer",
                "model",
                "evidence_note",
                "page_refs"
              ],
              "additionalProperties": False
            },
            "description": "List of module search results"
          },
          "Racking System": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "found": {
                  "type": "boolean",
                  "description": "Whether the racking system was found"
                },
                "manufacturer": {
                  "type": "string",
                  "description": "The racking system manufacturer, or empty if unavailable",
                  "minLength": 0
                },
                "model": {
                  "type": "string",
                  "description": "The racking system model, or empty if unavailable",
                  "minLength": 0
                },
                "evidence_note": {
                  "type": "string",
                  "description": "A textual note citing the evidence for this racking system"
                },
                "page_refs": {
                  "type": "array",
                  "items": {
                    "type": "integer",
                    "description": "Page number of relevant evidence"
                  },
                  "description": "Pages where supporting evidence was found"
                }
              },
              "required": [
                "found",
                "manufacturer",
                "model",
                "evidence_note",
                "page_refs"
              ],
              "additionalProperties": False
            },
            "description": "List of racking system search results"
          }
        },
        "required": [
          "Inverter",
          "Module",
          "Racking System"
        ],
        "additionalProperties": False
      }
    },
    "verbosity": "low"
  },
  reasoning={
    "effort": "high",
    "summary": "auto"
  },
  tools=[
    {
      "type": "file_search",
      "vector_store_ids": [
        "vs_68d33131305881918e1d00741e7418a6"
      ]
    }
  ],
  store=True,
  include=[
    "reasoning.encrypted_content",
    "web_search_call.action.sources"
  ]
)