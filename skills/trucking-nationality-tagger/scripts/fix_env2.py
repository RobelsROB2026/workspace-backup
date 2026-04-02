import re
with open('tag.py', 'r') as f:
    content = f.read()

content = content.replace('DATABASE_URL = os.getenv("DATABASE_URL")', 'DATABASE_URL = os.getenv("DATABASE_URL") or os.environ.get("DATABASE_URL")\nif not DATABASE_URL:\n    load_dotenv(os.path.expanduser("~/.openclaw/workspace/projects/AutoPax-Trucking-CRM/.env.local"))\n    DATABASE_URL = os.getenv("DATABASE_URL")')

with open('tag.py', 'w') as f:
    f.write(content)
print("Applied fix_env2.py")
