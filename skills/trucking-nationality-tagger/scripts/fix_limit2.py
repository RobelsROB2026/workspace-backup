with open('tag.py', 'r') as f:
    content = f.read()

# Make sure --all actually uses batching internally and doesn't get stuck processing 35k at once
# Actually, the batching is already there: batches = [rows[i:i+BATCH_SIZE] for i in range...]
# Let's add more logs
content = content.replace('print(flush=True, f"Firing up to {MAX_WORKERS}', 'print(flush=True, "Generating batches...");\n    print(flush=True, f"Firing up to {MAX_WORKERS}')

with open('tag.py', 'w') as f:
    f.write(content)
