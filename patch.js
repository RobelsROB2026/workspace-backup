const fs = require('fs');
let mem = fs.readFileSync('MEMORY.md', 'utf-8');

// Update gws tool status
mem = mem.replace(
  "- **New Tool**: Installed Google Workspace CLI (`gws`) via npm + 107 AI Agent Skills.\n  - Purpose: Full Google Workspace automation (Gmail, Drive, Docs, Calendar, Sheets) via structured JSON + MCP.\n  - Status: Awaiting `gws auth setup` OAuth2 credential setup by Robel.",
  "- **Google Workspace CLI (`gws`)**: Installed and **FULLY AUTHENTICATED** (robake2006@gmail.com). We now have persistent, unattended access at all times to Drive, Gmail, Calendar, Docs, and Sheets. Replaces `gog`."
);

// Update Lead Management System goal
mem = mem.replace(
  "- **Goal**: Sync to a live Google Sheet once `gog` OAuth is configured.",
  "- **Goal**: Sync to a live Google Sheet using `gws sheets` now that we have persistent Workspace access."
);

// Update FMCSA Dashboard
mem = mem.replace(
  "- **Status**: Initial structure and architecture defined. ETL pipeline in development.",
  "- **Status**: Initial structure and architecture defined. ETL pipeline in development. (Note: Can now export directly to Google Sheets using `gws` if needed)."
);

fs.writeFileSync('MEMORY.md', mem);
console.log("MEMORY.md updated.");
