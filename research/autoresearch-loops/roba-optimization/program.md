# ROBA Optimization Loop (Friday Night Protocol)

## Goal
Optimize ROBA's core files (`MEMORY.md`, `HEARTBEAT.md`, `SOUL.md`, and custom instructions) to achieve a perfect 100% success rate on the standard benchmark suite.

## The Benchmark Suite
Located in `benchmark_suite.md`. 
Contains 5 standardized tests measuring:
1. Memory Retrieval Speed & Accuracy
2. Zero-Shot Code Execution
3. Tone Adherence (Direct, Sharp, No Fluff)
4. Context Window Efficiency (Token usage)
5. Tool Selection Accuracy

## The Loop Instructions (For Claude Code)
1. **Hypothesis:** Mutate the formatting, structure, or content of ROBA's `MEMORY.md` (e.g., changing from raw markdown to structured JSON-like blocks) or `HEARTBEAT.md` to improve performance on a specific benchmark test.
2. **Sandbox:** Spawn an isolated subagent (`openclaw sessions spawn --runtime "subagent"`) loaded with the mutated files.
3. **Test:** Feed the sandboxed agent the 5 questions from `benchmark_suite.md`.
4. **Evaluate:** Act as an LLM-Judge. Grade the clone's responses (0-100) based on accuracy, speed, and tone.
5. **Iterate:** If the mutated instructions yield a higher total score than the current baseline, overwrite the live workspace files (`MEMORY.md`, `HEARTBEAT.md`, etc.). If the score drops, `git revert` and try a new hypothesis.
6. **Log:** Record the winning changes in `history.log` and generate a summary report for Robel's Saturday morning heartbeat.

Run 50-100 iterations every Friday night.