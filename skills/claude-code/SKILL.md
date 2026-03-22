---
name: claude-code
description: How ROBA should use the claude CLI as a coding and execution engine — spawning it via exec for file edits, code generation, bash commands, git operations, and multi-step agentic tasks.
---

# Claude Code — ROBA's Coding Muscle

## Description

Claude Code (`claude`) is a full-featured agentic coding CLI powered by Claude Sonnet/Opus. It can read and write files, run bash commands, search codebases, create git commits, open PRs, run tests, and execute multi-step software engineering tasks autonomously. ROBA uses it as an **execution engine** — delegating all coding, scripting, and file manipulation tasks to it via the `exec` tool.

Claude Code is composable: it follows Unix philosophy, accepts piped input, and outputs structured JSON. It has a powerful permission system, and can run in fully non-interactive ("headless") mode, making it ideal for automation.

---

## Use When

- Writing, editing, or refactoring code in any language
- Reading and analyzing codebases (finding files, understanding architecture)
- Running bash commands, tests, or build processes
- Creating git commits, branches, or pull requests
- Fixing bugs (paste error → claude traces + fixes)
- Generating boilerplate, migrations, or bulk file changes
- Analyzing log files, data files, or error traces
- Any task requiring file system access and code execution
- Automating multi-step software workflows end-to-end
- Reviewing code for security issues, bugs, or style violations
- Generating documentation or comments

---

## Don't Use When

