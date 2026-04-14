# MemPalace Installation — 2026-04-12

Robel asked Claude Code to install MemPalace as a local AI memory system for OpenClaw.

## What is MemPalace?

A local, offline AI memory system that stores conversations and project data in a hierarchical structure (wings/halls/rooms/drawers). Uses ChromaDB for vector search — no cloud API calls, no costs, lightweight on RAM (~100-400MB).

- 19 MCP tools for search, knowledge graph, diary, and palace traversal
- 96.6% recall on LongMemEval benchmark
- Temporal knowledge graph with entity relationships and time-validity
- Fully offline — embeddings computed locally via Sentence Transformers

## What Was Installed

- **Package**: `mempalace 3.1.0` via pip (user install)
- **ChromaDB**: pinned to `>=0.4.0,<1` to avoid ARM64 segfault (issue #74)
- **Binary location**: `/Users/roba/Library/Python/3.9/bin/mempalace`
- **PATH**: Added `$HOME/Library/Python/3.9/bin` to `.zshrc`

## OpenClaw Integration

### MCP Server
Configured in `openclaw.json` under `mcp.servers`:
```json
{
  "mempalace": {
    "command": "python3",
    "args": ["-m", "mempalace.mcp_server"]
  }
}
```

### Palace Location
- Palace data: `~/.mempalace/palace/`
- Workspace config: `~/.openclaw/workspace/mempalace.yaml`
- Entities: `~/.openclaw/workspace/entities.json`

### Palace Structure
Initialized from `/Users/roba/.openclaw/workspace` with 1712 files across 11 rooms:
- research, memory, claude, projects, test_claude_supervisor, agents, documentation, state, scripts, skills, general

## How to Use (Session Protocol)

1. **On wake-up**: Call `mempalace_status` to load palace overview
2. **Before responding** about any person/project/past event: call `mempalace_search` first
3. **If unsure** about a fact: query rather than guess
4. **After each session**: Call `mempalace_diary_write` to record what happened
5. **When facts change**: Call `mempalace_kg_invalidate` on old fact, then `mempalace_kg_add` for new

## Available MCP Tools (19)

`mempalace_status`, `mempalace_search`, `mempalace_list_wings`, `mempalace_list_rooms`, `mempalace_get_taxonomy`, `mempalace_check_duplicate`, `mempalace_get_aaak_spec`, `mempalace_add_drawer`, `mempalace_delete_drawer`, `mempalace_kg_query`, `mempalace_kg_add`, `mempalace_kg_invalidate`, `mempalace_kg_timeline`, `mempalace_kg_stats`, `mempalace_traverse`, `mempalace_find_tunnels`, `mempalace_graph_stats`, `mempalace_diary_write`, `mempalace_diary_read`

## Troubleshooting

- If segfault after crash/disk-full: run `mempalace repair`
- If ChromaDB issues on ARM64: pin `chromadb<1`
- Status check: `mempalace status`
