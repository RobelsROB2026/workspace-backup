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

### OpenClaw Updates & News (2026-03-17)
- **GitHub Release v2026.3.13-1**: Recovery release fixing broken tag/release path.
- **New Channels**: Twitch and Google Chat plugins now available.
- **Model Support**: Added support for KIMI K2.5 and Xiaomi MiMo-V2-Flash models.
- **Onboarding**: Improved daemon installation for slower Macs/fresh VMs.
- **Security**: ClawHub now integrates VirusTotal for automatic skill scanning; still recommended to review skills before install.
- **Pro-Tip**: Use memory categorization (3-tier system) to reduce token costs and improve performance by only providing relevant context.
- **Debugging**: Use verbose mode ("full" option) to observe agent tool calls and learn which tools to invoke explicitly.

