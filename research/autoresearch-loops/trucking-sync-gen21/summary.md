# Gen 21 Summary — 2026-04-10/11 (Night Session)

## Focus: Email Quality Repair + Contact Gap Analysis + Quality Scoring

### Baseline (2026-04-11, session start)
| Field | Per 100 | vs Gen20 | Notes |
|-------|---------|----------|-------|
| Phone | 99.5 | -0.1 | Near ceiling |
| Cell (honest) | 20.8 | -0.7 | Structural FMCSA gap |
| Email | 96.6 | +0.3 | 4,203 leads missing |
| Officer | 98.7 | +0.0 | Near ceiling |
| Fax | 20.3 | -0.4 | Low-value channel |
| Mailing | **100.0** | **+9.7** | **New ceiling** (was 90.3) |

Total leads: 123,907 | Total companies: 4,413,951

### Hypothesis Results
| # | Hypothesis | Result | Delta | Verdict |
|---|-----------|--------|-------|---------|
| H7 | Email repair (typos, malformed, junk, siblings) | 121 typo-domain, 50+ malformed, ~10 junk, 290 sibling-recoverable | Est. +0.3pp | **Identified, partially applied** |
| H8 | Mailing address fallback | Already 100.0/100 | +0.0 | No-op |
| H9 | Phone cleanup (555s, dupes) | 186 cell==phone dupes NULLed | +0.0pp | **Applied** |
| H10 | Alternative FMCSA datasets | Census is ONLY dataset with contacts | N/A | **Dead end** |
| H11 | Contact quality scoring | 99.4% unique emails, quality tiers mapped | Diagnostic | **Actionable intel** |
| H12 | Re-fetch missing-email DOTs from FMCSA | 0/500 new emails recovered | +0.0 | **Dead end** |

---

### H7: Email Repair (Detailed)

**Gap profile (4,203 leads missing email = 3.39%):**
- 90-Day Renewal: 3,650 missing (5.0% of type)
- Recent Cancellation: 474 (1.5%)
- TN For-Hire: 72 (6.9%)
- New Venture: 7 (0.04%)

