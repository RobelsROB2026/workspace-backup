# Weekly AI & OpenClaw Research: 2026-02-15

## 1. OpenClaw Updates (v2026.2.14)
- **Telegram Polls:** Support for sending native polls (`openclaw message poll`).
- **Slack/Discord Security:** New `dmPolicy` and `allowFrom` config aliases for DM control.
- **Reliability:** Added write-ahead delivery queue (v2026.2.13) to prevent message loss on restart.
- **Discord Voice:** Native voice messages with waveforms from local files.
- **Fixes:** Cron scheduler hardened against skips; better workspace bootstrap handling (`BOOTSTRAP.md` persists onboarding state).

## 2. Industry & AI Agent Trends
- **GLM-5 Release:** 744B parameter model (40B active) targeting long-horizon agentic tasks. Features DeepSeek Sparse Attention (DSA).
- **Agentic Infrastructure:** "Agentic Real-Time Framework" (ARTF) gaining traction in ad tech/governance (IAB Tech Lab).
- **Spotify/Big Tech Agents:** Spotify reporting top developers use AI for majority of coding; Microsoft AI chief Mustafa Suleyman predicting white-collar automation surge in 18 months.
- **Anthropic vs Pentagon:** FEUD over Claude's use in military operations (Maduro raid), highlighting safety/terms-of-use tension.

## 3. New Tools & Skills
- **City2Graph:** Python library for geospatial data processing into GNN tensors.
- **MechaEpstein-8000:** Niche but notable local model training example (Qwen3-8B base).
- **GGUF Visualizer:** Community tool for inspecting model internals.

## 4. Learnings for ROB
- **Prompt Injection:** ICML using embedded instructions in PDFs as "compliance checks" - a reminder that even "trusted" documents can have hidden agent triggers.
- **Local Model Efficiency:** DSA and MoE (GLM-5) are the standard for large-scale efficient agents.
