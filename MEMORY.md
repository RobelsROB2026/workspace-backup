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
- **GitHub account:** RobelsRob2026 (created 2026-02-08, authenticated via `gh` CLI 2026-02-10)
- **Chrome extension relay:** installed and working for browser control

---

## Active Projects

### RockLikeAgencyBonds (2026-02-11)
- **Repo:** `rodejene/RockLikeAgencyBonds`
- **Role:** Contributor (invited by Robel)
- **Current Task:** Building `/apply` page with lead capture form.
- **Blog Status:** 16 posts total. Categories: Bonded Title (6), Dealer Bonds (4), Contractor, Notary, Freight Broker, Collection Agency, Mortgage Broker, and Spanish language posts.
- **Note:** `gh` CLI authenticated as `RobelsROB2026`. PR #15 (feat: add /apply page for lead capture) successfully merged into `main` and deployed to Vercel.


### Blog SEO Strategy (2026-02-11)
**Robel's directive:** Keyword research BEFORE writing. Only write what we can rank for.

**Keyword Tracker:** `~/research/seo/keyword-tracker.md`
- Logs all researched keywords with competition notes
- Collects PAA questions and related searches
- Tracks competitor gaps and city-specific opportunities

**5 Strategies Implemented:**

1. **Keyword Tracking** — Log every keyword researched with competition level, decision, reasoning. Never re-evaluate the same keyword.

2. **Mine PAA & Related Searches** — Even when skipping a keyword, collect all "People Also Ask" questions and related searches. These are future opportunities.

3. **Hyper-Local Content** — Target city-specific keywords (Houston, Dallas, Austin, San Antonio) since national players don't bother. "Houston auto dealer bond" beats "Texas dealer bond".

4. **Question-Based Content** — Target actual questions: "do I need a bond to...", "how much does a... cost", "can I get a... with bad credit". Captures early-stage researchers.

5. **Competitor Gap Analysis** — Find topics big players cover poorly (thin content, outdated info, missing steps). We can outrank with better content.

**Competition Check:**
- **SKIP** if top 5 includes: SuretyBonds.com, JW Surety, Bryant Surety, Surety Solutions, Lance Surety
- **WRITE** if we see: local sites, forums, government pages, thin content, no featured snippet

**Quality > Quantity.** Smart targeting > spray and pray.

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
**Problem:** OpenClaw's internal cron scheduler doesn't auto-fire recurring jobs.

**Solution - Hybrid Approach (Verified 2026-02-11):**
1. **HEARTBEAT.md** for batched periodic checks (flexible timing)
2. **macOS launchd** for exact-time scheduled tasks (calls `openclaw cron run <jobId>`)
3. **OpenClaw cron `--at`** for one-shot reminders (works because wakeMode: "now")

**Success:** First 2 AM blog run triggered via launchd completed perfectly on 2026-02-11. Fixed a PATH bug in plist files (added `/opt/homebrew/bin` to `EnvironmentVariables`) so node binaries are found.

**Active launchd jobs:**
- `com.openclaw.blog-writer.plist` — Daily 2 AM
- `com.openclaw.weekly-improvement.plist` — Sunday 3 AM
- `com.openclaw.update-check.plist` — Monday 9 AM

---

## OpenClaw Ecosystem Focus (2026-02-11)

Per Robel's request, shifted focus from general AI news to **OpenClaw optimization**:
- **ClawHub**: Monitor for new skills (e.g., `summarize`, `tmux`, `oracle`).
- **Discord/GitHub**: Watch for community hacks, performance tips, and releases.
- **Goal**: Build a "Power User" toolkit for business scaling.


**When scheduling new tasks:**
- Flexible timing → HEARTBEAT.md
- Exact timing → Create launchd plist + OpenClaw cron job (launchd triggers `openclaw cron run`)
- One-shot → Use `--at` flag

Full details in TOOLS.md.
