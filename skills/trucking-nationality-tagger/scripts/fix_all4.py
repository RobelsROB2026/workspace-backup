with open('tag.py', 'r') as f:
    content = f.read()

# Fix limit behavior for None
content = content.replace(
    'def run(limit=None):\n    if not limit:\n        limit = 5000',
    'def run(limit=None):\n    if limit is None:\n        limit = 5000'
)

with open('tag.py', 'w') as f:
    f.write(content)
print("Applied fix_all4.py")
