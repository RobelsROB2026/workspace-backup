import json
import os

STATE_FILE = os.path.expanduser("~/research/social-auto/barry_video_state.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"posted_drive_ids": [], "last_run": None}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

files = [
    {"id": "1COYb8tJ7YuIDCNJhwzb7o8G8vfRP8NXy", "name": "lv_0_20250730211003.mp4", "webViewLink": "https://drive.google.com/file/d/1COYb8tJ7YuIDCNJhwzb7o8G8vfRP8NXy/view?usp=drivesdk"},
    {"id": "1CczykH07m10EVgl_312kDxYkttksOCAh", "name": "BARRY HAULER SLAMS A PINEAPPLE", "webViewLink": "https://drive.google.com/file/d/1CczykH07m10EVgl_312kDxYkttksOCAh/view?usp=drivesdk"},
    {"id": "1FCxVbmXewAHCGSzPBQbC97_5wrJjaXRO", "name": "lv_0_20250804211442.mp4", "webViewLink": "https://drive.google.com/file/d/1FCxVbmXewAHCGSzPBQbC97_5wrJjaXRO/view?usp=drivesdk"},
    {"id": "1Gzi3IzQftHEenC1soMf1OpekXMwR-0Ob", "name": "THE DAY HE ALMOST DIED", "webViewLink": "https://drive.google.com/file/d/1Gzi3IzQftHEenC1soMf1OpekXMwR-0Ob/view?usp=drivesdk"},
]

state = load_state()

# We manually mark the ones we've already done or know are done
posted_ids = [
  "1OmvHlb4m6pGtJ3ENUVOqgp4ou-ZZc9U0", # Barry's fever dream
  "1KUgjR98Wa8yEEG-8PAcBX4Hlsm16DSDB", # No Trucking For Old Men
  "1ELZIuY10xatxfsPrn8VmMgsiyUkvWTQc", # Standoff with Wrenchnator
]

for pid in posted_ids:
    if pid not in state["posted_drive_ids"]:
        state["posted_drive_ids"].append(pid)

save_state(state)

next_vid = None
for f in files:
    if f["id"] not in state["posted_drive_ids"]:
        next_vid = f
        break

print(f"Next Video:\nName: {next_vid['name']}\nLink: {next_vid['webViewLink']}\nID: {next_vid['id']}")
