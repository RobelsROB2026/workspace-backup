import json
import os
import sys

STATE_FILE = os.path.expanduser("~/research/social-auto/barry_video_state.json")
FOLDER_ID = "11IjZBXaII_s67KZzFw8IF-HXSMuf4PW4"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"posted_drive_ids": [], "last_run": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

print("Daily poster script skeleton created.")
