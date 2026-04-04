#!/usr/bin/env python3
"""Lint the LLM Knowledge Base for a topic using Claude CLI.

Usage:
    wiki_lint.py --topic <name>

Finds inconsistent data, missing links, and suggests new article connections.
"""

import argparse
import subprocess
import sys
from pathlib import Path

RESEARCH_ROOT = Path(__file__).resolve().parent.parent / "research"


def collect_markdown(base: Path) -> str:
    parts = []
    for md in sorted(base.rglob("*.md")):
        rel = md.relative_to(base)
        try:
            text = md.read_text(errors="replace")
        except OSError:
            continue
        parts.append(f"--- {rel} ---\n{text}")
    return "\n\n".join(parts)


def run_claude(prompt: str, timeout: int = 300) -> str:
    result = subprocess.run(
        ["claude", "--print", "--dangerously-skip-permissions"],
        input=prompt,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        print(f"Claude CLI error: {result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout.strip()


def main():
    parser = argparse.ArgumentParser(description="Lint a knowledge base topic")
    parser.add_argument("--topic", required=True, help="Topic name under research/")
    args = parser.parse_args()

    topic_dir = RESEARCH_ROOT / args.topic
    if not topic_dir.is_dir():
        print(f"Topic not found: {args.topic}", file=sys.stderr)
        sys.exit(1)

    content = collect_markdown(topic_dir)
    if not content.strip():
        print(f"No markdown files found in {args.topic}/")
        sys.exit(0)

    # Also collect topic names for cross-reference suggestions
    all_topics = [d.name for d in sorted(RESEARCH_ROOT.iterdir()) if d.is_dir() and d.name != args.topic]

    prompt = f"""You are a knowledge-base quality auditor reviewing the '{args.topic}' topic.

Other topics in this knowledge base: {', '.join(all_topics)}

Below are ALL markdown files in this topic. Analyse them and report:

1. **Inconsistencies** — contradictory facts, outdated claims, conflicting numbers
2. **Missing internal links** — files that reference concepts covered in other files but don't link to them
3. **Cross-topic connections** — suggest links to other topics listed above where relevant
4. **Gaps** — important sub-topics mentioned but never elaborated
5. **Stale content** — anything that looks outdated or superseded

Format as a structured markdown report. Be specific — cite file names and quotes.

Files:
{content}"""

    print(f"Linting '{args.topic}' ({len(content)} chars across all files)...")
    report = run_claude(prompt)

    report_path = topic_dir / "LINT-REPORT.md"
    report_path.write_text(f"# Lint Report — {args.topic}\n\n{report}\n")
    print(f"\nReport saved to {report_path.relative_to(RESEARCH_ROOT)}")
    print(report)


if __name__ == "__main__":
    main()
