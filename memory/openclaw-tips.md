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

## 2026-04-05
- **Releases:** OpenClaw v2026.4.2 is out.
  - Restoration of "Task Flows" with managed and mirrored modes for durable state and revision tracking.
  - Ability to spawn child tasks for complex orchestration.
  - Fully overhauled security model.
  - Android integration with Google Assistant (voice triggers).
  - Breaking changes for XAI search and Firecrawl configs (migration to plugin-owned paths required).
  - Phishing alert: Watch out for fake GitHub issues asking for crypto wallet connections.

## 2026-04-11
- **Releases:** OpenClaw v2026.4.9 confirmed. Features grounded REM backfill and structured diary view.
- **Ecosystem:**
  - **Anthropic Claude Restriction:** Anthropic has restricted standard subscription Claude models for 3rd party agent tools (effective April 4). API-based billing is required.
  - **NemoClaw:** Nvidia unveiled NemoClaw, an enterprise version of OpenClaw with built-in security guardrails.
  - **Security:** Continued focus on protecting internet-facing instances. Researchers flagged risks of script execution with minimal safeguards.
  - **ClawHub:** Marketplace for skills is live.
- **Project Updates:**
  - **AutoPax Gen 23:** Completed. 100% mailing coverage, 97.6% driver count enrichment, 100% reachability.
  - **GWS Auth:** Still 401. Requires `gws auth login`.
  - **Trucking:** Topic routing fixed using `[[reply_to_current]]`.
