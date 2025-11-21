## Documentation: https://platform.openai.com/docs/guides/images-vision?api-mode=responses&format=file#analyze-images
# Includes info about how to upload files to OpenAI, models, etc. 

from unittest import result
from dotenv import load_dotenv
from openai import OpenAI
import time

# Load API key from environment variable
load_dotenv()

client = OpenAI()

# Include here a function that converts PDF into JPG. (And call it). 

# Function to create a file with the Files API
def create_file(file_path):
  with open(file_path, "rb") as file_content:
    result = client.files.create(
        file=file_content,
        purpose="user_data", # 'vision': used for fine tuning. 'user_data': flexible, 'assistants': ??
            # They are all working, but lets stick to user data for now. 
    )
    return result.id

def main():
    
    image_path = "diagram.jpg" # Sending a JPG because PDF is not supported in this API.
    print(f"Uploading image: {image_path}")
    file_id = create_file(image_path)

    # First message with image
    response_1 = client.responses.create(
        model="gpt-4.1-mini", # Per order of cost (high to low): "gpt-4.1-nano", "o4-mini", "gpt-4.1-mini".
            # "gpt-4.1-nano" hallucinates!! Lets stick with "gpt-4.1-mini" for now.
        instructions="Provide a short answer that contains only one of the options of the architecture type.",
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": "Analyze the attached Single Line Diagram of a residential solar PV installation."},
                {
                    "type": "input_image",
                    "file_id": file_id,
                    "detail": "high",  # High detail is recommended for better analysis, but higher cost. Skip this field for 'auto'.
                },
                {"type": "input_text", "text": "What is the architecture type used for all inverters in this project? Choose in between: 'Microinverters', 'AC Modules', 'String Inverter without DC-DC Converters', 'String Inverter with DC-DC Converters'."},
            ],
        }],
    )

    print("Response 1:\n\n",response_1.output_text, "\n\n")

    time.sleep(1)

    if response_1.output_text.strip().startswith("Microinverters"):
        response_2 = client.responses.create(
            model="gpt-4.1-mini", # Per order of cost (high to low): "gpt-4.1-nano", "o4-mini", "gpt-4.1-mini".
            previous_response_id=response_1.id,
            instructions="Provide a super short answer, followed by a short concise explanation.",
            input=[{
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "Can you see the attached image? What is the complete inverter brand and inverter model NO.?"},
                ],
            }],
        )
        print("Response 2:\n\n",response_2.output_text, "\n\n")

if __name__ == "__main__":
    main()