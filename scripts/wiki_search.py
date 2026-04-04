#!/usr/bin/env python3
"""Fast text/regex search over the LLM Knowledge Base markdown files.

Usage:
    wiki_search.py <pattern> [--topic <name>] [--ignore-case]

--topic restricts search to research/<name>/ (subagent mode).
Without --topic, searches all of research/ (global ROBA mode).
"""

import argparse
import re
import sys
from pathlib import Path

RESEARCH_ROOT = Path(__file__).resolve().parent.parent / "research"


def search_files(pattern: re.Pattern, base: Path):
    hits = []
    for md in sorted(base.rglob("*.md")):
        try:
            text = md.read_text(errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                hits.append((md.relative_to(RESEARCH_ROOT), i, line.rstrip()))
    return hits


def main():
    parser = argparse.ArgumentParser(description="Search the LLM Knowledge Base")
    parser.add_argument("pattern", help="Text or regex pattern to search for")
    parser.add_argument("--topic", help="Restrict search to research/<topic>/")
    parser.add_argument("-i", "--ignore-case", action="store_true")
    args = parser.parse_args()

    flags = re.IGNORECASE if args.ignore_case else 0
    try:
        pat = re.compile(args.pattern, flags)
    except re.error as e:
        print(f"Invalid regex: {e}", file=sys.stderr)
        sys.exit(1)

    if args.topic:
        base = RESEARCH_ROOT / args.topic
        if not base.is_dir():
            print(f"Topic not found: {args.topic}", file=sys.stderr)
            print(f"Available: {', '.join(d.name for d in sorted(RESEARCH_ROOT.iterdir()) if d.is_dir())}", file=sys.stderr)
            sys.exit(1)
    else:
        base = RESEARCH_ROOT

    hits = search_files(pat, base)

    if not hits:
        print("No matches.")
        sys.exit(0)

    for path, lineno, line in hits:
        print(f"{path}:{lineno}: {line}")

    print(f"\n{len(hits)} match(es) found.")


if __name__ == "__main__":
    main()
