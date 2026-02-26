# OpenClaw Tips & Updates

## [2026-02-26] v2026.2.25 Released
- **Android/Chat**: Improved streaming and markdown rendering.
- **Android/Startup**: Better perf tracking and deferred startup.
- **Heartbeat Config**: `agents.defaults.heartbeat.directPolicy` (allow|block) replaces the old DM toggle. **Note: default is now 'allow' again.**
- **Subagents**: Refactored completion announce state machine for better reliability.
- **Security**: Hardened Gateway auth and WebSocket origin checks. Pairing now required for operator device-identity sessions.
- **Branding**: Migration to `ai.openclaw` continues (replaces `bot.molt`).

## General Tips
- Use `openclaw update` to pull the latest version.
- `openclaw status --deep` for channel testing.
- `agents.defaults.heartbeat.directPolicy: "block"` if you want to keep heartbeats out of DMs.
