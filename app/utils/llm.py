import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Gemini API
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Configure the model - using gemini-1.5-flash for speed and multi-step tool use
def get_model(tools=None, system_instruction=None):
    return genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        tools=tools,
        system_instruction=system_instruction
    )
