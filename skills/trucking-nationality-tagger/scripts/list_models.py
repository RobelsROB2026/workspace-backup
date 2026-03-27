import os
from dotenv import load_dotenv
from google import genai

load_dotenv(os.path.expanduser("~/research/trucking/.env"))
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

for m in client.models.list():
    if "flash" in m.name.lower():
        print(m.name)
