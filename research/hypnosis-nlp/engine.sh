#!/bin/bash
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"

WORKDIR="$HOME/.openclaw/workspace/research/hypnosis-nlp"
cd "$WORKDIR" || { echo "ERROR: cannot cd to $WORKDIR"; exit 1; }

TODAY=$(date +%Y-%m-%d)
UPDATE_DIR="$WORKDIR/updates"
mkdir -p "$UPDATE_DIR"

echo "Waking up Holographic Engine for $TODAY..."

PROMPT_FILE="/tmp/claude_daily_hypnosis.txt"

cat << 'PROMPT' > "$PROMPT_FILE"
You are the Holographic Knowledge Engine for Hypnosis and NLP.
You must be CREATIVE and relentlessly curious. We only care about peer-reviewed research papers (no blogs, no junk).

Your tasks for today's ingest:
1. Read our current holographic understanding at ~/.openclaw/workspace/research/hypnosis-nlp/mesh.md and ~/.openclaw/workspace/research/hypnosis-nlp/hypotheses.md. 
2. Identify the "blank spots", the weirdest anomalies, or the most promising unanswered questions in the current mesh.
3. INVENT a highly specific, novel, creative search query to explore those gaps. (e.g. "hypnosis somatosensory cortex predictive coding", "hypnotic analgesia descending inhibition", "dissociation DMN connectivity anomaly").
4. Execute `python3 ~/.openclaw/workspace/research/hypnosis-nlp/fetch_papers.py "YOUR NOVEL QUERY HERE"` to fetch 3 brand new, peer-reviewed full-text XML papers.
5. Read the newly downloaded XML files in ~/.openclaw/workspace/research/hypnosis-nlp/papers/ (Check ~/.openclaw/workspace/research/hypnosis-nlp/staging_papers.md to see which PMCIDs are new today).
6. Evolve ~/.openclaw/workspace/research/hypnosis-nlp/mesh.md by integrating the new findings to increase its resolution. Focus on contradictions or "footnote phenomena" researchers brushed past.
7. Generate 1-3 new, highly specific, TESTABLE hypotheses based on the anomalies you found. Append them to ~/.openclaw/workspace/research/hypnosis-nlp/hypotheses.md.
8. Append the new citations to ~/.openclaw/workspace/research/hypnosis-nlp/sources.md.
9. Write your daily discovery report to ~/.openclaw/workspace/research/hypnosis-nlp/updates/$(date +%Y-%m-%d).md. 
   IMPORTANT: This file MUST clearly outline:
   - Section 1: "ANOMALIES & MISSED CONNECTIONS" (What did the researchers miss or ignore in today's papers?)
   - Section 2: "TESTABLE HYPOTHESIS" (What is the new hypothesis we can test based on this new resolution?)

Work completely autonomously using bash, grep, curl, etc. Do not stop until the updates file is written.
PROMPT

# Run Claude Code in the background to execute the daily creative prompt
claude --permission-mode bypassPermissions --add-dir "$WORKDIR" -p "$(cat $PROMPT_FILE)"

# Schedule a callback in OpenClaw to notify Robel exactly when it finishes
openclaw cron add --name "hypnosis-callback-$TODAY" --at "1m" --session "isolated" --agent "hypnosis" --system-event "CRON_CALLBACK: The Holographic Ingest for $TODAY is complete. Read the file ~/.openclaw/workspace/research/hypnosis-nlp/updates/$TODAY.md. Send a message to Robel titled '⚡ DAILY HYPNOSIS DISCOVERY REPORT' outlining the anomalies and testable hypotheses. Be direct and sharp. Route it to the Telegram AutoPax Group, Topic 943."

echo "Ingest loop complete. Engine is spinning down."
