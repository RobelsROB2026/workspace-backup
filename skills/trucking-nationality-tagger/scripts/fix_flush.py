with open('tag.py', 'r') as f:
    content = f.read()

# Make sure print is flushed so we can see the logs immediately
content = content.replace('print(', 'print(flush=True, ')

with open('tag.py', 'w') as f:
    f.write(content)
print("Applied fix_flush.py")
