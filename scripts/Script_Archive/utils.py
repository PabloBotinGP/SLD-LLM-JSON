# Import necessary libraries
import base64
from openai import OpenAI

# Define client
client = OpenAI()

# Upload file using File API. https://platform.openai.com/docs/api-reference/files
file = client.files.create(
    file=open("diagram.pdf", "rb"),
    purpose="user_data"
) # Returns the uploaded file object:https://platform.openai.com/docs/api-reference/files/object

# File object example: 
# FileObject(
#  id='file-LN3RtQEimj3chBFKbbA5Mv',
#  bytes=10261015, 
#  created_at=1758667240,
#  filename='diagram.pdf',
#  object='file',
#  purpose='user_data',
#  status='processed',
#  expires_at=None,
#  status_details=None)

# 
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
                    "text": "What is the first dragon in the book?",
                },
            ]
        }
    ]
)# Returns a response object. 

# Response object example:
#  Response(id='resp_68d324f7f8208190a6a91574ef3ba9450a870a2e0ed9f824',
#  created_at=1758668026.0,
#  error=None,
#  incomplete_details=None,
#  instructions=None,
#  metadata={},
#  model='gpt-5-2025-08-07',
#  object='response',
#  output=
#   [ResponseReasoningItem(
#       id='rs_68d324fd11b08190b88814c4807c3c790a870a2e0ed9f824',
#       summary=[], 
#       type='reasoning', 
#       content=None, 
#       encrypted_content=None, 
#       status=None), 
#     ResponseOutputMessage(
#       id='msg_68d3251830388190a3ff7aba7bbd09360a870a2e0ed9f824', 
#       content=
#           [ResponseOutputText(annotations=[], 
#           text='It’s a residential solar PV permit plan set.', 
#           type='output_text', 
#           logprobs=[])], 
#           role='assistant', 
#           status='completed', 
#           type='message')], 
#           parallel_tool_calls=True, 
#           temperature=1.0, 
#           tool_choice='auto', 
#           tools=[], 
#           top_p=1.0, 
#           background=False, 
#           conversation=None, 
#           max_output_tokens=None, 
#           max_tool_calls=None, 
#           previous_response_id=None, 
#           prompt=None, 
#           prompt_cache_key=None, 
#           reasoning=Reasoning(effort='medium', generate_summary=None, summary=None), 
#           safety_identifier=None, 
#           service_tier='default', 
#           status='completed', 
#           text=ResponseTextConfig(format=ResponseFormatText(type='text'), verbosity='medium'), 
#           top_logprobs=0, 
#           truncation='disabled', 
#           usage=ResponseUsage(
#               input_tokens=14685, 
#               input_tokens_details=InputTokensDetails(cached_tokens=14592), 
#               output_tokens=1382, 
#               output_tokens_details=OutputTokensDetails(reasoning_tokens=1088), 
#               total_tokens=16067),    
#           user=None, 
#           billing={'payer': 'developer'}, 
#           store=True)

print(response.output_text)