with open('tag.py', 'r') as f:
    content = f.read()

# Update run signature and limit parsing
content = content.replace(
    'def run(limit=None, daily=False, full_backfill=False):\n    if daily:\n        limit = 5000\n    if full_backfill:\n        limit = 10000',
    'def run(limit=None):\n    if not limit:\n        limit = 5000'
)

# Update main
main_old = '''if __name__ == "__main__":
    full = "--all" in sys.argv
    dry = "--dry-run" in sys.argv
    daily = "--daily" in sys.argv
    limit_arg = None
    for arg in sys.argv[1:]:
        if arg.isdigit():
            limit_arg = int(arg)
    run(limit=limit_arg, daily=daily, full_backfill=full)'''

main_new = '''if __name__ == "__main__":
    limit_arg = None
    for arg in sys.argv[1:]:
        if arg.isdigit():
            limit_arg = int(arg)
    if "--all" in sys.argv:
        limit_arg = 35000 # Just pull everything
    run(limit=limit_arg)'''

content = content.replace(main_old, main_new)

with open('tag.py', 'w') as f:
    f.write(content)
print("Applied fix_all3.py")
