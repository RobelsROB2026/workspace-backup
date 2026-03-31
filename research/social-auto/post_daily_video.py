import json
import os
import subprocess

PREP_FILE = os.path.expanduser("~/research/social-auto/barry_prepped_post.json")
X_POSTER_SKILL = os.path.expanduser("~/.openclaw/workspace/skills/x-poster/x-poster.js")
FINAL_COMPRESSED = "/tmp/openclaw/uploads/barry_final_upload.mp4"

def main():
    if not os.path.exists(PREP_FILE):
        print("Prep file missing. Cannot post.")
        return
        
    with open(PREP_FILE, "r") as f:
        prepped = json.load(f)
        
    source_path = prepped["local_path"]
    caption = prepped["caption"]

    print(f"Compressing video {source_path} to {FINAL_COMPRESSED}...")
    
    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", source_path, 
        "-vcodec", "libx264", "-crf", "32", 
        "-preset", "veryfast", "-vf", "scale=720:-2", 
        "-acodec", "aac", FINAL_COMPRESSED
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"FFMPEG Error: {e.stderr}")
        return
        
    print(f"Video compressed. Initiating Web UI upload via x-poster skill...")
    
    # Run Playwright Web UI script from the x-poster skill
    result = subprocess.run(["node", X_POSTER_SKILL, caption, FINAL_COMPRESSED], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Error Output:", result.stderr)

    if result.returncode == 0:
        # Update state
        STATE_FILE = os.path.expanduser("~/research/social-auto/barry_video_state.json")
        vidId = prepped["id"]
        
        state = {"posted_drive_ids": []}
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                
        if vidId not in state["posted_drive_ids"]:
            state["posted_drive_ids"].append(vidId)
            with open(STATE_FILE, "w") as f:
                json.dump(state, f, indent=2)
                
        # Clean up prep file so it doesn't double post
        os.remove(PREP_FILE)
        print("Successfully posted to X and updated state!")
    else:
        print("Failed to post.")

if __name__ == "__main__":
    main()