- Simple text generation with no file/code involvement (use the model directly)
- Tasks that are fully handled by a more specialized OpenClaw skill
- Real-time interactive sessions where back-and-forth with a human is needed (claude's headless mode is one-shot; use interactive mode for that)
- Tasks that require a GUI or browser interaction not addressable by code
- When the working directory doesn't exist or isn't set up (claude needs a valid `cwd`)

---

## Core CLI Modes

### 1. Interactive (default)
```bash
claude                          # Start REPL in current dir
claude "explain this project"   # Start with initial prompt
claude -n "auth-refactor"       # Named session
```
Used for exploration and conversation. Not useful for ROBA's automation needs.

### 2. Headless / Print Mode (`-p`) — ROBA's PRIMARY MODE
```bash
claude -p "your task here"
```
- Runs task non-interactively and exits
- No session saved by default
- Outputs plain text (default), JSON, or streaming JSON
- THIS IS WHAT ROBA USES via the exec tool

### 3. Continue / Resume
```bash
claude -c                        # Continue most recent session in cwd
claude -r "session-name"         # Resume named session
claude -c -p "follow-up task"    # Continue via headless mode
```

---

## Critical CLI Flags

### Permission Control (MOST IMPORTANT FOR AUTOMATION)

| Flag | Behavior | When ROBA Uses It |
|------|----------|-----------------|
| `--dangerously-skip-permissions` | Skips ALL permission prompts (except `.git`, `.claude`, `.vscode`, `.idea` dirs) | Use for fully automated tasks where no human is watching |
| `--permission-mode bypassPermissions` | Same as above but set as a mode, composable with other flags | Preferred for scripted/headless runs |
| `--permission-mode plan` | Read-only: can analyze but NOT modify files or run commands | Use for safe exploration and planning |
| `--permission-mode acceptEdits` | Auto-accepts file edit permissions | Use when file writes are needed but Bash is risky |
| `--allowedTools "Bash,Edit,Read"` | Restricts which tools claude can use (allowlist) | Scope permissions for specific tasks |
| `--disallowedTools "Bash"` | Blocks specific tools | Prevent bash execution for read-only analysis |

**ROBA's go-to for automation:**
```bash
claude -p "task" --dangerously-skip-permissions
```

### Output Format

| Flag | Output | When to Use |
|------|--------|-------------|
| `--output-format text` | Plain text (default) | Simple tasks, human-readable output |
| `--output-format json` | JSON array of messages with metadata (cost, duration) | When ROBA needs to parse results or check cost |
| `--output-format stream-json` | Newline-delimited JSON stream | Real-time processing of long tasks |

**For ROBA parsing results:**
```bash
claude -p "list all API endpoints" --output-format json
```

### Context and Scope

| Flag | Purpose |
|------|---------|
| `--add-dir ../other-repo` | Give claude access to additional directories |
| `--model sonnet` | Force specific model (`sonnet`, `opus`, `haiku`, or full ID) |
| `--effort high` | Set reasoning depth (`low`, `medium`, `high`, `max`) |
| `--max-turns 5` | Limit agentic turns (prevents runaway sessions) |
| `--max-budget-usd 2.00` | Hard dollar cap on API spend |
| `--no-session-persistence` | Don't save session to disk (clean runs) |
| `--system-prompt "..."` | Replace entire system prompt (full control) |
| `--append-system-prompt "..."` | Add to default system prompt (preserves capabilities) |

### Session Management

| Flag | Purpose |
|------|---------|
| `-n "name"` or `--name "name"` | Name the session for later resumption |
| `-c` or `--continue` | Resume most recent session in cwd |
| `-r "name"` or `--resume "name"` | Resume session by name or UUID |
| `--fork-session` | Fork a session (new ID, preserves history) |
| `-w "feature-name"` | Start in isolated git worktree |

### Subagents and Agents

| Flag | Purpose |
|------|---------|
| `--agent my-custom-agent` | Run session as a specific subagent |
| `--agents '{"name":{"description":"...","prompt":"..."}}` | Define inline subagents via JSON |

---

## How to Structure Prompts for Claude Code

Claude Code works best with **specific, verifiable, self-contained tasks**. The quality of ROBA's prompt directly determines result quality.

### Golden Rules (Based on Anthropic's Best Practices)

1. **Bash is All You Need** — Give Claude broad bash access (`--dangerously-skip-permissions`) and encourage it to use bash to solve problems organically. "Use the bash tool more" is Anthropic's top advice for agents.
2. **Your Agent Should Use a File System** — Explicitly tell Claude to write its plans, intermediate data, and thoughts to files (e.g., `notes/scratchpad.md`) rather than holding everything in its context window. This prevents context bloat and data loss.
3. **Playgrounds for Visual Iteration** — When doing UI or frontend work, instruct Claude to build a quick HTML/JS "playground" to iterate visually before integrating into the main app.
4. **Leverage Prompt Caching** — Claude Code supports prompt caching. Keeping sessions focused and re-using context (via files) makes it significantly faster and cheaper.
5. **State the goal, not the steps** — Claude figures out how. "Fix the login bug" is fine; you don't need to explain how to grep for it.
6. **Include the working directory context** — Always set `cwd` in exec calls.
7. **Provide verification criteria** — Tell claude how to verify success: "run the tests", "check the output", "confirm the file exists".
8. **One clear task per invocation** — Don't chain unrelated work into one prompt. Split into multiple exec calls if needed.

### Prompt Templates ROBA Should Use

**Bug fix:**
```
Fix the error in src/sync.py: [paste error]. Trace the root cause,
implement a fix, and verify by running python3 src/sync.py --dry-run.
Do not suppress errors, fix the underlying issue.
```

**Code generation:**
```
Write a Python script at scripts/export_leads.py that:
1. Connects to Postgres using DATABASE_URL from .env
2. Queries leads table where status='active'
3. Exports to CSV at /tmp/leads.csv
4. Prints row count on completion

Run it to verify it works before finishing.
```

**Refactoring:**
```
Refactor src/tagger.py to replace the row-by-row UPDATE loop (lines 45-60)
with a bulk ANY::uuid[] update. Maintain identical behavior.
Run the test suite afterward to verify.
```

**Codebase analysis (read-only):**
```
Analyze this codebase and identify all database queries that lack
index hints or could cause full table scans. List file:line for each.
Do not modify any files.
```

**Git workflow:**
```
Stage all modified files, write a descriptive commit message summarizing
the sync performance improvements, and commit. Do not push.
```

**Multi-step task:**
```
1. Write your detailed plan and intermediate thoughts to notes/sync_plan.md first (agents should use a file system).
2. Read sync_daily_optimized.py and understand the current architecture.
3. Identify the top 3 performance bottlenecks using bash profiling tools.
4. Implement the highest-impact optimization.
5. Run a benchmark comparing before/after.
6. Commit the change if improvement is >10%.
```

**Frontend Playground Task:**
```
Create a standalone HTML/JS playground in /tmp/playground.html to visually iterate on the new dashboard widget. Use your frontend-design skill. Once it looks perfect in the browser, integrate the React version into src/components/Dashboard.tsx.
```

### Anti-Patterns to Avoid

- **Vague goals**: "make it better" → claude will do something arbitrary
- **Missing verification**: no way for claude to confirm success = silent failures
- **Over-specified steps**: listing every grep to run prevents claude from finding better solutions
- **Unbounded exploration**: "investigate everything" → context explosion, slow, expensive
- **Chaining unrelated tasks**: "fix the bug AND also write docs AND also refactor" → messy

---

## Spawning Claude via exec Tool

ROBA uses the OpenClaw `exec` tool to invoke `claude`. Here are patterns:

### Basic headless invocation
```json
{
  "tool": "exec",
  "command": "claude",
  "args": ["-p", "explain the main architecture of this project", "--dangerously-skip-permissions"],
  "cwd": "/Users/roba/research/trucking"
}
```

### With output format for parsing
```json
{
  "tool": "exec",
  "command": "claude",
  "args": [
    "-p", "list all Python files that import psycopg2 and their line counts",
    "--output-format", "json",
    "--dangerously-skip-permissions",
    "--no-session-persistence"
  ],
  "cwd": "/Users/roba/research/trucking"
}
```

### Budget-capped task
```json
{
  "tool": "exec",
  "command": "claude",
  "args": [
    "-p", "optimize the SQL query in sync_daily_optimized.py for the FMCSA batch fetch. Run a benchmark before and after.",
    "--dangerously-skip-permissions",
    "--max-budget-usd", "3.00",
    "--max-turns", "20"
  ],
  "cwd": "/Users/roba/research/trucking"
}
```

### Piping data
```bash
# In a shell exec call:
tail -200 /var/log/app.log | claude -p "identify any anomalies or errors" --dangerously-skip-permissions
```

```json
{
  "tool": "exec",
  "command": "bash",
  "args": ["-c", "tail -200 /var/log/app.log | claude -p 'identify anomalies' --dangerously-skip-permissions"],
  "cwd": "/Users/roba"
}
```

### Read-only analysis (plan mode)
```json
{
  "tool": "exec",
  "command": "claude",
  "args": [
    "-p", "analyze the nationality tagger codebase and propose the top 3 optimization opportunities with estimated impact",
    "--permission-mode", "plan",
    "--output-format", "text"
  ],
  "cwd": "/Users/roba/research/trucking"
}
```

### Named session for multi-step work
```json
{
  "tool": "exec",
  "command": "claude",
  "args": [
    "-n", "sync-gen11-research",
    "-p", "Start exploring sync_daily_gen10.py and identify opportunities for a Gen11 implementation.",
    "--dangerously-skip-permissions"
  ],
  "cwd": "/Users/roba/research/trucking"
}
```

Then resume it later:
```json
{
  "tool": "exec",
  "command": "claude",
  "args": [
    "-r", "sync-gen11-research",
    "-p", "Continue: implement the Gen11 changes we discussed.",
    "--dangerously-skip-permissions"
  ],
  "cwd": "/Users/roba/research/trucking"
}
```

### Isolated worktree for risky changes
```json
{
  "tool": "exec",
  "command": "claude",
  "args": [
    "-w", "gen11-experiment",
    "-p", "Implement and benchmark the Gen11 sync changes. Do not merge.",
    "--dangerously-skip-permissions"
  ],
  "cwd": "/Users/roba/research/trucking"
}
```

### Inline custom subagent
```json
{
  "tool": "exec",
  "command": "claude",
  "args": [
    "--agents", "{\"perf-analyzer\":{\"description\":\"Performance analysis specialist\",\"prompt\":\"You are a Python performance expert. Analyze code for bottlenecks, measure with cProfile/timeit, and propose concrete optimizations with expected speedups.\",\"tools\":[\"Read\",\"Bash\",\"Grep\",\"Glob\"]}}",
    "-p", "Analyze sync_daily_optimized.py for performance bottlenecks",
    "--dangerously-skip-permissions"
  ],
  "cwd": "/Users/roba/research/trucking"
}
```

---

## Permission Modes — Decision Guide

```
Need to READ files only?
  → --permission-mode plan
  → Safe, no risk of side effects

Need to WRITE files but not run commands?
  → --permission-mode acceptEdits
  → Safe for code generation

Need FULL autonomy (read + write + bash)?
  → --dangerously-skip-permissions
  → Use in trusted dirs only

Need to SCOPE what tools are available?
  → --allowedTools "Read,Grep,Glob,Bash(git *)"
  → Surgical permission control
```

**WARNING**: `--dangerously-skip-permissions` allows:
- Writing any file in the working directory
- Running any bash command
- Creating git commits and branches
- Installing packages

It does NOT allow (still prompts):
- Writing to `.git/`, `.claude/`, `.vscode/`, `.idea/`

---

## Cost and Token Management

- Use `--max-budget-usd N` for expensive tasks to prevent runaway costs
- Use `--max-turns N` to bound agentic loops (default: unlimited)
- Use `--model haiku` for cheap analysis tasks (fast, cheap, good enough for search/grep)
- Use `--model opus` for complex reasoning, architecture decisions, hard bugs
- Use `--model sonnet` (default) for most tasks — best balance
- Use `--no-session-persistence` for throwaway runs (saves disk space)
- Use `--output-format json` to get cost metadata in the response

---

## CLAUDE.md — Persistent Instructions

Claude reads `CLAUDE.md` in the project directory at session start. ROBA can create or update this file to give claude persistent project context:

```bash
# Create project instructions
claude -p "Create a CLAUDE.md in this directory with: the project structure, key scripts and what they do, database connection info (use env vars, not hardcoded), and the preferred Python style (python3, type hints, no pandas)." \
  --dangerously-skip-permissions \
  --cwd /Users/roba/research/trucking
```

**What to put in CLAUDE.md:**
- Build/run commands (`python3 sync_daily_optimized.py`)
- Testing approach
- Code style rules that differ from defaults
- Architecture decisions and key file locations
- Non-obvious env var requirements
- Common gotchas

**What NOT to put:**
- Things claude can figure out from reading code
- Standard Python/language conventions
- File-by-file descriptions (too verbose)

---

## Subagents — Delegating Within Claude

When ROBA spawns claude for a complex task, claude itself can spawn subagents internally. ROBA doesn't need to manage this — but can influence it:

- `"use a subagent to research X"` — keep investigation out of main context
- `"investigate X and Y in parallel using separate subagents"` — parallelism
- `"use the Explore subagent to find all files related to authentication"` — built-in specialist
- `"run this in the background"` — non-blocking subagent

Built-in subagents ROBA can request:
- **Explore** — Fast, read-only codebase search (Haiku model)
- **Plan** — Read-only planning and analysis
- **general-purpose** — Full capabilities, all tools

---

## Common ROBA Workflows

### "Fix this error"
```bash
claude -p "$(cat error.txt)" --append-system-prompt "Fix the root cause. Run the failing command to verify the fix." --dangerously-skip-permissions
```

### "Optimize this script"
```bash
claude -p "Profile sync_daily_optimized.py and implement the single highest-impact optimization. Run before/after benchmarks and report the improvement. Commit if >20% faster." --dangerously-skip-permissions
```

### "Research before touching"
```bash
claude -p "Analyze the tagger architecture. What are the 3 riskiest parts to modify? Do not change any files." --permission-mode plan
```

### "Bulk migration"
```bash
# Generate file list first, then loop
for f in $(find . -name "*.py" | head 20); do
  claude -p "Migrate $f from requests to httpx. Maintain identical behavior. Run any tests." \
    --dangerously-skip-permissions \
    --no-session-persistence \
    --max-turns 10
done
```

### "Write and run tests"
```bash
claude -p "Write pytest tests for tag_nationality_historical.py covering: batch processing, error handling on bad Gemini response, and database write failures. Run them. Fix any failures." --dangerously-skip-permissions
```

---

## Output Parsing (JSON Mode)

When using `--output-format json`, the response is a JSON array. The last element with `type: "result"` contains the final answer:

```bash
result=$(claude -p "count lines in sync_daily_optimized.py" --output-format json --no-session-persistence)
# Parse with jq:
echo "$result" | jq -r '.[] | select(.type=="result") | .result'
# Cost info:
echo "$result" | jq -r '.[] | select(.type=="result") | {cost: .cost_usd, turns: .num_turns}'
```

---

## Key Limitations

- **No nested subagent spawning**: subagents cannot spawn other subagents
- **Context window**: long sessions degrade; use `/clear` or start fresh for unrelated tasks
- **bypassPermissions still protects**: `.git`, `.claude`, `.vscode`, `.idea` directories always prompt
- **Session persistence**: by default, sessions are saved to disk at `~/.claude/projects/`; use `--no-session-persistence` for clean throwaway runs
- **Headless only**: `-p` mode cannot do interactive back-and-forth; each call is a single turn (unless using `--continue`)
- **Rate limits**: Anthropic API rate limits apply; `--max-budget-usd` and `--max-turns` are ROBA's guardrails

## Claude Code Plugins & Native Skills (Official Marketplace)

Claude Code has its own native ecosystem of "plugins" and "skills" officially supported by Anthropic. 

**Important:** Claude Code will *only* leverage specialized UI/UX skills if the relevant plugin is installed first.

### Discovering and Installing Official Plugins

ROBA can explore and install official plugins directly via the `claude plugin` commands:

1. **List available official plugins:**
   ```bash
   claude plugin list --available --json
   ```
   *Note: This lists plugins from the `claude-plugins-official` marketplace, including tools like `frontend-design` (for UI/UX), `github`, `supabase`, `playwright`, `coderabbit`, etc.*

2. **Install a plugin (globally for the user):**
   ```bash
   claude plugin install frontend-design
   ```

### How Claude Uses Skills

Anthropic's "Skills" are specialized, domain-specific instructions that automatically inject into Claude's context when relevant. 

Once you install a skill like `frontend-design`:
1. It registers a `skill.md` file in Claude Code's internal registry.
2. When you spawn Claude Code and ask it to build a UI/UX component, Claude's routing layer *automatically* matches your request to the `frontend-design` skill.
3. Claude adopts the specific persona and guidelines (e.g., "avoid generic AI aesthetics, use bold typography, implement distinctive motion").

**ROBA's Workflow for Specialized Tasks (Like UI/UX):**
If Robel asks for a high-quality UI/UX task, ROBA should:
1. First, ensure the `frontend-design` plugin is installed:
   `exec(command: "claude plugin install frontend-design")`
2. Then, invoke `claude` using `exec` and EXPLICITLY TELL IT to use the skill:
   `exec(command: "claude -p 'Build a React dashboard component for the trucking CRM. Make sure to leverage your frontend-design skill to make it visually striking.' --dangerously-skip-permissions")`

### MCP Servers and Other Plugins
Other plugins (like `github` or `playwright`) install **MCP Servers**. These provide Claude with actual functional tools (like `take_screenshot` or `create_pull_request`). Once installed via `claude plugin install playwright`, Claude Code will autonomously decide when to use those tools based on the prompt.

### Explicit Invocation (The Golden Rule)
While Claude Code *can* automatically route to skills, **ROBA MUST ALWAYS EXPLICITLY TELL CLAUDE TO USE THE SKILL in the prompt.** This ensures the skill is guaranteed to trigger and doesn't get skipped by Claude's routing layer.

**Wrong (Implicit):**
`claude -p "Build a React component"`

**Right (Explicit):**
`claude -p "Build a React component. You must use your 'frontend-design' skill to ensure it has a production-grade, distinctive aesthetic."`

Whenever delegating a task to Claude Code, ROBA must:
1. Identify if an official Claude plugin exists for the task (UI, PR reviews, Supabase, Github, etc.).
2. Ensure the plugin is installed.
3. Explicitly name-drop the skill/plugin in the `-p` prompt payload.
