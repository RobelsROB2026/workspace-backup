import json
import os
import subprocess

STATE_FILE = os.path.expanduser("~/research/social-auto/barry_video_state.json")
TEMP_DIR = "/tmp/openclaw/uploads"
PREP_FILE = os.path.expanduser("~/research/social-auto/barry_prepped_post.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {"posted_drive_ids": [], "last_run": None}

def main():
    state = load_state()
    
    cmd = [
        "gws", "drive", "files", "list", 
        "--params", '{"q": "\\"11IjZBXaII_s67KZzFw8IF-HXSMuf4PW4\\" in parents and mimeType contains \\"video\\"", "fields": "files(id,name,createdTime,webViewLink)", "orderBy": "createdTime"}',
        "--format", "json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    drive_data = json.loads(result.stdout)
    files = drive_data.get("files", [])
    
    next_vid = None
    for f in files:
        if f["id"] not in state["posted_drive_ids"]:
            next_vid = f
            break
            
    if not next_vid:
        print("NO_VIDEOS_LEFT")
        return
        
    vid_id = next_vid["id"]
    vid_name = next_vid["name"]
    vid_url = next_vid["webViewLink"]
    
    # Download for caption gen
    import re
    clean_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '', vid_name)
    if not clean_name.endswith('.mp4'):
        clean_name += '.mp4'
    local_path = os.path.join(TEMP_DIR, clean_name)
    if not os.path.exists(local_path):
        dl_cmd = [
            "gws", "drive", "files", "get",
            "--params", f'{{"fileId": "{vid_id}", "alt": "media"}}',
            "--output", local_path
        ]
        subprocess.run(dl_cmd, check=True)
        
    transcribe_script = f"""
import sys
import time
from google import genai
client = genai.Client()
video_file = client.files.upload(file="{local_path}", config={{"mime_type": "video/mp4"}})
while True:
    video_file = client.files.get(name=video_file.name)
    if video_file.state == 'ACTIVE':
        break
    if video_file.state == 'FAILED':
        sys.exit(1)
    time.sleep(5)
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[
        video_file,
        "Transcribe what the person in the video is saying. Then write a short, catchy Twitter caption (under 250 characters) based on the transcription. Make sure it highlights the country accent and 'Barry Hauler' trucking persona. Use tags like #trucking #CDLLife #truckerlore #blackdog @barryhauler. ONLY return the final caption text you want to post, nothing else. No markdown formatting, just the raw text."
    ]
)
print(response.text.strip())
"""
    with open("/tmp/temp_transcribe.py", "w") as f:
        f.write(transcribe_script)
        
    cap_result = subprocess.run(["python3.11", "/tmp/temp_transcribe.py"], capture_output=True, text=True, check=True)
    caption = cap_result.stdout.strip()
    
    prepped_data = {
        "id": vid_id,
        "name": vid_name,
        "url": vid_url,
        "local_path": local_path,
        "caption": caption
    }
    
    with open(PREP_FILE, "w") as f:
        json.dump(prepped_data, f, indent=2)
        
    print(json.dumps(prepped_data, indent=2))

if __name__ == "__main__":
    main()
