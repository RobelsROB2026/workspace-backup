import os
import subprocess

with open('tag_backfill.log', 'w') as f:
    f.write("Starting massive 35k backfill\\n")

proc = subprocess.Popen(
    ["python3", "tag.py", "--all"],
    stdout=open('tag_backfill.log', 'a'),
    stderr=subprocess.STDOUT
)
print(f"Background backfill started with PID {proc.pid}")
