# Script Archive Index

This directory contains experimental, development, and reference scripts that were created during the development of the solar equipment extraction system. These scripts represent different approaches, iterations, and proof-of-concept implementations that contributed to the final production system.

## Core Extraction Scripts

### `Dev.py`
A streamlined demonstration script that shows the minimal OpenAI Responses API integration for equipment extraction. This script uses Pydantic models (`EquipmentEntry` and `ExtractionResult`) to enforce structured JSON output from the API and automatically saves results to `extracted_fields.json`. It represents the simplest possible implementation using a hardcoded prompt ID and demonstrates the core parsing workflow that became the foundation for more complex implementations.

### `parse_and_save_extraction.py` 
Similar to `Dev.py` but focuses specifically on the Pydantic model parsing and JSON serialization aspects of the extraction workflow. This script demonstrates how to use the OpenAI Responses API's structured output capabilities with custom Pydantic models, including proper field aliasing and configuration. It serves as a reference implementation for converting API responses into properly formatted JSON files with the exact field names required by the system.

### `quick_extract_example.py`
A basic example script that demonstrates the simplest possible extraction workflow using the OpenAI Responses API. Unlike the structured output versions, this script retrieves raw text output and saves it to a plain text file. It's useful as a starting point for understanding the API mechanics before adding the complexity of structured parsing and Pydantic models.

## LangGraph Integration Scripts

### `langgraph_workflow_branch1_v0.py`
The original LangGraph-based extraction implementation that combines OpenAI's Responses API with LangGraph's workflow orchestration. This script defines the complete state graph for equipment extraction, including error handling, structured output parsing, and CLI interface. It represents the bridge between simple API calls and complex workflow management, showing how to integrate multiple processing steps into a coherent extraction pipeline.

### `run_extraction_v0.py`
A modularized version of the LangGraph workflow designed to be imported by other scripts rather than run standalone. This script exports a clean `run_extraction()` function that encapsulates the entire workflow, making it suitable for use in Lambda functions, web applications, or other integration scenarios. It includes both programmatic and CLI interfaces and demonstrates how to structure extraction code for maximum reusability.

## Alternative Approaches

### `elm_tree_extraction.py`
An experimental implementation using the ELM (Explainable Language Model) framework with decision trees for equipment extraction. This script demonstrates a more structured, rule-based approach to equipment identification using NetworkX graphs and sklearn decision trees. It shows how to build conditional logic flows for different equipment types (particularly microinverters) and represents an alternative to the direct LLM approach used in the production system.

### `tree.py`
A conversation-based extraction implementation that uses the OpenAI Responses API with conversation threading and conditional logic. This script demonstrates a multi-step approach where the system first identifies the inverter architecture type and then conditionally asks follow-up questions based on the initial response. It showcases how to build interactive, context-aware extraction workflows.

## File Management and Utilities

### `upload_pdf_tool.py`
A fundamental utility script that demonstrates how to upload PDF files to OpenAI using the Files API and then analyze them using the Responses API. This script shows the basic file upload workflow that underlies all the more complex extraction implementations. It serves as a reference for understanding OpenAI's file handling requirements and API structure.

### `utils.py`
A comprehensive utility script that demonstrates the complete OpenAI Files API workflow, including detailed examples of API response objects and their structure. This script includes extensive comments showing the exact structure of FileObject and Response objects returned by the OpenAI API, making it valuable for debugging and understanding the API's behavior.

## AWS Lambda Integration

### `lambda_handler.py`
A complete AWS Lambda handler implementation designed to run the extraction scripts in a serverless environment. This script handles JSON payload parsing, dynamic module loading (to work around Python's module naming restrictions), and proper error handling for Lambda deployment. It demonstrates how to structure code for AWS Lambda deployment, including proper exception handling and response formatting.

### `README_lambda.md`
Comprehensive documentation for deploying the extraction system to AWS Lambda, including both zip-based and container-based deployment strategies. This document covers environment variable configuration, Laravel integration patterns, and provides concrete code examples for invoking Lambda functions from PHP applications. It serves as a complete deployment guide for production environments.

## Development and Testing Tools

### `env_check_example.py`
A demonstration script showcasing multi-agent conversation patterns using the OpenAI Agents framework. While not directly related to equipment extraction, this script shows advanced conversation routing and handoff patterns that could be applied to more sophisticated extraction workflows. It demonstrates how to build agents that can route conversations based on content analysis.

## Script Organization and Evolution

These scripts represent the evolutionary path of the solar equipment extraction system, from simple API calls to sophisticated workflow orchestration. The progression generally follows this pattern:

1. **Basic API Integration** (`quick_extract_example.py`, `upload_pdf_tool.py`) - Fundamental OpenAI API usage
2. **Structured Output** (`Dev.py`, `parse_and_save_extraction.py`) - Adding Pydantic models and JSON formatting
3. **Workflow Orchestration** (`langgraph_workflow_branch1_v0.py`) - Complex multi-step processing with LangGraph
4. **Modular Design** (`run_extraction_v0.py`) - Reusable components for integration
5. **Alternative Approaches** (`elm_tree_extraction.py`, `tree.py`) - Exploring different extraction methodologies
6. **Production Deployment** (`lambda_handler.py`) - Cloud deployment and integration patterns

Each script includes embedded documentation and represents a working implementation that can be used for reference, testing, or as a starting point for further development. The code demonstrates various patterns and approaches that were evaluated during the development process, providing valuable context for understanding the final system architecture.

---
