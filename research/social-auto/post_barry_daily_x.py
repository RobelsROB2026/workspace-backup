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

async def main():
    print("Starting daily Barry Hauler video post...")
    
    # 1. Load state
    state = load_state()
    
    # 2. Get sorted list of videos from Google Drive
    print("Fetching file list from Google Drive...")
    cmd = [
        "gws", "drive", "files", "list", 
        "--params", '{"q": "\\"11IjZBXaII_s67KZzFw8IF-HXSMuf4PW4\\" in parents and mimeType contains \\"video\\"", "fields": "files(id,name,createdTime,webViewLink)", "orderBy": "createdTime"}',
        "--format", "json"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        drive_data = json.loads(result.stdout)
        files = drive_data.get("files", [])
    except Exception as e:
        print(f"Error fetching from Drive: {e}")
        if hasattr(e, 'stderr'):
            print(f"Stderr: {e.stderr}")
        return
        
    if not files:
        print("No files found in Drive folder.")
        return
        
    # 3. Find oldest unposted
    next_vid = None
    for f in files:
        if f["id"] not in state["posted_drive_ids"]:
            next_vid = f
            break
            
    if not next_vid:
        print("All videos in the folder have been posted!")
        return
        
    vid_id = next_vid["id"]
    vid_name = next_vid["name"]
    print(f"Selected next video: {vid_name} (ID: {vid_id})")
    
    # 4. Download video
    sanitized_name = vid_name.replace(" ", "_")
    if not sanitized_name.endswith(".mp4"):
        sanitized_name += ".mp4"
    local_path = os.path.join(TEMP_DIR, sanitized_name)
    
    if not os.path.exists(local_path):
        print(f"Downloading {vid_name} from Drive...")
        dl_cmd = [
            "gws", "drive", "files", "get",
            "--params", f'{{"fileId": "{vid_id}", "alt": "media"}}',
            "--output", local_path
        ]
        subprocess.run(dl_cmd, check=True)
        print("Download complete.")
    else:
        print(f"File {sanitized_name} already exists locally.")
        
    # 5. Transcribe and generate caption using Gemini
    print("Generating caption via Gemini...")
    transcribe_script = f"""
import sys
import time
from google import genai
client = genai.Client()
video_file = client.files.upload(file="{local_path}")
while True:
    video_file = client.files.get(name=video_file.name)
    if video_file.state == 'ACTIVE':
        break
    if video_file.state == 'FAILED':
        print("Processing failed")
        sys.exit(1)
    time.sleep(5)
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents=[
        video_file,
        "Transcribe what the person in the video is saying. Then write a short, catchy Twitter caption (under 250 characters) based on the transcription. Make sure it highlights the country accent and 'Barry Hauler' trucking persona. DO NOT use the hashtag #truckersoftiktok. Use tags like #trucking @barryhauler. ONLY return the final caption text you want to post, nothing else. No markdown formatting, just the raw text."
    ]
)
print(response.text.strip())
"""
    with open("/tmp/temp_transcribe.py", "w") as f:
        f.write(transcribe_script)
        
    try:
        cap_result = subprocess.run(["python3.11", "/tmp/temp_transcribe.py"], capture_output=True, text=True, check=True)
        caption = cap_result.stdout.strip()
        print(f"Generated caption:\n{caption}")
    except Exception as e:
        print(f"Error generating caption: {e}")
        if hasattr(e, 'stderr'):
            print(f"Stderr: {e.stderr}")
        return
        
    # 6. Post to X via twikit
    print("Uploading to X via Twikit...")
    client = Client('en-US')
    try:
        client.load_cookies(COOKIES_FILE)
    except Exception as e:
        print(f"Failed to load twikit cookies: {e}")
        return
        
    try:
        media_id = await client.upload_media(
            local_path,
            wait_for_completion=True,
            media_category='tweet_video'
        )
        print(f"Media uploaded to X. ID: {media_id}")
        
        # Truncate caption if too long (Twitter limit is 280, leaving room for safety)
        if len(caption) > 270:
            caption = caption[:267] + "..."
        
        tweet = await client.create_tweet(
            text=caption,
            media_ids=[media_id]
        )
        print(f"Successfully posted! Tweet ID: {tweet.id}")
        print(f"URL: https://x.com/barryhauler/status/{tweet.id}")
        
        # 7. Update state
        state["posted_drive_ids"].append(vid_id)
        save_state(state)
        print("State updated.")
        
    except Exception as e:
        print(f"Failed to post to X: {e}")

if __name__ == "__main__":
    asyncio.run(main())
