# Import necessary libraries
from openai import OpenAI

# Define client
client = OpenAI()

# Ask the model to analyze it via Responses API.
# The prompt was created in the Dashboard and includes the file.
response = client.responses.create(
    model="gpt-5",
    prompt={
        "id": "pmpt_68d3321897f481979180ca9152284cd00a7317fbe81972f1",
        "version": "1"
    }
)

# Extract the text output (first message, first content block)
output_text = response.output[0].content[0].text

# Print to terminal
print(output_text)

# Save to txt file
with open("model_output.txt", "w", encoding="utf-8") as f:
    f.write(output_text)

print("✅ Saved output to model_output.txt")

