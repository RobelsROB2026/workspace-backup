# OpenClaw Tips & Ecosystem Updates (Updated 2026-03-10)

## OpenClaw Releases
- **v2026.3.8 (2026-03-09)**: Stable release. 
    - New Features: `openclaw backup create` and `verify` for local state archives.
    - Improvements: Resolved Telegram DM routing duplicates and macOS launchd restart bugs.
    - **Security Alert**: Beware of fake OpenClaw GitHub repositories distributing malware (info-stealers). Only download from the official `openclaw/openclaw` repo.
- **v2026.3.8-beta.1 (2026-03-08)**: Focuses on Telegram deduplication and cron fixes.

## ClawHub New Skills
- **RootData Skills (2026-03-09)**: Crypto data platform integration. Access to project, financing, token, and market sentiment data.
- **EngageLab Omni Connect**: WhatsApp, SMS, Voice, and Email integration for agents. High value for lead gen automation.
- **Zapier-Bridge**: Connect to 5,000+ web services via Zapier.
- **GitHub-Orchestrator v4.0**: Supports GitHub Projects and Copilot Workspace.
- **Security Command**: `clawhub audit` scans skills against threat feeds (VirusTotal, GitHub Advisory).

## Security Partnership
- **VirusTotal x OpenClaw (2026-02-10)**: Automated security scanning for all ClawHub skills. Malicious skills are blocked; suspicious ones are flagged.

## Productivity
- **Parallel Fetching**: Implementing parallel batching in data pipelines (like the Trucking Daily Sync) reduces execution time by ~75% (from 3 mins to 42s).

### 2026-03-12: OpenClaw v2026.3.12 Released
- **Control UI v2**: Modular overview, command palette, and mobile optimization.
- **Fast Mode**: Per-model /fast toggles for GPT-5.4 and Claude.
- **Security**: Short-lived bootstrap tokens for device pairing.
- **Yield**: New `sessions_yield` for orchestrators.
- **Upgrade**: `npm install -g openclaw`

### 2026-03-13: OpenClaw Global News & Plugins
- **China Mania**: Massive adoption (300k+ stars) and mixed regulatory response in China.
- **New Plugin**: Memori Labs launched a persistent memory capture/recall plugin for multi-agent gateways.
- **AMD Support**: Native local execution now supported on Ryzen AI Max+ and Radeon GPUs.
- **Security**: Critical vulnerability chain patched (ensure running latest stable 2026.3.12).

### 2026-03-13: OpenClaw Architecture & Market Trends
- **China Market Leader**: China has overtaken the US in OpenClaw adoption, leveraging cheaper domestic AI models for large-scale automation.
- **ContextEngine (v2026.3.7)**: A new pluggable interface for context management, maturing the agentic architecture for sophisticated workflows.
- **Security Hardening (v2026.2.23+)**: Improved CVE handling and optional HSTS headers. High-risk actions should be containerized (e.g., using Docker as seen in NanoClaw).
- **Founder Move**: OpenClaw creator Peter Steinberger reportedly joined OpenAI to lead personal agents, signaling industry-wide shift toward agentic AI.

### 2026-03-13: OpenClaw v2026.3.13 Released
- **Latest Stable**: v2026.3.13 just dropped.
- **Features**: Focused on dashboard UI enhancements, chat settings, and improved subagent spawning/iOS sharing.
- **Status**: We are on v2026.3.11. Update available via `npm update`.
