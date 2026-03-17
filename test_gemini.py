import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

try:
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents="Hi",
    )
    print("Default success:", response.text)
except Exception as e:
    print("Default error:", e)

try:
    response = client.models.generate_content(
        model="gemini-3-flash-preview",
        contents="Hi",
        config=types.GenerateContentConfig(http_options={'timeout': 60000})
    )
    print("Timeout 60000 success:", response.text)
except Exception as e:
    print("Timeout 60 error:", e)
