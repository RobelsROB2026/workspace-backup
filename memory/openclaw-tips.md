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

## General Tips
- Use `openclaw update` to pull the latest version.
- `openclaw status --deep` for channel testing.
- `agents.defaults.heartbeat.directPolicy: "block"` if you want to keep heartbeats out of DMs.
- Check `openclaw cron list` to verify background task health.
