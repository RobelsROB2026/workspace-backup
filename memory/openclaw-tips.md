# OpenClaw Tips & Research (2026-03-18)

## News & Releases
- **v2026.3.13 (March 16, 2026)**: Mobile redesign, 2x memory fix, 70+ stability patches.
- **v2026.3.11/12 (March 13, 2026)**: Dashboard rewrite, Fast mode, 8 security fixes.
- **NVIDIA NemoClaw™**: Announced March 16, 2026. A secure stack for OpenClaw agents providing sandbox isolation and a 'privacy router'.
- **Milestone**: OpenClaw reached 310,000 stars on GitHub.

## Security Alerts
- **HKCERT Warning**: Risks in the skills supply chain and fake installers. Always verify skill sources (ClawHub) and avoid root access.
- **CVE-2026-25253**: Reminder that one-click RCE was patched in v2026.1.29. Ensure we stay updated.

## Tips & Hacks
- **Port Security**: Change default port (18789) to prevent scanning.
- **Model Routing**: Use tiered routing (Gemini Flash for routine, Opus for reasoning) to manage costs.
- **Guardrails**: Use `SKILL.md` to define strict agent behavior.
- **Cron**: Use the native scheduler for background tasks (we are doing this!).
- **Workspace Memory**: Keep `USER.md`, `AGENTS.md`, `HEARTBEAT.md`, and `MEMORY.md` updated for persistent context.
