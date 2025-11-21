Overview

This folder contains tools to run the LangGraph OpenAI extraction from AWS Lambda and to call it from Laravel.

Files
- `10_extract_LangGraph_wip.py`: Main extraction script. It now exposes a programmatic function `run_extraction(prompt_id, file_id, image_ids, dry_run=False)` and still supports the CLI.
- `lambda_handler.py`: AWS Lambda handler that loads the extraction script and invokes `run_extraction`.
- `requirements.txt`: Python dependencies for the Lambda environment.

Deploying to Lambda (zip)
1. Create a deployment package (zip) containing:
   - `10_extract_LangGraph_wip.py`
   - `lambda_handler.py`
   - Any required vendor packages (install into the package root)
   - `requirements.txt` (optional)

2. Ensure environment variables are set in Lambda configuration (e.g., `OPENAI_API_KEY`).

3. Upload the zip to AWS Lambda and set the handler to `lambda_handler.lambda_handler`.

Deploying as container
- Build a container image with the above files and `requirements.txt` installed.
- Push to ECR and create a Lambda function from the image.

Laravel invocation
- Configure AWS SDK for PHP with credentials/region.
- Use `Aws\Lambda\LambdaClient` invoke method to call the function synchronously.
- Pass the payload as JSON with keys: `prompt_id`, `file_id`, `image_ids` (optional array), `dry_run` (optional).

Example Laravel code snippet (outline):

$lambda = new \Aws\Lambda\LambdaClient([...]);
$payload = json_encode([
    'prompt_id' => 'pmpt_...',
    'file_id' => 'file-abc...',
    'image_ids' => ['file-img1', 'file-img2'],
    'dry_run' => false
]);
$result = $lambda->invoke([
    'FunctionName' => 'your-lambda-name',
    'InvocationType' => 'RequestResponse',
    'Payload' => $payload,
]);
$responsePayload = json_decode((string) $result->get('Payload'), true);

Notes & Caveats
- The Lambda must have network access to the OpenAI API (VPC/NAT or public access).
- Keep `OPENAI_API_KEY` in Lambda environment variables or AWS Secrets Manager.
- For large dependencies, prefer a container image.
- Test with `dry_run=true` to avoid billing and for fast local checks.

Local testing
- You can import `run_extraction` in local Python scripts by loading the module directly or running the CLI.
- Example: `python 10_extract_LangGraph_wip.py pmpt_id file-xxx file-img1 file-img2`

