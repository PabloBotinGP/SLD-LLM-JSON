"""
Development Scripts Utilities

This module defines all functions used to define the scripts.

Main functional areas:
1. PDF Rendering: Convert PDF files to PNG images 
2. OpenAI Extraction: Extract structured equipment data using OpenAI API
3. Lambda/Module Loading: Dynamically load Python modules for Lambda execution
4. File Management: Handle JSON output saving and timestamping

Dependencies:
- openai: OpenAI API client
- pydantic: Data validation and serialization
- langgraph: Graph-based workflow execution
- pymupdf (fitz): PDF rendering
- Standard library: os, json, datetime, argparse, importlib

Environment Requirements:
- OPENAI_API_KEY: Required for extraction functions
- Python 3.8+: For typing annotations and modern features
"""

import os
import json
import argparse
import importlib.util
import sys
import fitz  # PyMuPDF
from datetime import datetime
from typing import Optional, List, Dict, Any, Set
from importlib.machinery import SourceFileLoader

# OpenAI and Pydantic imports (lazy loaded in extraction functions)
try:
    from openai import OpenAI
    from pydantic import BaseModel, Field, ConfigDict
    from langgraph.graph import StateGraph, START, END
    from typing_extensions import TypedDict
    EXTRACTION_DEPS_AVAILABLE = True
except ImportError:
    EXTRACTION_DEPS_AVAILABLE = False

# ============================================================================
# PDF RENDERING UTILITIES
# ============================================================================

def parse_page_ranges(pages_arg: Optional[str], num_pages: int) -> List[int]:
    """
    Parse page range specification into a list of page numbers.
    
    Args:
        pages_arg: String like "1,3-5,7" or None for all pages
        num_pages: Total number of pages in the document
    
    Returns:
        List of 1-based page numbers to process
        
    Examples:
        parse_page_ranges("1,3-5", 10) -> [1, 3, 4, 5]
        parse_page_ranges(None, 5) -> [1, 2, 3, 4, 5]
        parse_page_ranges("2-4,1", 10) -> [1, 2, 3, 4]
    """
    if not pages_arg:
        return list(range(1, num_pages + 1))
    
    out = set()
    for part in pages_arg.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            a, b = int(a), int(b)
            if a < 1 or b < 1 or a > num_pages or b > num_pages or a > b:
                raise ValueError(f"Invalid page range: {part}")
            out.update(range(a, b + 1))
        else:
            p = int(part)
            if p < 1 or p > num_pages:
                raise ValueError(f"Invalid page number: {p}")
            out.add(p)
    
    return sorted(out)


def render_pdf_to_images(pdf_path: str, dpi: int = 300, pages: Optional[str] = None, 
                        grayscale: bool = False) -> List[str]:
    """
    Render PDF pages to PNG images with customizable options.
    
    Args:
        pdf_path: Path to the input PDF file
        dpi: Resolution for rendering (default: 300)
        pages: Page specification like "1,3-5" or None for all pages
        grayscale: Whether to convert images to grayscale
    
    Returns:
        List of paths to the generated PNG files
        
    Creates:
        - A folder with the same name as the PDF (without extension)
        - PNG files for each rendered page
        - A copy of the original PDF in the output folder
        
    Example:
        files = render_pdf_to_images("document.pdf", dpi=450, pages="1-3")
        # Creates: document/document_p01.png, document/document_p02.png, etc.
    """
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    num_pages = doc.page_count
    page_list = parse_page_ranges(pages, num_pages)

    # Create output folder named after the PDF
    base_name, _ = os.path.splitext(pdf_path)
    output_folder = base_name
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Calculate zoom factor from DPI
    zoom = dpi / 72.0
    transform_matrix = fitz.Matrix(zoom, zoom)

    # Determine naming strategy
    single_page_output = (len(page_list) == 1)
    saved_files = []
    
    for page_num in page_list:  # 1-based page numbers
        page = doc[page_num - 1]  # Convert to 0-based for PyMuPDF
        pixmap = page.get_pixmap(matrix=transform_matrix, alpha=False)

        # Apply grayscale conversion if requested
        if grayscale and pixmap.n > 1:
            pixmap = fitz.Pixmap(fitz.csGRAY, pixmap)

        # Generate output filename
        base_filename = os.path.basename(base_name)
        if single_page_output:
            output_path = os.path.join(output_folder, f"{base_filename}.png")
        else:
            output_path = os.path.join(output_folder, f"{base_filename}_p{page_num:02d}.png")

        pixmap.save(output_path)
        saved_files.append(output_path)

    # Copy original PDF to output folder
    pdf_copy_path = os.path.join(output_folder, f"{os.path.basename(base_name)}.pdf")
    if not os.path.exists(pdf_copy_path):
        with open(pdf_path, "rb") as src, open(pdf_copy_path, "wb") as dst:
            dst.write(src.read())

    doc.close()
    return saved_files


