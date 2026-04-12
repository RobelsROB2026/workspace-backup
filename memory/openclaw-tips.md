# OpenClaw Tips & Ecosystem Findings

## 2026-03-30
- **Releases:** OpenClaw v2026.3.28 is out.
  - Adds current-conversation ACP binds for Discord/iMessage (`/acp spawn codex --bind here`).
  - Native Matrix voice bubbles for TTS replies.
  - Adds async `requireApproval` to plugin hooks (pauses tool execution and prompts user via /approve).
  - Removes deprecated `qwen-portal-auth` integration for portal.qwen.ai.
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

## 2026-04-12
- **Ecosystem News:**
  - **Japanese AI Consortium:** SoftBank, NEC, Sony, and Honda formed a firm to develop high-performance Japanese AI, supported by a ¥1 trillion government program (NEDO).
  - **California AI Regulation:** California is moving forward with its own AI safety framework, despite federal efforts to limit state-level controls.
  - **DeepSeek V4:** Anticipation for DeepSeek's new V4 model, a benchmark for China's AI progress and self-sufficiency in hardware.
  - **AI in Warfare:** Emerging ethical and risk discussions regarding automation bias and corporate responsibility in military AI.
- **Project Status:**
  - **Gen 25 Autoresearch:** Baseline established at 34311 RPM. 2-hour optimization loop started in ACP session.
  - **GWS:** Access remains 401 Unauthorized. User action required.
