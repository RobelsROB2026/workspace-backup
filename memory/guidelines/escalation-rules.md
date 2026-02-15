# Escalation Rules: When to Use Ops (Opus)

## Use Gemini (Main) For:
- Following existing workflows
- Routine tasks with clear steps
- Simple questions and lookups
- Executing documented procedures
- Basic file operations
- Standard cron job execution

## Escalate to Ops (Opus) When:
- No existing workflow covers the task
- Complex multi-step planning needed
- Creating new procedures or guidelines
- OpenClaw configuration changes
- Security-sensitive decisions
- Debugging complex issues
- Evaluating tradeoffs or strategies
- Improving existing systems

## How to Escalate
```
sessions_spawn task:"[describe what needs Opus-level thinking]" model:"anthropic/claude-opus-4-5" label:"ops"
```

## After Ops Completes
1. Ops creates workflow/guideline
2. Store in `memory/workflows/` or `memory/guidelines/`
3. Future similar tasks → Gemini follows the workflow
