import json

path = "/Users/roba/research/social-auto/barry_video_state.json"
with open(path, "r") as f:
    state = json.load(f)

if "1FCxVbmXewAHCGSzPBQbC97_5wrJjaXRO" not in state["posted_drive_ids"]:
    state["posted_drive_ids"].append("1FCxVbmXewAHCGSzPBQbC97_5wrJjaXRO")

with open(path, "w") as f:
    json.dump(state, f, indent=2)

print("Updated state.")
