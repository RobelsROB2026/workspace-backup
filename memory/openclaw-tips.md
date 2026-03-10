# OpenClaw Tips & Ecosystem Updates

## OpenClaw Releases
- **v2026.3.8 (2026-03-09)**: Stable release. 
    - New Features: `openclaw backup create` and `verify` for local state archives.
    - Improvements: Resolved Telegram DM routing duplicates and macOS launchd restart bugs.
    - **Security Alert**: Beware of fake OpenClaw GitHub repositories distributing malware (info-stealers). Only download from the official `openclaw/openclaw` repo.

## GitHub Community (March 10)
- **New Issues**:
    - #42054: Discord button interactions expire before agent responds.
    - #42039: Expose `maxMissedJobsPerRestart` and `missedJobStaggerMs` in cron config.
    - #42038: WebChat lacks support for Exec Approval pop-ups.
- **Security**: Surge in GHSAs (255+). Disparity between GitHub advisories and CVE tracking.

## ClawHub New Skills
- **EngageLab Omni Connect**: WhatsApp, SMS, Voice, and Email integration for agents. High value for lead gen automation and after-sales follow-ups.
- **Zapier-Bridge**: Connect to 5,000+ web services via Zapier.
- **GitHub-Orchestrator v4.0**: Supports GitHub Projects and Copilot Workspace.
- **Security Command**: `clawhub audit` scans skills against threat feeds (VirusTotal, GitHub Advisory).

## Productivity
- **Parallel Fetching**: Implementing parallel batching in data pipelines (like the Trucking Daily Sync) reduces execution time by ~75% (from 3 mins to 42s).
