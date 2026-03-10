# Gateway Restart Protocol

**MANDATORY CHECKLIST** before executing `openclaw gateway restart`, `stop`, or `install --force`.

## 1. Check Active Work
- [ ] **Running Processes:** Use the `process` tool (`action: "list"`) to ensure no long-running terminal commands (like Claude Code, scrapers, or ETL pipelines) are currently executing.
- [ ] **Subagents:** Check if any subagents are mid-task. If yes, wait for completion or gracefully pause them.

## 2. Check Scheduled Tasks
- [ ] **Impending Cron Jobs:** Run `openclaw cron list` (or check `HEARTBEAT.md`) for tasks scheduled in the next 5-10 minutes.
- [ ] **Action:** If a scheduled task is imminent, either wait for it to finish OR manually trigger it before restarting so the trigger isn't missed during the downtime window.

## 3. Prevent Restart Failures (Pre-flight)
- [ ] **Config Health:** Run `openclaw doctor` to ensure there are no fatal syntax errors in `openclaw.json` or channel configs that would prevent the gateway from booting back up.
- [ ] **Port Conflicts:** Ensure no ghost processes are hung (`ps aux | grep openclaw`) that might block the restart.

## 4. Execution (The Detached Method)
- [ ] **Never run synchronously.** The restart script must survive the death of the parent OpenClaw process.
- [ ] **Required Command Format:**
  `nohup bash -c 'sleep 5 && openclaw gateway restart' > /tmp/gateway_restart.log 2>&1 &`
  *(Must use `background: true` if using the `exec` tool).*
- [ ] **Communication:** Send a final message to Robel confirming the restart sequence has begun and all checks passed.
