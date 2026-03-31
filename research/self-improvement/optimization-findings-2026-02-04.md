# OpenClaw Optimization Research - Feb 4, 2026

## Key Findings from X/Twitter Community

### 🎯 Model Routing (Biggest Impact - 90% cost savings possible)

**Multi-tier approach:**
- **Complex reasoning** → Opus ($15/M tokens)
- **Execution/sub-agents** → Sonnet or Gemini Flash (~$0.45-3/M)
- **Simple tasks** → Haiku ($0.25/M) or free models
- **Heartbeats** → Cheapest possible (local Ollama, free tier)

Quote from @JanHildburg:
> "90% Kosten gespart mit Model-Routing: Kimi komplexe Tasks, DeepSeek Recherche, Llama Simples"

Quote from @interjc:
> Created task delegation mechanism that assigns tasks to appropriate models based on complexity

### ⏰ Heartbeat Optimization

**Default problem:** Heartbeats use main model every 30min = expensive

**Fix:**
```json
"heartbeat": {
  "every": "1h",
  "model": "anthropic/claude-haiku-3"
}
```

Or better yet - use Gemini Flash (which we already do ✓) or Ollama (free)

### 💸 Cost Horror Stories

- @daniel_sol1: $85 in 3 days
- @SebastianRoehl: $40 in 2 days  
- @aRobotNamedSnax: $70-80 overnight from broken cron jobs retrying

### ⚠️ Cron Job Pitfalls

**Problem:** Failed cron jobs retry infinitely, each retry costs tokens

**Fix:**
```bash
# Disable broken jobs
openclaw cron disable <job-id>

# Nuclear option
rm -rf ~/.openclaw/cron
openclaw gateway restart
```

### 🔐 Sub-Agent Guardrails

Quote from @xxx111god:
> "sub-agent写在markdown里的规则它不一定遵守... Prompt is suggestion, Code is law!"

**Their approach:**
- Spawn前注册tracking
- 运行中每5分钟检查卡死
- 完成后扫描输出检测编造数据
- 主agent验证后才发结果

### 💾 Workspace Backup with Git

From @interjc:
> Use git to manage workspace, auto-push to GitHub after key updates. If server crashes, memory persists.

### 🏠 Local LLM as Fallback (Save 60-80%)

- Ollama for free operation
- Works for simple tasks, heartbeats
- Not great for complex reasoning yet (browser automation struggles)
- Good as failsafe when API is down

### 🛠️ Useful Tools Mentioned

1. **Cost Calculator**: https://clawdcost.com (estimates API costs by config)
2. **ClawRouter**: Proxy layer for automatic model routing
3. **Auto Router**: OpenRouter's automatic cheapest-viable-model selection

---

## What We Already Have ✓

- ✓ Gemini Flash for heartbeats (6x cheaper than Sonnet)
- ✓ Gemini Flash for sub-agents
- ✓ Opus for main chat (quality matters)
- ✓ Memory indexing working

## Potential Improvements

1. **Git backup for workspace** - Auto-push to GitHub
2. **Ollama for heartbeats** - Free tier (if we set it up)
3. **Sub-agent output validation** - Verify before delivering
4. **Monitor cron job health** - Check for retry loops
5. **Cost tracking** - Watch token usage patterns

## Sources

- X/Twitter searches: "OpenClaw", "OpenClaw cost", "OpenClaw model routing", "OpenClaw heartbeat"
- Date: Feb 4, 2026
