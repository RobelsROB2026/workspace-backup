const fs = require('fs');
let soul = fs.readFileSync('SOUL.md', 'utf-8');

soul = soul.replace(
  "I design the architecture, plan the steps, and then spawn Claude Code (via `sessions_spawn(runtime=\"acp\", agentId=\"claude\")`) to execute it.",
  "I design the architecture, plan the steps, and then spawn Claude Code (via the terminal using `exec(pty: true, command: \"claude ...\")`) to execute it."
);

fs.writeFileSync('SOUL.md', soul);
