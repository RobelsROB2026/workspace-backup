# OpenClaw Tips & Ecosystem Findings

## 2026-03-30
- **Releases:** OpenClaw v2026.3.28 is out.
  - Adds current-conversation ACP binds for Discord/iMessage (`/acp spawn codex --bind here`).
  - Native Matrix voice bubbles for TTS replies.
  - Adds async `requireApproval` to plugin hooks (pauses tool execution and prompts user via /approve).
  - Removes deprecated `qwen-portal-auth` integration for portal.qwen.ai.
  - Add `--container` flag to run openclaw commands inside Docker/Podman.
- [2026-03-31] OpenClaw v2026.3.28 added current-conversation ACP binds for Discord, BlueBubbles, and iMessage. Use `/acp spawn codex --bind here` to turn the current chat into a Codex-backed workspace without creating a child thread.
