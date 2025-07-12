from dotenv import load_dotenv
import google.generativeai as genai
import os

# Load environment variables from .env file
load_dotenv()

# Get the Google API key from .env
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Configure the Gemini API with the loaded key
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)
else:
    raise ValueError("GOOGLE_API_KEY not found in environment variables.")

# Initialize the Gemini model
model = genai.GenerativeModel('gemini-1.5-flash')

# Start a chat session to support memory/context
chat_session = model.start_chat(history=[])

def get_gemini_response(prompt):
    """
    Sends a prompt to Gemini AI and returns the response text.
    """
    try:
        response = chat_session.send_message(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred while fetching the Gemini response: {e}"