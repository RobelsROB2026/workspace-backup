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

---

## Things to Remember

- OpenClaw browser works without the Chrome extension (use profile: openclaw)
- Peekaboo needs Screen Recording permission for UI automation
- Mac mini is at home, Robel sometimes away

### Model Setup (2026-02-06)
- **Main chat:** Gemini 3 Pro Preview (switched from Opus for speed/cost)
- **Heartbeats:** Gemini 3 Flash Preview (better benchmarks than Sonnet, 6x cheaper)
- **Sub-agents:** Gemini 3 Flash Preview (configured default)
- **Research synthesis:** Gemini 3 Flash Preview via CLI (bulk processing)
- **Search result analysis:** Gemini 3 Flash Preview (don't burn Pro tokens on raw data)
- **Image Generation:** Nano Banana Pro (Gemini 3 Pro Image)
- **Web search:** OpenClaw browser (profile: openclaw)

---

## My Resources

- **My email:** robake2006@gmail.com (for account signups, etc.)
- **Google account:** robake2006@gmail.com (Chrome)
- **X account:** @RobelAlema63562 (linked to Google, created 2026-02-04)
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
