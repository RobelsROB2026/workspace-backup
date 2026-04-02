with open('tag.py', 'r') as f:
    content = f.read()

# Change it to process max 5000 leads on daily run, not all of them
content = content.replace(
    'limit = None if full_backfill or daily else BATCH_SIZE',
    'limit = None if full_backfill else (5000 if daily else BATCH_SIZE)'
)

with open('tag.py', 'w') as f:
    f.write(content)
print("Applied fix_limit.py")
