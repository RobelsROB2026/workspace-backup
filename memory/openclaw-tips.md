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
  - **OpenClaw v2026.4.10:** Major release with bundled Codex provider, Active Memory plugin, and local MLX speech for Talk Mode on macOS.
  - **OpenClaw v2026.4.7:** Introduced "Memory Wiki Stack" and session compaction & branching.
  - **ClawHub Package Catalog:** Now supports native publishing and versioning of code/bundle plugins (not just text SKILL.md).
  - **Anthropic Claude Restriction:** Third-party tools like OpenClaw are now blocked from using Claude models on standard subscription plans; API usage-billing is required.
- **Project Status:**
  - **Gen 25 Autoresearch:** Baseline established at 34,311 RPM. Nightly loop failed to run autonomously due to interactive TTY prompts. Terminated process.
  - **GWS:** Gmail/Calendar active but require regular triage.

## 2026-04-13
- **AI Industry News:**
  - **Claude for Word:** Anthropic launched beta for Team/Enterprise. Includes AI editing and clickable citations.
  - **Claude Mythos Security:** UK regulators issuing warnings to financial institutions regarding Mythos Preview security risks.
  - **Meta "Mango":** Image/Video AI model expected H1 2026.
  - **Nvidia Blackwell:** Rental prices for Blackwell GPUs surged 48% to .08/hr due to agentic AI demand.
  - **Regulatory:** US AI chip export implementation risks due to BIS licensing bottlenecks. California AG investigating xAI/Grok over AI image proliferation.
  - **Hardware:** Apple testing 4 designs for AI glasses with camera systems.
  - **Japan:** Consorted effort (SoftBank, Sony, Honda) targeting a 1T-parameter "physical AI" foundation model by 2030.

## 2026-04-13 Midday Update
- **Meta Superintelligence Labs:** Released **Muse Spark**, aimed at a smarter/faster Meta AI.
- **Stanford HAI 2026 AI Index:** Reports AI capability is accelerating; US-China gap has closed; US leads in investment.
- **Qualcomm AI Chips:** Unveiled **AI200** (2026) and **AI250** (2027) inference chips.
- **Corporate Trends:** Amazon planning layoffs citing increased AI efficiency.
