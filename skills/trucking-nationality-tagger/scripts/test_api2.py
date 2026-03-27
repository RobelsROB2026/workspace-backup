import os
import http.client
from dotenv import load_dotenv
from google import genai

load_dotenv(os.path.expanduser("~/research/trucking/.env"))
http.client.HTTPConnection.debuglevel = 1

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3-flash-preview"

try:
    print(f"--- Sending minimal request to model: {MODEL} ---")
    response = client.models.generate_content(
        model=MODEL,
        contents="Say hi"
    )
    print(f"--- Response received: {response.text.strip()} ---")
except Exception as e:
    print(f"Error: {e}")
