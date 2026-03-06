const fs = require('fs');
let mem = fs.readFileSync('MEMORY.md', 'utf-8');

mem = mem.replace(
  "I must read before answering and write immediately after learning.",
  "I must read before answering and write immediately after learning.\n\n**The Muscle Protocol (2026-03-05):** Robel authenticated Claude Code in the terminal. Moving forward, I am the **thinker/planner**, and **Claude Code** is the muscle. For all complex execution, especially coding and terminal tasks, I must spawn Claude Code via `sessions_spawn(runtime=\"acp\", agentId=\"claude\")` and delegate the work. I design the architecture; Claude writes the code."
);

fs.writeFileSync('MEMORY.md', mem);
