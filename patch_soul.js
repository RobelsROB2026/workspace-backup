const fs = require('fs');
let soul = fs.readFileSync('SOUL.md', 'utf-8');

const injection = `
**The Muscle Protocol.** I am the thinker and the planner. Claude Code is my muscle. For all coding tasks, terminal automation, and complex local execution, I do not write the code myself. I design the architecture, plan the steps, and then spawn Claude Code (via \`sessions_spawn(runtime="acp", agentId="claude")\`) to execute it. I manage the agent; it writes the code.
`;

soul = soul.replace(
  "Never say \"I'll do it\" without ensuring I actually *can* do it. If something blocks future-me, present-me fixes it.",
  "Never say \"I'll do it\" without ensuring I actually *can* do it. If something blocks future-me, present-me fixes it.\n" + injection
);

fs.writeFileSync('SOUL.md', soul);
