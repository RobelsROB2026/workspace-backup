with open('tag.py', 'r') as f:
    content = f.read()

# Remove daily_clause logic completely
content = content.replace(
    'def fetch_leads(conn, limit=None, daily=False):',
    'def fetch_leads(conn, limit=None):'
)

content = content.replace(
    'rows = fetch_leads(conn, limit=limit, daily=daily)',
    'rows = fetch_leads(conn, limit=limit)'
)

content = content.replace(
    'limit_clause = f"LIMIT {limit}" if limit else ""\n    daily_clause = "AND l.created_at >= CURRENT_DATE - INTERVAL \'3 days\'" if daily else ""',
    'limit_clause = f"LIMIT {limit}" if limit else ""\n    daily_clause = ""'
)

with open('tag.py', 'w') as f:
    f.write(content)
