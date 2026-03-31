#!/bin/bash
set -e

# Download the video
export VID_ID="1HueiSK3IZbkpimEleG6RW_tcYtB-lcOl"
export LOCAL_PATH="/tmp/openclaw/uploads/BARRYSADVENTURE.mp4"
export CAPTION="Whew! Just finished a cosmic run. These interdimensional routes ain't for the faint of heart, folks. Time to park this rig and get some shut-eye. Black Dog's got stories for lightyears! #trucking #CDLLife #truckerlore #blackdog @barryhauler"

echo "Downloading video $VID_ID..."
gws drive files get --params "{\"fileId\": \"$VID_ID\", \"alt\": \"media\"}" --output "$LOCAL_PATH" || true # If already exists, ignore error

# Write prep file for post_video_web.js
cat << JSON > ~/research/social-auto/barry_prepped_post.json
{
  "id": "$VID_ID",
  "name": "BARRYSADVENTURE.mp4",
  "url": "",
  "local_path": "$LOCAL_PATH",
  "caption": "$CAPTION"
}
JSON

echo "Posting to X..."
cd ~/research/social-auto
node post_video_web.js
