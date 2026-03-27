import os
import logging
from dotenv import load_dotenv
from google import genai
import http.client

load_dotenv(os.path.expanduser("~/research/trucking/.env"))

# Enable full debug logging for urllib3 to capture raw request payload
http.client.HTTPConnection.debuglevel = 1

# Configure logging to capture requests
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
req_log = logging.getLogger('requests.packages.urllib3')
req_log.setLevel(logging.DEBUG)
req_log.propagate = True

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL = "gemini-3-flash-preview"

print("==================== RAW REQUEST LOG ====================")
response = client.models.generate_content(
    model=MODEL,
    contents="Say hi"
)
