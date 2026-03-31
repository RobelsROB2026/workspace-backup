import json
import os
import subprocess
import asyncio
from twikit import Client

STATE_FILE = os.path.expanduser("~/research/social-auto/barry_video_state.json")
TEMP_DIR = "/tmp/openclaw/uploads"
COOKIES_FILE = os.path.join(TEMP_DIR, "twikit_cookies.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"posted_drive_ids": [], "last_run": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

print("Script works syntactically!")
