import subprocess
import os
import sys

def run_cmd(cmd):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

if len(sys.argv) < 2:
    print("Usage: python repost_missing.py <1|2>")
    sys.exit(1)

post_num = sys.argv[1]

if post_num == "1":
    # The Day He Almost Died
    vid_id = "1Gzi3IzQftHEenC1soMf1OpekXMwR-0Ob"
    local_path = "/tmp/openclaw/uploads/THEDAYHEALMOSTDIED.mp4"
    caption = "That's the sound of the road callin', and Barry Hauler answerin'! Every breath, every rumble, fueled by adventure. Get ready for a wild ride!  #trucking #CDLLife #truckerlore #blackdog"
elif post_num == "2":
    # Barry's Adventure
    vid_id = "1HueiSK3IZbkpimEleG6RW_tcYtB-lcOl"
    local_path = "/tmp/openclaw/uploads/BARRYSADVENTURE.mp4"
    caption = "Whew! Just finished a cosmic run. These interdimensional routes ain't for the faint of heart, folks. Time to park this rig and get some shut-eye. Black Dog's got stories for lightyears! #trucking #CDLLife #truckerlore #blackdog"
else:
    print("Invalid post num")
    sys.exit(1)

# Download if not exists
if not os.path.exists(local_path):
    print(f"Downloading {vid_id} to {local_path}...")
    run_cmd([
        "gws", "drive", "files", "get",
        "--params", f'{{"fileId": "{vid_id}", "alt": "media"}}',
        "--output", local_path
    ])

# Compress using ffmpeg to ensure compatibility for X
final_path = local_path.replace(".mp4", "_compressed.mp4")
if not os.path.exists(final_path):
    print("Compressing video...")
    run_cmd([
        "ffmpeg", "-y", "-i", local_path,
        "-c:v", "libx264", "-preset", "fast", "-crf", "28",
        "-c:a", "aac", "-b:a", "128k", "-strict", "-2",
        final_path
    ])

# Write caption to env var for Node script
os.environ["BARRY_CAPTION"] = caption
os.environ["BARRY_VIDEO_PATH"] = final_path

# Run the web posting script
node_script = "/Users/roba/research/social-auto/post_video_web_repost.js"

with open(node_script, "w") as f:
    f.write("""
const { chromium } = require('playwright-extra');
const stealth = require('puppeteer-extra-plugin-stealth')();
chromium.use(stealth);

(async () => {
  const caption = process.env.BARRY_CAPTION;
  const videoPath = process.env.BARRY_VIDEO_PATH;
  
  console.log(`Posting: ${caption}`);
  console.log(`Video: ${videoPath}`);
  
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  
  // Load cookies
  const fs = require('fs');
  const cookiesPath = '/tmp/openclaw/uploads/twikit_cookies.json';
  if (fs.existsSync(cookiesPath)) {
    const rawCookies = JSON.parse(fs.readFileSync(cookiesPath, 'utf8'));
    let formattedCookies = [];
    if (!Array.isArray(rawCookies)) {
      for (const [name, value] of Object.entries(rawCookies)) {
        formattedCookies.push({ name: name, value: String(value), domain: '.twitter.com', path: '/' });
        formattedCookies.push({ name: name, value: String(value), domain: '.x.com', path: '/' });
      }
    } else {
      formattedCookies = rawCookies;
    }
    await context.addCookies(formattedCookies);
  }

  const page = await context.newPage();
  await page.goto('https://x.com/home');
  await page.waitForTimeout(5000);
  
  // Try to click the compose area
  const composeArea = await page.$('div[data-testid="tweetTextarea_0"]');
  if (composeArea) {
    await composeArea.click();
    await page.waitForTimeout(1000);
    // Type the text naturally
    for (const char of caption) {
        await page.keyboard.press(char);
        await page.waitForTimeout(Math.random() * 50 + 10);
    }
    
    // Upload video
    const fileChooserPromise = page.waitForEvent('filechooser');
    await page.click('div[aria-label="Add media"]');
    const fileChooser = await fileChooserPromise;
    await fileChooser.setFiles(videoPath);
    console.log("Attached video.");
    
    // Wait for upload progress
    await page.waitForTimeout(15000);
    
    // Click Post
    const postBtn = await page.$('button[data-testid="tweetButtonInline"]');
    if (postBtn) {
      await postBtn.click();
      console.log("Clicked Post button!");
      await page.waitForTimeout(10000);
    } else {
      console.log("Could not find Post button!");
    }
  } else {
    console.log("Could not find compose area.");
  }
  
  await browser.close();
})();
""")

run_cmd(["node", node_script])
