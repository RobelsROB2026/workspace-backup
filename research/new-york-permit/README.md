# NYC Tourist Bus Business

## Executive Summary
**Verdict:** High barrier to entry, but high potential profit.
**Main Hurdle:** Securing **NYC DOT Authorized Sightseeing Bus Stop Permits**. You can buy a bus, but without legal places to stop, you can't operate. Existing players (Big Bus, TopView) likely control the prime real estate.

## 1. Getting Started (The Requirements)
To legally operate, you need three main things:
1.  **DCWP Sightseeing Bus License:** For the business itself (~$100/2 years). **Must be obtained first.**
2.  **NYC DOT Authorized Bus Stop Permits:** For *each* on-street stop. **Must be obtained second.**
3.  **Compliant Vehicles:** Must meet USEPA emissions (Local Law 41) and have headphone-limited sound systems (no loudspeakers).

## 2. The Application Process (Updated 2026-03-15)
**DOT Bus Stop Permits:**
- **New application fee:** $520 per stop.
- **Renewal fee:** $155 per stop (valid for up to 3 years).
- **Timeline:** Up to 180 days (6 months) for approval.
- **Requirements for Application:**
    - Contact info for owner/operator.
    - Federal and State Motor Carrier Identification Numbers (US DOT/MC).
    - Valid DCWP Sightseeing Bus License.
    - Proposed stop location + 2 alternates.
    - Schedule of service.
    - Proof of Insurance and Registration ID Cards.
    - Planned route in/out of NYC.
- **Consultation:** DOT consults with Community Boards (45-day review period) and other agencies (MTA, Port Authority).

## 3. Why So Few Players? (The Cons)
- **Scarcity of Bus Stops:** NYC curb space is fiercely contested. Getting *new* stops approved requires community board review and DOT sign-off.
- **Strict Regulations:**
    - **Headphone Rule:** Open-air buses must use headphones. Loudspeakers are illegal.
    - **Emissions:** Strict engine conformity rules (Local Law 41). No cheap used buses.
    - **Inspections:** Every 4 months. Failure = suspension.
- **Political Pressure:** Consistent push to cap total licenses around ~225-237 citywide to reduce congestion.

## 3. Official Contacts
Use these to confirm availability of *new* bus stop permits before spending a dime.

**NYC DOT General Permits Office (Bus Stops):**
- **Phone:** (646) 892-1242
- **Ask:** "Are you currently accepting applications for *new* sightseeing bus stops, or is there a waiting list?"

**NYC DCWP (Business License):**
- **Email:** BCC@dcwp.nyc.gov
- **Location:** 42 Broadway, Manhattan

## 4. Next Steps
1.  **Call DOT immediately:** Confirm if *new* bus stop permits are even being issued.
2.  **Check Vehicle Costs:** Price out buses that meet Local Law 41 (emissions) + headphone systems.
3.  **Scout Competitor Stops:** See where Big Bus/TopView stop. Those spots are likely "taken" unless shared use is allowed (unlikely).

## Note (2026-03-05)
We now have persistent, background access to Google Workspace at all times via `gws`. We can integrate Google Sheets, Drive, or Calendar into this project's workflows autonomously.

## The Muscle Protocol (Coding Workflow)
As of 2026-03-05, all coding, script writing, and complex terminal executions for this project must be delegated to **Claude Code**. I (ROB) will design the architecture and plan the steps, but I must spawn Claude via the terminal (`exec pty:true command:"claude ..."`) to execute the actual code writing.
Update (2026-03-09): Reviewed NYC Tour Bus requirements with Robel. Sent immediate next steps to AutoPax Telegram Topic 3. Key blockers to apply for DOT stops include forming the business entity in NY, obtaining US DOT/MC numbers, and acquiring compliant vehicles with VINs/Insurance to register in NYCStreets.
