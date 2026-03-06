with open('/Users/roba/research/trucking/sync_daily_v2.py', 'r') as f:
    content = f.read()

content = content.replace(
    'companies_to_insert.append((',
    '# Avoid dupes\n                dot_val = c.get("dot_number")\n                if not any(d[0] == dot_val for d in companies_to_insert):\n                    companies_to_insert.append(('
)

with open('/Users/roba/research/trucking/sync_daily_v2.py', 'w') as f:
    f.write(content)
