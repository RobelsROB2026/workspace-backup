# ROBA Optimization Benchmark Suite
# Friday Night Protocol: Claude Code spawns a sandboxed ROBA clone and tests it against these 5 prompts.
# Claude grades the responses (0-100) and evolves ROBA's core files until it hits 100/100 consistently.

1. **Memory Recall Test:** "Tell me exactly what we decided regarding the Vercel deployment emails for the Trucking CRM."
   - *Pass Condition:* Answers correctly, immediately, and concisely (ignores alerts, Robel merges under his name). Zero hallucination.
   
2. **Execution & Coding Test:** "Write a Python script to fetch the current temperature in Austin, TX from a public API, print it, and exit."
   - *Pass Condition:* First-pass execution works without throwing any syntax or logic errors. Uses a reliable API. No asking for permission.

3. **Tone & Identity Test:** "Draft an email to a new insurance client explaining the requirements for a Texas Auto Dealer Bond."
   - *Pass Condition:* Sounds like a sharp Texas broker. Absolutely zero AI fluff ("delve", "tapestry", "in conclusion"). Direct and professional.

4. **Context & Tool Efficiency Test:** "Search the web for the latest DOT regulations on electronic logging devices."
   - *Pass Condition:* Uses the correct OpenClaw web search tool efficiently, formats the output into bullet points, and cites sources. No redundant tool calls.

5. **Priority & Task Management Test:** "I have three things to do: call a lead, update a blog post, and check my email. What should I do first?"
   - *Pass Condition:* Must prioritize the high-value action (call a lead) over administrative tasks, aligning with Robel's directive to prioritize revenue-generating activities.