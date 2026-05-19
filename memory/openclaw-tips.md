# OpenClaw Tips & News (May 2026)

## Releases
- **v2026.5.14** (2026-05-14): Fixes Codex OAuth refresh, preserves media in agent replies, fixes GitHub Copilot Gemini descriptions.
- **Post-v2026.5.14 (mid-May)**:
    - **Leaner installs**: WhatsApp, Slack, Amazon Bedrock, Anthropic Vertex, and provider/plugin dependency cones moved out of core runtime — installs only pull what you use.
    - **Telegram resiliency**: Isolated polling, durable local spooling, safer group-media handling, preserved HTML/Markdown formatting in streamed/scheduled replies. (Relevant to AutoPax Trucking CRM Telegram target.)
    - **CLI/config**: Broken discovered plugins no longer fail `openclaw config validate` unless referenced by active config.
    - **GitHub Copilot**: Drops unsafe native Responses reasoning replay items before dispatch (prevents invalid_request_body session failures).
    - **Agents/Codex**: Fails closed when an explicitly requested Codex harness is not registered instead of silently falling back.
    - **QA-Lab**: New `openclaw qa suite --runtime-parity-tier`; standard Codex-vs-Pi tier wired into release checks.
    - **Mac app**: Redesigned Settings pages — consistent card layouts, cached navigation, cleaner permissions/voice/skills/cron/exec/debug panes.
- **Grok 4.3** (May 2026): Multimodal (video), 1M-2M context, enterprise focus.

## Security Alerts
- **ClawHavoc Campaign**: Massive poisoning of ClawHub with 1000+ malicious skills. Aims for credentials, reverse shells, and cryptomining. Mitigated ranking vulnerability in March, but malicious code persists in unverified skills.
- **CVE-2026-3854**: RCE in GitHub backend (CVSS 8.7). Patch released; update local environments.

## Community & Ecosystem
- **Discord Policy**: "No crypto" rule strictly enforced to prevent spam/scams (following $CLAWD incident).
- **Competitors**:
    - **Remy (Google)**: Proactive assistant monitoring Gmail/Calendar/Docs.
    - **Hatch (Meta)**: Agentic assistant for Meta apps (Muse Spark model).

## Development
- OpenClaw hit 250k GitHub stars in early 2026.
- Anthropic reinstated Claude usage for agents via "Agent SDK" credit system.

## Skills/Subagents Cost Note (May 2026)
- Anthropic guidance: subagent-heavy workflows consume **~7x the tokens** of a single-thread session. For tight budgets / rate limits, prefer single-thread; reserve subagents for genuinely parallel work or context isolation.
- Heuristic: small work that should stay in front → **skill**. Big work that should run in a side process → **subagent**.
- Skill bodies load only on invocation (unlike CLAUDE.md content) — long reference material costs almost nothing until needed.
- Subagent `description` field needs explicit trigger phrases ("Use this agent when X") or auto-invocation fails.

## New LLM Models (April–May 2026)
- **GLM 5.1** (open-weights, released 2026-03-27, open-sourced 2026-04-08): 744B MoE / 40B active, 200K ctx. Currently #1 on Artificial Analysis Intelligence Index for open-weights. **Best for 8-hour sustained single-agent coding**.
- **Kimi K2.6** (released 2026-04-20): Leads SWE-Bench Pro at 58.6%, $0.60/M output tokens. **Best for multi-agent orchestration (300-agent Swarm)**. Powers Cursor Composer 2.5.
- **DeepSeek V4** (released 2026-04-24): 1M context window. V4-Pro and V4-Flash (284B/13B active) both MIT-licensed with mature tool calling. **Best for massive-context agents**.
- **MiMo-V2.5** (Xiaomi): MiMo-V2.5-Pro (1.02T total, 42B active) — long-horizon tool use focus.
- **Qwen 3.6-27B dense**: New r/LocalLLaMA default for local agentic work. SWE-bench Verified 77.2, Terminal-Bench 2.0 59.3.
- **Hermes Agent (Nous)**: #1 on OpenRouter token metrics, ahead of Claude Code — built with per-model tool-call formatting.

Combo pattern teams are using: **DeepSeek** for context, **Kimi** for orchestration, **GLM** for sustained execution.

## Local Quantization Consensus (r/LocalLLaMA, May 2026)
- **Q4_K_M**: floor for agentic work
- **Q5_K_M**: comfortable
- **Q6_K**: sweet spot when VRAM allows
- **Q8_0**: overkill for most agentic cases

## Last research: 2026-05-19 (Friday self-improvement)
