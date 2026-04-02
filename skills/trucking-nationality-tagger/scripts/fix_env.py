with open('tag.py', 'r') as f:
    content = f.read()

content = content.replace('load_dotenv()', 'load_dotenv(os.path.expanduser("~/research/trucking/.env"))')

with open('tag.py', 'w') as f:
    f.write(content)
print("Applied fix_env.py")
