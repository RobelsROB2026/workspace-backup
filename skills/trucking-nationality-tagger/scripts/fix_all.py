import re

with open('tag.py', 'r') as f:
    content = f.read()

# Add NotApplicable to tags_to_check
content = content.replace(
    'nationality_check = " AND ".join([f"NOT (COALESCE(l.tags, \'{{}}\') @> ARRAY[\'{n}\'])" for n in NATIONALITIES])',
    'tags_to_check = NATIONALITIES + ["NotApplicable"]\n    nationality_check = " AND ".join([f"NOT (COALESCE(l.tags, \'{{}}\') @> ARRAY[\'{n}\'])" for n in tags_to_check])'
)

# Update run signature and limit parsing
content = content.replace(
    'def run(limit=None):',
    'def run(limit=None, daily=False, full_backfill=False):\n    if daily:\n        limit = 5000\n    if full_backfill:\n        limit = 10000'
)

content = content.replace(
    'def fetch_leads(conn, limit=None):',
    'def fetch_leads(conn, limit=None, daily=False):'
)

content = content.replace(
    'rows = fetch_leads(conn, limit=limit)',
    'rows = fetch_leads(conn, limit=limit, daily=daily)'
)

# Update SQL to use daily
sql_old = '''        WHERE ({nationality_check})
          AND (c.legal_name IS NOT NULL OR c.email IS NOT NULL)
        ORDER BY l.created_at DESC
        {limit_clause};'''

sql_new = '''        WHERE ({nationality_check})
          AND (c.legal_name IS NOT NULL OR c.email IS NOT NULL)
          {daily_clause}
        ORDER BY l.created_at DESC
        {limit_clause};'''

content = content.replace(sql_old, sql_new)

content = content.replace(
    'limit_clause = f"LIMIT {limit}" if limit else ""',
    'limit_clause = f"LIMIT {limit}" if limit else ""\n    daily_clause = "AND l.created_at >= CURRENT_DATE - INTERVAL \'3 days\'" if daily else ""'
)

# Update main
main_old = '''if __name__ == "__main__":
    limit_arg = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    run(limit=limit_arg)'''

main_new = '''if __name__ == "__main__":
    full = "--all" in sys.argv
    dry = "--dry-run" in sys.argv
    daily = "--daily" in sys.argv
    limit_arg = None
    for arg in sys.argv[1:]:
        if arg.isdigit():
            limit_arg = int(arg)
    run(limit=limit_arg, daily=daily, full_backfill=full)'''

content = content.replace(main_old, main_new)

# Fix process_batch to insert NotApplicable
# First, look for the results parsing
process_old = '''            results = json.loads(raw)
            match_count = 0
            for item in results:
                nat = item.get("nationality")
                if nat and nat in NATIONALITIES:
                    write_queue.put((item["id"], nat))
                    match_count += 1
            return batch_num, match_count'''

process_new = '''            results = json.loads(raw)
            match_count = 0
            for item in results:
                nat = item.get("nationality")
                if not nat or nat == "null":
                    nat = "NotApplicable"
                if nat in NATIONALITIES or nat == "NotApplicable":
                    write_queue.put((item["id"], nat))
                    match_count += 1 if nat != "NotApplicable" else 0
            return batch_num, match_count'''

content = content.replace(process_old, process_new)

# Add load_dotenv properly
content = content.replace(
    'load_dotenv(os.path.expanduser("~/research/trucking/.env"))',
    '''load_dotenv(os.path.expanduser("~/research/trucking/.env"))\n\nif not os.getenv("DATABASE_URL"):\n    load_dotenv(os.path.expanduser("~/.openclaw/workspace/projects/AutoPax-Trucking-CRM/.env.local"))'''
)

with open('tag.py', 'w') as f:
    f.write(content)
print("Applied fix_all.py")
