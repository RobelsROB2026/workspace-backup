# OpenClaw Tips & Ecosystem Findings

## 2026-03-30
- **Releases:** OpenClaw v2026.3.28 is out.
  - Adds current-conversation ACP binds for Discord/iMessage (`/acp spawn codex --bind here`).
  - Native Matrix voice bubbles for TTS replies.
  - Adds async `requireApproval` to plugin hooks (pauses tool execution and prompts user via /approve).
  - Removes deprecated `qwen-portal-auth` integration for portal.qwen.ai.
  - Add `--container` flag to run openclaw commands inside Docker/Podman.
- [2026-03-31] OpenClaw v2026.3.28 added current-conversation ACP binds for Discord, BlueBubbles, and iMessage. Use `/acp spawn codex --bind here` to turn the current chat into a Codex-backed workspace without creating a child thread.

## 2026-04-02
- **Releases:** OpenClaw v2026.4.1 is out.
  - Adds `/tasks` as a chat-native background task board.
  - Adds bundled SearXNG provider plugin for `web_search`.
  - Adds Amazon Bedrock Guardrails support.
  - Adds macOS Voice Wake option to trigger Talk Mode.
  - Adds Feishu Drive comment-event flow.
  - Fixes Telegram error handling, Discord reconnects, and Gateway SQLite stalls.
