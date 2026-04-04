#!/usr/bin/env python3
"""Compile raw research into structured knowledge using Claude CLI.

Usage:
    wiki_compile.py --topic <name>

Reads research/<topic>/raw/*.md, sends them to Claude for summarisation,
and incrementally updates research/<topic>/notes/ and KNOWLEDGE.md.
"""

import argparse
import subprocess
import sys
from pathlib import Path

RESEARCH_ROOT = Path(__file__).resolve().parent.parent / "research"


def read_raw_files(topic_dir: Path) -> list[tuple[str, str]]:
    raw_dir = topic_dir / "raw"
    if not raw_dir.is_dir():
        return []
    files = []
    for f in sorted(raw_dir.glob("*.md")):
        files.append((f.name, f.read_text(errors="replace")))
    return files


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
    parser = argparse.ArgumentParser(description="Compile raw research into knowledge")
    parser.add_argument("--topic", required=True, help="Topic name under research/")
    args = parser.parse_args()

    topic_dir = RESEARCH_ROOT / args.topic
    if not topic_dir.is_dir():
        print(f"Topic not found: {args.topic}", file=sys.stderr)
        sys.exit(1)

    raw_files = read_raw_files(topic_dir)
    if not raw_files:
        print(f"No raw files in {topic_dir / 'raw'}/. Drop markdown files there first.")
        sys.exit(0)

    notes_dir = topic_dir / "notes"
    notes_dir.mkdir(exist_ok=True)
    knowledge_file = topic_dir / "KNOWLEDGE.md"

    # Build context from raw files
    raw_content = ""
    for name, content in raw_files:
        raw_content += f"\n\n--- FILE: {name} ---\n{content}"

    # Read existing knowledge for incremental update
    existing_knowledge = ""
    if knowledge_file.exists():
        existing_knowledge = knowledge_file.read_text(errors="replace")

    # Step 1: Generate per-file notes
    print(f"Summarising {len(raw_files)} raw file(s)...")
    notes_prompt = f"""You are a research assistant for the '{args.topic}' knowledge base.

Below are raw research files. For each file, produce a concise note (bullet points preferred)
capturing the key facts, decisions, and actionable insights.

Format your output as:
## <filename>
- bullet points

Raw files:
{raw_content}"""

    notes_output = run_claude(notes_prompt)
    notes_path = notes_dir / "compiled-notes.md"
    notes_path.write_text(f"# Compiled Notes — {args.topic}\n\n{notes_output}\n")
    print(f"  -> Wrote {notes_path.relative_to(RESEARCH_ROOT)}")

    # Step 2: Update KNOWLEDGE.md
    print("Updating KNOWLEDGE.md...")
    knowledge_prompt = f"""You are a research assistant maintaining the '{args.topic}' KNOWLEDGE.md file.

Existing KNOWLEDGE.md:
{existing_knowledge if existing_knowledge else '(empty — create from scratch)'}

New compiled notes:
{notes_output}

Task: Merge the new notes into the KNOWLEDGE.md. Keep it well-structured with headings.
Deduplicate, resolve conflicts (prefer newer info), and keep it concise.
Output ONLY the updated KNOWLEDGE.md content (no commentary)."""

    knowledge_output = run_claude(knowledge_prompt)
    knowledge_file.write_text(knowledge_output + "\n")
    print(f"  -> Updated {knowledge_file.relative_to(RESEARCH_ROOT)}")

    print("Done.")


if __name__ == "__main__":
    main()
