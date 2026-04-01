#!/bin/bash
claude -p "You are running the Nightly Lead Gen Autoresearch Loop following Karpathy's empirical methodology.
1. Create notes/autoresearch_plan.md to store your intermediate thoughts, hypotheses, and benchmark results.
2. The target is sync_daily_optimized.py. Your goal is to optimize the 'Records processed per minute' (RPM) or DB upsert latency.
3. Run an evolutionary trial-and-error loop:
   - Hypothesize a code change.
   - Edit the code.
   - Run a short fixed-time test batch to measure the metric.
   - Evaluate against the baseline.
   - If it improves by >5%, keep it. Otherwise, revert the change.
4. Repeat this loop at least 5 times.
5. When finished, append a summary of your final benchmark improvement and the winning code changes to /Users/roba/.openclaw/workspace/memory/logs/2026-04-01.md." \
  --dangerously-skip-permissions \
  --max-turns 150 \
  --max-budget-usd 10.00
