# OpenClaw Tips & Updates

## [2026-02-26] v2026.2.25 Released
- **Android/Chat**: Improved streaming and markdown rendering.
- **Android/Startup**: Better perf tracking and deferred startup.
- **Heartbeat Config**: `agents.defaults.heartbeat.directPolicy` (allow|block) replaces the old DM toggle. **Note: default is now 'allow' again.**
- **Subagents**: Refactored completion announce state machine for better reliability.
- **Security**: Hardened Gateway auth and WebSocket origin checks. Pairing now required for operator device-identity sessions.
- **Branding**: Migration to `ai.openclaw` continues (replaces `bot.molt`).

## [2026-02-28] v2026.2.26 Highlights & ClawHub Discoveries
- **OpenClaw v2026.2.26**: Latest stable release. Highlights include External Secrets Management workflow, ACP/Thread-bound agents as first-class runtimes, and explicit account-risk warnings for Gemini CLI OAuth.
- **ClawHub Discoveries**:
    - `Ontology`: Structured memory using a typed knowledge graph (useful for complex project tracking).
    - `self-improving-agent`: Systematized correction capture for continuous improvement.
    - `Proactive Agent`: Patterns for anticipation and autonomous crons (The "Hal Stack").

## [2026-03-03] v2026.3.2 Released & Community Insights
- **OpenClaw v2026.3.2**: Latest stable release. Features include native PDF analysis (Anthropic/Google backends), enhanced SecretRef (64 targets), STT API, and Telegram "partial" streaming.
- **Discord Community Tips**:
    - **No Crypto Talk**: Strict and actively enforced ban on all cryptocurrency discussions following a rebrand scam.
    - **Support Protocol**: Provide detailed config snippets and error logs up front for faster help in Discord.
    - **Security**: Use user allowlists and granular channel permissions to secure your bot; each channel can have its own isolated session context.
- **Ecosystem News**:
    - **Anthropic**: Claude Code now has a voice mode (rolling out).
    - **Meta**: New applied AI engineering org focused on superintelligence.
    - **Hardware**: New MacBook Pros with M5 Pro/Max chips are 4x faster at LLM prompt processing—significant for local agents.
    - **OpenClaw Milestone**: Surpassed **250,000 GitHub stars**, overtaking React.

## [2026-03-06] Mid-day Update
- **Cursor Automations**: New agentic coding tool launched. Can trigger agents via git, Slack, or timers.
- **Claude Opus 4.6**: Firefox bug hunt success (100+ bugs found in 2 weeks).
- **SoftBank/OpenAI**: B loan sought for OpenAI stake.

## [2026-03-06] Afternoon Update
- **OpenAI Codex Security**: New agent launched for automated vulnerability discovery and remediation.
- **Anthropic Claude Marketplace**: Companies can now buy third-party software using committed Anthropic spend.
- **Cerebras IPO**: AI chipmaker aiming for ~B raise as soon as April.
- **Oracle/OpenAI Data Center**: Plans for Stargate Texas expansion abandoned amid financing disputes.


## [2026-03-07] Night Update
- **OpenClaw v2026.3.2 Features**: 
    - **Native PDF Tool**: Supports Anthropic and Google PDF backends for direct analysis.
    - **Expanded SecretRef**: 64 targets across lifecycle (planning/exec/audit).
    - **Telegram "Partial" Streaming**: Default for real-time preview in DMs.
- **ClawHub Community & Security**:
    - **ClawHavoc Warning**: Be cautious of malicious skills exfiltrating data; audit unverified authors.
    - **New Skills**: "Audience Architect" (Google Ads management) and `n8n` workflow integration are trending.
    - **Agentmail-integration**: New skill for automated email handling in coding workflows.
- **Web3 & Finance**:
    - **Binance & BNB Chain**: Launched 7 AI Agent skills for market insights, trade execution, and on-chain management.
- **Ecosystem**:
    - **iPollo ClawPC A1 Mini**: Dedicated hardware specifically for running OpenClaw agents.
