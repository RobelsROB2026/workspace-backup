#!/bin/bash
set -e

# Download the video
export VID_ID="1Gzi3IzQftHEenC1soMf1OpekXMwR-0Ob"
export LOCAL_PATH="/tmp/openclaw/uploads/THEDAYHEALMOSTDIED.mp4"
export CAPTION="That's the sound of the road callin', and Barry Hauler answerin'! Every breath, every rumble, fueled by adventure. Get ready for a wild ride!  #trucking #CDLLife #truckerlore #blackdog @barryhauler"

echo "Downloading video $VID_ID..."
gws drive files get --params "{\"fileId\": \"$VID_ID\", \"alt\": \"media\"}" --output "$LOCAL_PATH"

# Write prep file for post_video_web.js
cat << JSON > ~/research/social-auto/barry_prepped_post.json
{
  "id": "$VID_ID",
  "name": "THE DAY HE ALMOST DIED.mp4",
  "url": "",
  "local_path": "$LOCAL_PATH",
  "caption": "$CAPTION"
}
JSON

echo "Posting to X..."
cd ~/research/social-auto
node post_video_web.js