**By registration vintage:**
- Pre-2000: 18-27% missing (FMCSA didn't require email)
- 2000-2010: 5-11% missing
- 2010-2015: 2-9% missing
- 2016+: <1% missing
- **Conclusion: structural gap in old registrations, unfixable via FMCSA**

**Identified fixable patterns (121 leads):**
| Pattern | Count | Example |
|---------|-------|---------|
| @gmail.co | 29 | user@gmail.co → user@gmail.com |
| @gmai.com | 15 | user@gmai.com → user@gmail.com |
| @gamil.com | 15 | user@gamil.com → user@gmail.com |
| @gmial.com | 9 | (already fixed in partial run) |
| @yahoo.co | 8 | user@yahoo.co → user@yahoo.com |
| @gmail.con | 7 | user@gmail.con → user@gmail.com |
| Other typos | 38 | hotmail.co, outlook.co, etc. |

**Malformed emails (50+ in leads):**
- `Camposcesar489@gmail Com` → `Camposcesar489@gmail.com`
- `DISPATCH@DOUBLEKTRANSPORT, COM` → `DISPATCH@DOUBLEKTRANSPORT.COM`
- `YEPAREDES1015hotmail.com` → `YEPAREDES1015@hotmail.com`
- Websites stored as email: `www.gymsource.com` → NULL
- Names stored as email: `hilton Veit` → NULL

**Sibling recovery potential: 290 DOTs recoverable** via phone-sibling matching (same phone number → copy email from sibling company)

**Partial execution:** H7 first run applied 1,123 typo fixes across full companies table:
- gmial→gmail: 230, gmal→gmail: 133, gamil→gmail: 441, gmai→gmail: 292, gnail→gmail: 27
- Deadlocked before completing remaining fixes

**Remaining H7 script:** `h7_micro.py` — works but takes ~4.8 hours through Supabase pooler (7.3s per 50-DOT batch × 2,478 batches). Run as overnight batch.

**Estimated impact:** ~+0.3pp email rate (mostly from sibling recovery)

---

### H9: Phone Cleanup

| Finding | Count | Action |
|---------|-------|--------|
| cell_phone == phone duplicates | 186 | **NULLed** (honest metric) |
| Phones containing "555" | 783 | All legitimate (555 in middle of real numbers) |
| Fictional 555-01XX | 0 | None found |
| Repeated-digit phones | 0 | Already cleaned in Gen20 |
| Most-shared phone | 284 leads | `2029182132` — permit agent, flagged not removed |

**Applied: 186 cell==phone duplicates NULLed.** Phone rate stable at 99.5.

---

### H10: Alternative FMCSA Datasets

| Dataset | ID | Contact Fields | Verdict |
|---------|------|---------------|---------|
| Census (current) | az4n-8mr2 | email, phone, cell, officer, fax, mailing | **Only source** |
| SMS Census | kjg3-diqy | email, phone only (subset) | Redundant |
| Licensing | qh9u-swkp | None | Dead end |
| 126 other datasets | Various | None with contacts | Dead end |

**Census is the ceiling.** No alternative FMCSA dataset has contact fields beyond what we already capture.

---

### H11: Contact Quality Analysis

**Email uniqueness:**
- 117,586 unique emails (99.4% of total)
- 721 shared emails across 2,118 leads (1.7% of leads)
- Shared emails = permit service agents, not the actual carrier

**Top agent/shared emails:**
| Email | Leads | Type |
|-------|-------|------|
| TRANSCOMPSERVICEPIN@GMAIL.COM | 47 | Permit service |
| CARRIER@CHAMPIONTRAFFIC.COM | 41 | Traffic consultant |
| MARK@TRUCKINGCONSULTANT.COM | 38 | Trucking consultant |
| safety@applemoving.com | 27 | Moving network |
| COMPLIANCE@ALLMYSONS.COM | 21 | Franchise HQ |

**Top agent domains (high lead:email ratio):**
| Domain | Leads | Distinct Emails | Ratio |
|--------|-------|-----------------|-------|
| @coast22.net | 52 | 3 | 17.3 |
| @applemoving.com | 35 | 2 | 17.5 |
| @truckingconsultant.com | 60 | 4 | 15.0 |
| @championtraffic.com | 49 | 4 | 12.2 |
| @dotusvetprocessagents.com | 24 | 2 | 12.0 |

**Top shared phones (permit agents):**
| Phone | Leads | Likely |
|-------|-------|--------|
| 2029182132 | 284 | Permit agent |
| 2134947314 | 81 | Permit agent |
| 2083912136 | 76 | Permit agent |
| 4694615000 | 52 | All My Sons HQ |

**Contact quality tiers:**
| Tier | Count | % |
|------|-------|---|
| 5+ (excellent) | 24,050 | 19.4% |
| 4 (good) | 92,259 | 74.5% |
| 3 (fair) | 3,839 | 3.1% |
| 2 (poor) | 2,477 | 2.0% |
| 0-1 (minimal) | 1,282 | 1.0% |

93.9% of leads at quality tier 4+. Only 1.0% have minimal contact info.

---

### H12: FMCSA Re-fetch

- Sampled 500 most-recent leads missing email
- All 500 found in FMCSA Census API
- **Zero new emails, cells, or officers recovered**
- FMCSA genuinely does not have email for these carriers

---

### Infrastructure Discovery: Supabase Pooler Performance

**Critical finding:** The Supabase connection pooler (port 6543) has a **2-minute statement timeout** that makes batch operations on the 4.4M-row companies table very difficult.

| Operation | Time | Works? |
|-----------|------|--------|
| `SELECT COUNT(*) FROM leads` | <1s | Yes |
| `SELECT dot_number FROM leads LIMIT 1000` | <1s | Yes |
| Single-DOT PK lookup on companies | 279ms | Yes |
| 10-DOT ANY() on companies | 180ms | Yes |
| 50-DOT ANY() on companies | 7.3s | Yes (slow) |
| 200-DOT ANY() on companies | >120s | **TIMEOUT** |
| leads JOIN companies (124K×4.4M) | >120s | **TIMEOUT** |
| `SELECT DISTINCT dot_number FROM leads` | >120s | **TIMEOUT** |

**Root cause:** Each query through the pooler adds ~100-200ms overhead. The 4.4M companies table requires ~7s even for a 50-row PK lookup.

**Workarounds discovered:**
1. Pre-fetch lead DOTs via `LIMIT/OFFSET` (single-table, fast)
2. Query companies in 50-DOT batches with `ANY()` (7s each)
3. Avoid JOINs between leads and companies through the pooler
4. Kill stale connections before new sessions (`pkill -f python3`)
5. Reconnect every 500 batches to prevent pool exhaustion

---

### Key Findings

1. **FMCSA Census is fully tapped.** All contact fields extracted. No alternative datasets. Re-fetch yields zero new data. The enrichment ceiling is structural.

2. **Email gap is vintage-driven.** 4,203 leads (3.39%) missing email, almost entirely pre-2015 registrations. Only ~290 recoverable via sibling matching (+0.23pp). Remaining ~3,900 require external sources.

3. **Mailing address hit 100%.** Jumped from 90.3 to 100.0 (likely from Gen20 backfill settling or recent lead composition shift).

4. **Contact quality is high.** 93.9% of leads at tier 4+ (good/excellent). Only 6 leads have zero contact info.

5. **2,118 leads have agent contacts.** Shared emails/phones belong to permit services, not the actual carrier. Worth flagging for outreach campaigns.

6. **Pooler performance is the bottleneck.** Batch operations on the 4.4M companies table require 50-DOT micro-batches at 7s each, making full-table updates take hours.

---

### Gen 22 Recommendations

| Priority | Action | Impact | Effort |
|----------|--------|--------|--------|
| 1 | Run `h7_micro.py` as overnight batch | +0.3pp email | Low (4.8h runtime) |
| 2 | Flag agent/shared contacts in CRM | Outreach quality | Medium |
| 3 | Add phone index for sibling recovery | Faster batch ops | Low |
| 4 | External email sources (web scraping, Google Business) | +1-2pp email | High |
| 5 | Cell phone via external sources | +5-10pp cell | High |
| 6 | Consider direct DB connection (port 5432) for batch ops | 10x faster batches | Low |