# ============================================================================
# OPENAI EXTRACTION UTILITIES
# ============================================================================

class EquipmentEntry(BaseModel):
    """
    Represents a single piece of equipment found in the extraction.
    
    Attributes:
        found: Whether this equipment type was identified
        manufacturer: Equipment manufacturer name (if found)
        model: Equipment model/part number (if found)  
        evidence_note: Additional context or evidence from the document
    """
    found: bool
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    evidence_note: Optional[str] = None


class ExtractionResult(BaseModel):
    """
    Complete extraction result containing all equipment types.
    
    Each equipment type is a list with at most one entry, following the
    OpenAI API's structured output format for this specific use case.
    """
    inverter: Optional[List[EquipmentEntry]] = Field(default=None, alias="Inverter", max_length=1)
    module: Optional[List[EquipmentEntry]] = Field(default=None, alias="Module", max_length=1)
    racking_system: Optional[List[EquipmentEntry]] = Field(default=None, alias="Racking System", max_length=1)

    model_config = ConfigDict(populate_by_name=True)


class ExtractionState(TypedDict):
    """State dictionary for LangGraph workflow execution."""
    messages: list
    extraction_result: Optional[ExtractionResult]
    json_output: Optional[str]
    error: Optional[str]


# Global OpenAI client (lazy initialization)
_openai_client = None

def get_openai_client() -> OpenAI:
    """
    Get or create the OpenAI client instance.
    
    Returns:
        Configured OpenAI client
        
    Raises:
        RuntimeError: If OPENAI_API_KEY is not set in environment
        ImportError: If OpenAI dependencies are not available
    """
    global _openai_client
    
    if not EXTRACTION_DEPS_AVAILABLE:
        raise ImportError("OpenAI extraction dependencies not available. Install with: pip install openai pydantic langgraph")
    
    if _openai_client is None:
        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY not set in environment. Set the environment variable before calling extraction functions.")
        _openai_client = OpenAI()
    
    return _openai_client


