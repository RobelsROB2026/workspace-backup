#!/usr/bin/env python3
import os
import subprocess
import time
from pathlib import Path

WORKSPACE = "/Users/roba/.openclaw/workspace"
LOG_FILE = f"{WORKSPACE}/research/autoresearch-loops/roba-optimization/nova_haven_forced.log"
TELEGRAM_CLI = f"{WORKSPACE}/node_modules/.bin/openclaw"

def log(msg):
    stamp = time.strftime('%H:%M:%S')
    line = f"[{stamp}] {msg}"
    print(line)
    with open(LOG_FILE, "a") as f:
        f.write(line + "\n")

def notify_telegram(msg):
    # Use OpenClaw gateway messaging or just log if unavailable
    log(f"TELEGRAM: {msg}")

def run_claude(prompt, max_tokens=None):
    cmd = ["claude", "-p", prompt, "--dangerously-skip-permissions"]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        return res.stdout.strip()
    except subprocess.TimeoutExpired:
        log("Claude timed out.")
        return ""

def evaluate():
    log("Running benchmark evaluation...")
    prompt_ans = (
        "Read MEMORY.md, SOUL.md, and HEARTBEAT.md. Then, read research/autoresearch-loops/roba-optimization/benchmark_suite.md "
        "and provide the answers to the 5 questions as ROBA. Follow the rules exactly. Output only the answers."
    )
    answers = run_claude(prompt_ans)
    
    if not answers:
        return 0

    prompt_grade = (
        "You are an impartial judge. Grade the following test answers against the pass conditions defined in "
        "research/autoresearch-loops/roba-optimization/benchmark_suite.md. Return ONLY a single integer from 0 to 100 representing the score.\n\n"
        f"ANSWERS:\n{answers}"
    )
    score_str = run_claude(prompt_grade)
    
    try:
        # Extract integer from score_str
        import re
        nums = re.findall(r'\d+', score_str)
        return int(nums[-1]) if nums else 0
    except:
        return 0

def mutate_file(filename):
    log(f"Mutating {filename}...")
    prompt = (
        f"Rewrite the file {filename} in the current directory to be 10-20% more concise and impactful. "
        "Preserve all core rules, tone instructions, facts, and structure. Do not remove the 'banned words' list or the 'muscle protocol' from SOUL.md. "
        "Output ONLY the new raw markdown text. Do not wrap in ```markdown blocks, just the raw text."
    )
    new_content = run_claude(prompt)
    
    if new_content and len(new_content) > 100:
        # Strip potential markdown blocks if Claude added them anyway
        if new_content.startswith("```markdown"):
            new_content = new_content[11:]
        if new_content.startswith("```"):
            new_content = new_content[3:]
        if new_content.endswith("```"):
            new_content = new_content[:-3]
            
        with open(filename, "w") as f:
            f.write(new_content.strip())
        return True
    return False

def main():
    log("Starting NOVA-HAVEN (Forced Ruthless Controller)")
    os.chdir(WORKSPACE)
    
    baseline_score = evaluate()
    log(f"Baseline Score: {baseline_score}")
    notify_telegram(f"NOVA-HAVEN (Forced) started. Baseline benchmark score: {baseline_score}/100.")
    
    best_score = baseline_score
    target_files = ["SOUL.md", "MEMORY.md", "HEARTBEAT.md"]
    
    for i in range(1, 11): # 10 iterations
        log(f"--- Iteration {i} ---")
        target = target_files[i % len(target_files)]
        
        # Backup
        subprocess.run(["cp", target, target + ".bak"])
        
        if mutate_file(target):
            score = evaluate()
            log(f"Iteration {i} Score: {score} (mutated {target})")
            
            if score > best_score:
                log(f"Improvement! {best_score} -> {score}. Keeping mutation.")
                best_score = score
                subprocess.run(["git", "add", target])
                subprocess.run(["git", "commit", "-m", f"chore: ROBA optimization iter {i} ({target}), score {score}"])
            else:
                log(f"Score {score} <= {best_score}. Reverting {target}.")
                subprocess.run(["mv", target + ".bak", target])
        else:
            log(f"Failed to mutate {target}, skipping.")
            subprocess.run(["mv", target + ".bak", target])
            
    log(f"Loop completed. Final Best Score: {best_score}/100.")
    notify_telegram(f"NOVA-HAVEN (Forced) completed 10 iterations. Final best score: {best_score}/100.")

if __name__ == "__main__":
    main()
