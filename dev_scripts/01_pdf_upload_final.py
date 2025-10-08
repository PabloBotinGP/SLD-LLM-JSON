# Import necessary libraries
import base64
from openai import OpenAI

# Define client
client = OpenAI()

# Upload file
file = client.files.create(
    file=open("diagram.pdf", "rb"),
    purpose="user_data"
) 

# Ask the model to analyze it via Responses API
response = client.responses.create(
    model="gpt-5",
    input=[
        {
            "role": "user",
            "content": [
                {
                    "type": "input_file",
                    "file_id": file.id,
                },
                {
                    "type": "input_text",
                    "text": "What is in the diagram?",
                },
            ]
        }
    ]
) 

print(response.output_text)
