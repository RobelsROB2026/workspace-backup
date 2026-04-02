with open('tag.py', 'r') as f:
    content = f.read()

# For a 35k backfill, fetch everything but maybe just process 5k at a time?
# Actually, the 2 hour timeout hit because 35k took too long.
content = content.replace('limit = None if full_backfill else (5000 if daily else BATCH_SIZE)', 'limit = 10000 if full_backfill else (5000 if daily else BATCH_SIZE)')

with open('tag.py', 'w') as f:
    f.write(content)
