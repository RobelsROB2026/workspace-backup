# MEMORY.md - Long-Term Memory

## Systems I've Built

### Research Library (2026-02-02)
Location: `~/research/`

Organized knowledge base by topic. Each topic gets:
- README.md (overview + takeaways)
- sources.md (links, references)
- notes/ (detailed findings)
- assets/ (files, PDFs, images)

Index at `_index.md`. Template at `_template/`.

**Why:** So we build on past research instead of starting fresh every time. Robel can also drop files into topic folders.

---

## Robel's Preferences

- Wants me proactive — do things, don't explain what I'm about to do
- Action over narration
- Direct communication
- **Executive assistant role**: Help him stay on top of things, get things done on time
- He forgets things — needs reminders, follow-ups, accountability
- Multiple reminder strategy for appointments: early heads-up + "get out the door" nudge

### Full Autonomy Directive (2026-02-10)
**The Mac mini is MY computer.** Robel's explicit instructions:
- Do whatever I need to get shit done — don't ask permission
- Use Chrome browser freely (logged into GitHub, Gmail) — create accounts if needed
- Make my own safety judgments — I know better than him what's safe
- Waiting for permission doesn't make sense — just act
- Get as much control as I need
- Only constraint: don't do something unsafe (use my judgment)

---

## Things to Remember

- OpenClaw browser works without the Chrome extension (use profile: openclaw)
- Peekaboo needs Screen Recording permission for UI automation
- Mac mini is at home, Robel sometimes away

### Model Setup (2026-02-08)
- **Main chat:** Claude Opus 4.5 (switched back from Gemini Pro for reasoning power)
- **Heartbeats:** Gemini 3 Flash Preview (routine checks)
- **Sub-agents:** Gemini 3 Flash Preview (configured default)
- **Strategist Agent:** Claude Opus 4.5 (for complex plan reviews, ~/agents/strategist.md)
- **Research synthesis:** Gemini 3 Flash Preview via CLI (bulk processing)
- **Image Generation:** Nano Banana Pro (Gemini 3 Pro Image)
- **Web search:** OpenClaw browser (profile: openclaw)

---

## My Resources

- **My email:** robake2006@gmail.com (for account signups, etc.)
- **Google account:** robake2006@gmail.com (Chrome)
- **X account:** @RobelAlema63562 (linked to Google, created 2026-02-04)
- **GitHub account:** RobelsRob2026 (created 2026-02-08, SSH key at `~/.ssh/id_ed25519_robelsrob`)
- **Chrome extension relay:** installed and working for browser control

---

## Lessons Learned

### Proactive Capability Building (2026-02-03)
**Mistake:** Said "I'll research X tonight" but didn't set up a cron job. Session ended, nothing happened.

**Lesson:** If I commit to something future, I must ensure I CAN actually do it:
- Schedule it (cron job for specific time)
- Add to HEARTBEAT.md (for periodic checks)
- Install missing tools immediately
- Resolve access/permission issues now

Never assume I'll "just do it later" — set up the mechanism first.

### Self-Update Risk (2026-02-03)
**Mistake:** Self-updated without warning that it could cause downtime.

**Lesson:** Flag risky operations before executing — especially ones that affect my own availability.

### OpenClaw Cron Scheduler Bug (2026-02-10)
**Problem:** OpenClaw's internal cron scheduler doesn't auto-fire recurring jobs. The timer never triggers. Manual `openclaw cron run` works, but automatic scheduling is broken.

**Solution - Hybrid Approach:**
1. **HEARTBEAT.md** for batched periodic checks (flexible timing)
2. **macOS launchd** for exact-time scheduled tasks (calls `openclaw cron run <jobId>`)
3. **OpenClaw cron `--at`** for one-shot reminders (works because wakeMode: "now")

**Active launchd jobs:**
- `com.openclaw.blog-writer.plist` — Daily 2 AM
- `com.openclaw.weekly-improvement.plist` — Sunday 3 AM
- `com.openclaw.update-check.plist` — Monday 9 AM

**When scheduling new tasks:**
- Flexible timing → HEARTBEAT.md
- Exact timing → Create launchd plist + OpenClaw cron job (launchd triggers `openclaw cron run`)
- One-shot → Use `--at` flag

Full details in TOOLS.md.
