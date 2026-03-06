const fs = require('fs');
let mem = fs.readFileSync('MEMORY.md', 'utf-8');

mem = mem.replace(
  "For all complex execution, especially coding and terminal tasks, I must spawn Claude Code via `sessions_spawn(runtime=\"acp\", agentId=\"claude\")` and delegate the work.",
  "For all complex execution, especially coding and terminal tasks, I must spawn Claude Code via the terminal using `exec(pty: true, command: \"claude 'Your task'\")` and delegate the work."
);

fs.writeFileSync('MEMORY.md', mem);
