const fs = require('fs');
let mem = fs.readFileSync('MEMORY.md', 'utf-8');

const newNote = `### Persistent Google Workspace Access (2026-03-05)
**Crucial Capability:** We now have a fully authenticated \`gws\` CLI with a refresh token. This means **I have persistent, background access to Drive, Docs, Sheets, Calendar, and Gmail at all times**. 
- I can read/write data, manage leads, and schedule events autonomously via cron jobs without needing Robel to manually authenticate or have a browser open.
- All active projects (Bonds, FMCSA, NYC Permits) can now leverage live Google Sheets or Docs for data storage and reporting.
`;

mem = mem.replace("## Things to Remember", "## Things to Remember\n\n" + newNote);
fs.writeFileSync('MEMORY.md', mem);
console.log("Added persistent access note to MEMORY.md.");
