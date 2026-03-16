# OpenClaw Tips & Ecosystem Updates (Updated 2026-03-16)

## OpenClaw Releases
- **v2026.3.13 (2026-03-14)**: Security focus.
    - Mandatory short-lived bootstrap tokens for device pairing (`/pair`).
    - Implicit workspace plugin auto-load disabled for safety.
    - Improved session continuity: `lastAccountId` and `lastThreadId` preserved on gateway resets.
    - Fixed macOS daemon installation reliability.
- **v2026.3.8 (2026-03-09)**: Stable release. 
    - New Features: `openclaw backup create` and `verify` for local state archives.

## ClawHub New Skills
- **afrexai-business-automation**: Comprehensive suite for architecting business workflows.
- **RootData Skills (2026-03-09)**: Crypto data platform integration. 
- **EngageLab Omni Connect**: Omnichannel engagement (WhatsApp, SMS, Voice, Email).

## Security & Architecture
- **Unix Agent Philosophy**: Industry moving towards single `run` tool + CLI instead of bloated toolsets.
- **AMD Support**: Local execution enabled for Ryzen AI Max+ and Radeon GPUs.
- **China Market Dominance**: Significant adoption of OpenClaw in China using domestic models.

## Productivity
- **Parallel Fetching**: Implementing parallel batching in data pipelines reduces execution time significantly (e.g., Trucking Sync).
- **Master/Muscle Protocol**: Delegate execution to Claude Code while keeping ROB as the thinker/planner.

### Maintenance
- Update available via `npm install -g openclaw`.
