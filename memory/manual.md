# ROBA Manual - Systems, Operations, and Projects

## Operational Rules

### Telegram Topic Routing Table (AutoPax Group: -1003783528968)
**STRICT ROUTING RULE:** Never guess where to send a message. All cron jobs, automated reports, and project updates MUST explicitly use the `--to <group_id>:<topic_id>` flag matching this table. For general system updates (OpenClaw, ROBA, infra), route to Robel's DM (`393069019`). ALL OTHER output MUST go to its assigned topic in the AutoPax Group. If a project has no topic, discuss it in the DM first and create one. NEVER send project output to the DM or General topic. When adding a new project or automated task, ask Robel for the assigned Topic ID, log it here, and configure the tool to use it exclusively.

| Topic ID | Band / Visual Tag | Name/Purpose | Assigned Jobs / Output |
|----------|-------------------|--------------|-------------------------|
| `1` | 🌐 Topic 1: General | Group default chat | None |
| `2` | 🏗️ Topic 2: Bonds Dev | RockLikeAgencyBonds | Git branch updates, SEO blog reports |
| `3` | 🚌 Topic 3: NYC Permits | New York Tour Bus | Research, data dumps |
| `4` | 🎯 Topic 4: Bonds Lead Hunter | Texas Bond Leads | Daily lead reports, follow-ups |
| `96` | 🚚 Topic 5: Trucking Leads | RockLike Agency Trucking | Daily trucking insurance lead reports |
| `419` | 📱 Topic 6: Social Media | Social Media Manager | Content generation, scheduling, posting |
| `900` | 🧠 Topic 7: Local LLM | Local LLM Improvement | Qwen/Ollama optimization loops |
| `943` | 🌀 Topic 8: Hypnosis | Holographic NLP/Hypnosis | Daily research digest, hypotheses |
| `1051`| 💎 Topic 9: Gemma Agent | Gemma isolated tests | Local LLM interaction experiments |

**STRICT ROUTING RULE FOR TOPIC 2:** Topic 2 is STRICTLY and EXCLUSIVELY for the Bonds project (RockLikeAgencyBonds). NOTHING ELSE.
**GIT PUSH RULE FOR BONDS:** NEVER push code to GitHub for the Bonds project due to Vercel account migration. ALWAYS upload blog posts to Supabase ONLY. Do NOT use `git push` or `gh pr create` for RockLikeAgencyBonds.

---

## Systems I've Built

### Research Library (2026-02-02)
Location: `~/research/`

Organized knowledge base by topic. Current structure (consolidated 2026-02-26):
- `bonds/` (Texas surety bonds + SEO keyword tracker)
- `new-york-permit/` (NYC tour bus / permit research)
- `self-improvement/` (AI agent news and weekly summaries)

### AutoPax Pipeline Breakthrough (2026-03-11)
- **Nightly Lead Gen Loop**: Karpathy-style autoresearch loop on `sync_daily_optimized.py`.
- **Results**: **+5,307% performance increase**, baseline ~3,039 RPM → Gen 27 peak **~177,328 RPM**.
- **Impact**: Refresh the entire high-intent lead database for AutoPax in seconds rather than minutes.

---

## My Resources

- **My email:** robake2006@gmail.com
- **Google account:** robake2006@gmail.com (Chrome)
- **X account:** @barryhauler
- **GitHub account:** RobelsRob2026

---

## Active Projects

### RockLikeAgencyBonds (2026-02-11)
- **Repo:** `rodejene/RockLikeAgencyBonds`
- **Telegram Channel:** AutoPax group (id:-1003783528968, Topic 2)
- **Workflow Rule (2026-03-16):** Blog posts to Supabase ONLY.

### FMCSA Dashboard (2026-03-04)
- **Location:** `projects/fmcsa-dashboard/`

### AutoPax Trucking Lead CRM (2026-03-06 Update)
- **Repo:** `RobelsROB2026/AutoPax-Trucking-CRM`
- **Location:** `/Users/roba/.openclaw/workspace/projects/AutoPax-Trucking-CRM`
- **Scraper:** `/Users/roba/research/trucking/sync_daily_optimized.py`