def call_openai_extraction(state: Dict[str, Any], prompt_id: str, file_id: str, 
                          image_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Call OpenAI API for equipment extraction from documents.
    
    This is a LangGraph node function that processes the extraction request
    and returns structured results using the Pydantic models.
    
    Args:
        state: LangGraph state dictionary
        prompt_id: OpenAI prompt ID for the extraction task
        file_id: Primary document file ID
        image_ids: Optional list of image file IDs (max 2)
    
    Returns:
        Updated state dictionary with extraction results or error information
    """
    try:
        # Build content list for multimodal input
        content = [{"type": "input_file", "file_id": file_id}]
        if image_ids:
            for img_id in image_ids[:2]:  # Limit to 2 images
                if img_id and img_id.strip():
                    content.append({"type": "input_image", "file_id": img_id})

        # Call OpenAI Responses API with structured output
        response = get_openai_client().responses.parse(
            prompt={"id": prompt_id},
            input=[{
                "role": "user",
                "content": content,
            }],
            text_format=ExtractionResult
        )
        
        # Extract parsed result
        result: ExtractionResult = response.output_parsed
        json_output = result.model_dump_json(indent=2, by_alias=True, exclude_none=False)
        
        return {
            "messages": state.get("messages", []),
            "extraction_result": result,
            "json_output": json_output
        }
        
    except Exception as e:
        import traceback
        error_details = f"OpenAI extraction failed: {str(e)}\n{traceback.format_exc()}"
        print(f"DEBUG Error: {error_details}")
        return {
            "messages": state.get("messages", []),
            "extraction_result": None,
            "json_output": None,
            "error": error_details
        }


def save_extraction_results(json_output: str, base_directory: str) -> Dict[str, str]:
    """
    Save extraction results to both latest and timestamped files.
    
    Args:
        json_output: JSON string to save
        base_directory: Directory where files should be saved
    
    Returns:
        Dictionary with 'latest' and 'timestamped' file paths
        
    Example:
        paths = save_extraction_results(json_data, "/path/to/dev_scripts")
        # Creates: extracted_fields.json and extracted_fields-2023-11-20T15-30-45Z.json
    """
    try:
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%SZ")
        
        # Save timestamped version
        timestamped_filename = f"extracted_fields-{timestamp}.json"
        timestamped_path = os.path.join(base_directory, timestamped_filename)
        with open(timestamped_path, "w", encoding="utf-8") as f:
            f.write(json_output)

        # Save/update latest version
        latest_path = os.path.join(base_directory, "extracted_fields.json")
        with open(latest_path, "w", encoding="utf-8") as f:
            f.write(json_output)
            
        return {
            "latest": latest_path,
            "timestamped": timestamped_path
        }
        
    except Exception as e:
        print(f"Warning: Failed to save extraction files: {e}")
        return {}


def run_extraction(prompt_id: Optional[str] = None, file_id: Optional[str] = None, 
                  image_ids: Optional[List[str]] = None, dry_run: bool = False) -> Dict[str, Any]:
    """
    Execute the complete equipment extraction workflow.
    
    This is the main entry point for extraction functionality. It can use
    provided IDs or fall back to embedded defaults for testing.
    
    Args:
        prompt_id: OpenAI prompt ID (uses default if None)
        file_id: Document file ID (uses default if None)
        image_ids: Optional image file IDs
        dry_run: If True, return mock data without calling API
    
    Returns:
        Dictionary containing:
        - extraction_result: Parsed Pydantic object (or None)
        - json_output: JSON string of results (or None)  
        - error: Error message if extraction failed
        - messages: Empty list (for LangGraph compatibility)
        
    Side Effects:
        - Saves results to extracted_fields.json and timestamped files
        - Prints debug information on errors
    """
    # Embedded defaults for testing/development
    DEFAULT_PROMPT_ID = "pmpt_68d3321897f481979180ca9152284cd00a7317fbe81972f1"
    DEFAULT_CONTENT = [
        {"type": "input_image", "file_id": "file-RYMeojcDFBtoDYNwne2XHe"},
        {"type": "input_image", "file_id": "file-91iJcHy825krxoJeR1pRR6"},
        {"type": "input_file", "file_id": "file-2rs6FKsigL6J9LQyf8hDB4"},
    ]
    
    # Use provided IDs or fall back to defaults
    used_prompt = prompt_id or DEFAULT_PROMPT_ID
    used_file_id = file_id or (DEFAULT_CONTENT[-1].get("file_id") if DEFAULT_CONTENT else None)
    
    if dry_run:
        return {
            "status": "dry-run", 
            "prompt_id": used_prompt, 
            "file_id": used_file_id, 
            "image_ids": image_ids
        }

    try:
        # Choose between provided IDs and embedded defaults
        if not prompt_id or not file_id:
            # Use embedded defaults
            response = get_openai_client().responses.parse(
                prompt={"id": DEFAULT_PROMPT_ID},
                input=[{"role": "user", "content": DEFAULT_CONTENT}],
                text_format=ExtractionResult,
            )
        else:
            # Use provided IDs
            content = [{"type": "input_file", "file_id": used_file_id}]
            if image_ids:
                for img in image_ids[:2]:
                    if img and img.strip():
                        content.append({"type": "input_image", "file_id": img})

            response = get_openai_client().responses.parse(
                prompt={"id": used_prompt},
                input=[{"role": "user", "content": content}],
                text_format=ExtractionResult,
            )

        # Process results
        result: ExtractionResult = response.output_parsed
        json_output = result.model_dump_json(indent=2, by_alias=True, exclude_none=False)
        
        # Save to files (attempt, but don't fail if it doesn't work)
        base_dir = os.path.dirname(__file__)
        save_extraction_results(json_output, base_dir)
        
        return {
            "messages": [], 
            "extraction_result": result, 
            "json_output": json_output
        }
        
    except Exception as e:
        import traceback
        error_details = f"Extraction failed: {str(e)}\n{traceback.format_exc()}"
        print(f"DEBUG Error: {error_details}")
        return {
            "messages": [], 
            "extraction_result": None, 
            "json_output": None, 
            "error": error_details
        }


# ============================================================================
# MODULE LOADING UTILITIES (for Lambda/dynamic execution)
# ============================================================================

def load_module_from_path(script_path: str, module_name: Optional[str] = None):
    """
    Dynamically load a Python module from a file path.
    
    This function handles the importlib mechanics and proper module registration
    needed for tools like Pydantic and LangGraph that rely on module introspection.
    
    Args:
        script_path: Absolute or relative path to the Python file
        module_name: Name to register module under (uses filename if None)
    
    Returns:
        The loaded module object
        
    Raises:
        FileNotFoundError: If the script file doesn't exist
        ImportError: If the module fails to load
        
    Example:
        module = load_module_from_path("dev_scripts/run_extraction.py")
        extraction_func = getattr(module, "run_extraction", None)
    """
    # Convert to absolute path
    if not os.path.isabs(script_path):
        script_path = os.path.join(os.getcwd(), script_path)
    
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"Script not found: {script_path}")

    # Determine module name (important for type introspection)
    if module_name is None:
        module_name = os.path.splitext(os.path.basename(script_path))[0]
    
    # Load using SourceFileLoader
    loader = SourceFileLoader(module_name, script_path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)

    # Register in sys.modules for introspection tools
    sys.modules[module_name] = module

    # Execute the module (runs import-time code)
    loader.exec_module(module)
    
    return module


def load_run_extraction_function(script_path: str):
    """
    Load a run_extraction function from a Python script file.
    
    This is a specialized version of load_module_from_path that specifically
    looks for and returns the 'run_extraction' function, which is the
    standard interface expected by the Lambda wrapper.
    
    Args:
        script_path: Path to Python file containing run_extraction function
        
    Returns:
        The run_extraction callable, or None if not found
        
    Raises:
        FileNotFoundError: If script file doesn't exist
        
    Example:
        extractor = load_run_extraction_function("dev_scripts/run_extraction.py")
        if extractor:
            result = extractor("prompt_123", "file_456", image_ids=["img_1"])
    """
    module = load_module_from_path(script_path)
    return getattr(module, "run_extraction", None)


# ============================================================================
# LAMBDA HANDLER UTILITIES
# ============================================================================

def parse_lambda_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse Lambda event payload from various invocation sources.
    
    Lambda events can come from API Gateway (JSON in body), direct invocation
    (payload in event), or other sources. This function normalizes the format.
    
    Args:
        event: Raw Lambda event dictionary
        
    Returns:
        Parsed payload dictionary with normalized structure
        
    Example:
        payload = parse_lambda_payload(event)
        script = payload.get("script")
        prompt_id = payload.get("prompt_id")
    """
    # Handle API Gateway proxy integration (body is JSON string)
    payload = event.get("body")
    if isinstance(payload, str):
        payload = json.loads(payload) if payload else {}
    elif payload is None:
        # Direct invocation - event itself contains the payload
        payload = event
    
    return payload


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for running extraction scripts.
    
    This function serves as the main Lambda entrypoint. It parses the event,
    loads the specified script, and executes its run_extraction function.
    
    Expected Event Structure:
        {
            "script": "dev_scripts/run_extraction.py",
            "prompt_id": "pmpt_...",
            "file_id": "file_...",
            "image_ids": ["file_img1", "file_img2"],
            "dry_run": false
        }
    
    Args:
        event: Lambda event (dict or API Gateway structure)
        context: Lambda runtime context (unused)
        
    Returns:
        Lambda response with statusCode and JSON body:
        - 200: Success with extraction results
        - 400: Bad request (missing script, no run_extraction function)  
        - 500: Internal error (exception during execution)
        
    Example Response:
        {
            "statusCode": 200,
            "body": '{"status": "ok", "result": "..."}'
        }
    """
    try:
        payload = parse_lambda_payload(event)

        # Extract and validate required fields
        script = payload.get("script")
        if not script:
            return {
                "statusCode": 400, 
                "body": json.dumps({"error": "script parameter is required"})
            }

        # Extract optional parameters
        prompt_id = payload.get("prompt_id")
        file_id = payload.get("file_id")
        image_ids = payload.get("image_ids", [])
        dry_run = bool(payload.get("dry_run", False))

        # Load and validate the extraction function
        run_extraction_func = load_run_extraction_function(script)
        if not run_extraction_func:
            return {
                "statusCode": 400, 
                "body": json.dumps({
                    "error": f"Script '{script}' does not expose run_extraction function"
                })
            }

        # Execute the extraction
        result = run_extraction_func(prompt_id, file_id, image_ids=image_ids, dry_run=dry_run)
        
        return {
            "statusCode": 200, 
            "body": json.dumps({
                "status": "success", 
                "result": str(result)
            })
        }

    except Exception as e:
        # Log error details (visible in CloudWatch in Lambda environment)
        import traceback
        error_msg = f"Lambda execution error: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        
        return {
            "statusCode": 500, 
            "body": json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }


# ============================================================================
# CLI UTILITIES AND ARGUMENT PARSING
# ============================================================================

def create_extraction_cli_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for extraction CLI commands.
    
    Returns:
        Configured ArgumentParser for extraction operations
    """
    parser = argparse.ArgumentParser(
        description="Run OpenAI equipment extraction on documents"
    )
    parser.add_argument("--prompt-id", dest="prompt_id", 
                       help="OpenAI prompt ID to use in the API call")
    parser.add_argument("--file-id", dest="file_id", 
                       help="File ID for the primary input document")
    parser.add_argument("image_ids", nargs="*", 
                       help="Optional file IDs for input images (up to 2)")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Return mock data without calling OpenAI API")
    return parser


def create_lambda_cli_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for Lambda wrapper CLI commands.
    
    Returns:
        Configured ArgumentParser for Lambda operations
    """
    parser = argparse.ArgumentParser(
        description="Lambda wrapper for dynamically loading and running extraction scripts"
    )
    parser.add_argument("--script", required=True, 
                       help="Path to target Python script with run_extraction function")
    parser.add_argument("--prompt-id", "--prompt_id", dest="prompt_id", 
                       help="Prompt ID to use (optional)")
    parser.add_argument("--file-id", "--file_id", dest="file_id", 
                       help="File ID for input document (optional)")
    parser.add_argument("image_ids", nargs="*", 
                       help="Optional image file IDs")
    parser.add_argument("--dry-run", action="store_true",
                       help="Run in dry-run mode")
    return parser


def create_render_cli_parser() -> argparse.ArgumentParser:
    """
    Create argument parser for PDF rendering CLI commands.
    
    Returns:
        Configured ArgumentParser for PDF rendering operations
    """
    parser = argparse.ArgumentParser(
        description="Render PDF pages to PNG images"
    )
    parser.add_argument("pdf", help="Path to the PDF file")
    parser.add_argument("--dpi", type=int, default=300, 
                       help="Render DPI resolution (default: 300)")
    parser.add_argument("--pages", type=str, default=None,
                       help="Pages to render, e.g. '1,3-5' (1-based). Default: all pages")
    parser.add_argument("--grayscale", action="store_true",
                       help="Render in grayscale to reduce file size")
    return parser


# ============================================================================
# CONVENIENCE FUNCTIONS FOR COMMON WORKFLOWS
# ============================================================================

def extract_equipment_from_files(prompt_id: str, document_file_id: str, 
                                image_file_ids: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    High-level convenience function for equipment extraction.
    
    Args:
        prompt_id: OpenAI prompt ID for extraction
        document_file_id: Primary document file ID  
        image_file_ids: Optional supporting image file IDs
        
    Returns:
        Extraction results dictionary with structured data
        
    Example:
        result = extract_equipment_from_files(
            "pmpt_12345", 
            "file-doc123",
            ["file-img1", "file-img2"]
        )
        if result.get("extraction_result"):
            equipment = result["extraction_result"]
            print(f"Found inverter: {equipment.inverter}")
    """
    return run_extraction(prompt_id, document_file_id, image_file_ids)


def render_document_pages(pdf_path: str, output_dpi: int = 300, 
                         page_spec: Optional[str] = None) -> List[str]:
    """
    High-level convenience function for PDF rendering.
    
    Args:
        pdf_path: Path to PDF document
        output_dpi: Resolution for output images
        page_spec: Page range specification like "1-3,5"
        
    Returns:
        List of generated image file paths
        
    Example:
        images = render_document_pages("solar_plans.pdf", 450, "1-2")
        # Returns: ["solar_plans/solar_plans_p01.png", "solar_plans/solar_plans_p02.png"]
    """
    return render_pdf_to_images(pdf_path, dpi=output_dpi, pages=page_spec)


def format_extraction_results(extraction_result: ExtractionResult) -> str:
    """
    Format extraction results for human-readable display.
    
    Args:
        extraction_result: Parsed Pydantic extraction result
        
    Returns:
        Formatted string representation of the equipment found
        
    Example:
        formatted = format_extraction_results(result["extraction_result"])
        print(formatted)
        # Output:
        # 🔧 Inverter: SolarEdge SE7600H-US (Found: True)
        # 🔧 Module: Canadian Solar CS6K-300MS (Found: True)
    """
    if not extraction_result:
        return "No extraction results available"
        
    lines = []
    for equipment_type in ["Inverter", "Module", "Racking System"]:
        field_name = equipment_type.lower().replace(" ", "_")
        equipment_list = getattr(extraction_result, field_name, None)
        
        if equipment_list and len(equipment_list) > 0:
            equipment = equipment_list[0]
            lines.append(f"🔧 {equipment_type}:")
            lines.append(f"   Found: {equipment.found}")
            if equipment.manufacturer:
                lines.append(f"   Manufacturer: {equipment.manufacturer}")
            if equipment.model:
                lines.append(f"   Model: {equipment.model}")
            if equipment.evidence_note:
                lines.append(f"   Note: {equipment.evidence_note}")
            lines.append("")  # Empty line between equipment types
                
    return "\n".join(lines) if lines else "No equipment found"


# ============================================================================
# VALIDATION AND TESTING UTILITIES  
# ============================================================================

def validate_environment() -> Dict[str, bool]:
    """
    Check if required dependencies and environment variables are available.
    
    Returns:
        Dictionary with validation results for each requirement
        
    Example:
        status = validate_environment()
        if not status["openai_key"]:
            print("Warning: OPENAI_API_KEY not set")
    """
    return {
        "openai_deps": EXTRACTION_DEPS_AVAILABLE,
        "openai_key": bool(os.environ.get("OPENAI_API_KEY")),
        "pymupdf": True,  # If this imports, PyMuPDF is available
    }


def run_extraction_test(use_defaults: bool = True) -> bool:
    """
    Run a basic test of the extraction pipeline.
    
    Args:
        use_defaults: Whether to use embedded test data (True) or require real IDs
        
    Returns:
        True if test passes, False if it fails
        
    Example:
        success = run_extraction_test()
        if not success:
            print("Extraction test failed - check environment and dependencies")
    """
    try:
        if use_defaults:
            result = run_extraction(dry_run=True)
            return "status" in result and result["status"] == "dry-run"
        else:
            # Would need real prompt/file IDs
            return False
    except Exception as e:
        print(f"Extraction test failed: {e}")
        return False


if __name__ == "__main__":
    # Basic CLI interface when run directly
    print("Development Scripts Utilities")
    print("=" * 40)
    
    env_status = validate_environment()
    print("Environment Check:")
    for component, available in env_status.items():
        status = "✅" if available else "❌"
        print(f"  {component}: {status}")
    
    if all(env_status.values()):
        print("\n🎉 All dependencies available!")
        test_result = run_extraction_test()
        print(f"Extraction test: {'✅ PASS' if test_result else '❌ FAIL'}")
    else:
        print("\n⚠️  Some dependencies missing - see installation requirements")