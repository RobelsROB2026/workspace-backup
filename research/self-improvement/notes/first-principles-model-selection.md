# First Principles: Model Selection for ROB

## The Question
What model should be used for what task, based on actual capabilities and cost?

---

## Benchmark Data (Late 2025 - Early 2026)

### Top-Tier Models

| Model | SWE-bench | GPQA Diamond | τ2-bench (Agentic) | Cost (Input/Output) |
|-------|-----------|--------------|---------------------|---------------------|
| **Claude Opus 4.5** | 80.9% | 87.0% | 88.9% / 98.2% | $5 / $25 |
| **Gemini 3 Pro** | 76.2% | 91.9% | — | $2 / $12 |

### Mid-Tier Models

| Model | SWE-bench | Intelligence Index | Speed | Cost (Input/Output) |
|-------|-----------|-------------------|-------|---------------------|
| **Claude Sonnet 4.5** | 77.2% | 62.8 | Baseline | $3 / $15 |
| **Gemini 3 Flash** | 78.0% | 71.3 | 3x faster | $0.50 / $3 |

### Budget Models

| Model | Best For | Cost (Input/Output) |
|-------|----------|---------------------|
| **Claude Haiku 4.5** | Simple tasks, fast | $1 / $5 |
| **Gemini 2.5 Flash** | Bulk processing, 1M context | $0.30 / $2.50 |
| **Gemini 2.0 Flash** | Cheapest option | $0.10 / $0.40 |

---

## Key Insights

### 1. Opus 4.5 is the best for agentic/autonomous work
- 88.9% on τ2-bench-lite (agentic capabilities)
- 98.2% on τ2-bench (complex tool use)
- Best prompt injection resistance (4.7% vs 12.5% for Gemini 3 Pro)
- Best for high-stakes decisions and complex reasoning

### 2. Gemini 3 Flash beats Sonnet 4.5 on most metrics
- Higher intelligence index (71.3 vs 62.8)
- Better coding benchmark (78% vs 77.2%)
- 3x faster
- 83% cheaper ($0.50/$3 vs $3/$15)
- **This is huge** — Flash-tier pricing with Sonnet-tier performance

### 3. Gemini 3 Pro beats Claude on expert knowledge
- GPQA Diamond: 91.9% vs 87.0%
- Math (AIME 2025): 95.0%
- Better for frontend/UI work
- Still cheaper than Opus ($2/$12 vs $5/$25)

### 4. Context windows matter for research
- Gemini 2.5 Flash: 1,048,576 tokens (1M)
- Claude Sonnet: 200,000 tokens
- For large document processing, Gemini wins

---

## First Principles Analysis

### What tasks does ROB actually do?

1. **Conversations with Robel**
   - Requires: Best reasoning, nuance, judgment, personality
   - Frequency: High
   - Stakes: Medium-high (relationship quality)
   
2. **Heartbeats/routine checks**
   - Requires: Basic competence, follow instructions
   - Frequency: Regular
   - Stakes: Low
   
3. **Research synthesis**
   - Requires: Reading comprehension, summarization
   - Frequency: As needed
   - Stakes: Medium (accuracy matters)
   
4. **Analysis and decisions**
   - Requires: Deep reasoning, catching nuance
   - Frequency: As needed
   - Stakes: High

5. **Agentic tasks (spawned subagents)**
   - Requires: Autonomous problem-solving, tool use
   - Frequency: Occasional
   - Stakes: Varies

### Matching Tasks to Models

| Task | Best Model | Reasoning |
|------|------------|-----------|
| **Main chat** | Opus 4.5 | Best reasoning, nuance, personality. Worth the cost for quality relationship. |
| **Heartbeats** | Sonnet 4 or **Gemini 3 Flash** | Simple checks. Flash is 5x cheaper and actually scores higher. |
| **Research synthesis** | **Gemini 3 Flash** | 71.3 intelligence, good comprehension, 83% cheaper than Sonnet. |
| **Bulk text processing** | Gemini 2.5 Flash or 2.0 Flash | 1M context window, dirt cheap. |
| **Agentic subagents** | Opus 4.5 or Sonnet 4 | High autonomy needs best tool use. |
| **Quick lookups** | Haiku 4.5 or Gemini 2.0 Flash | Speed over depth. |

---

## Recommendation

### Current Setup Analysis

| Task | Current | Cost | Recommended | Cost | Savings |
|------|---------|------|-------------|------|---------|
| Main chat | Opus 4.5 | $5/$25 | **Keep Opus 4.5** | $5/$25 | — |
| Heartbeats | Sonnet 4 | $3/$15 | **Gemini 3 Flash** | $0.50/$3 | 83% |
| Research | Gemini 3 Flash | $0.50/$3 | **Keep Gemini 3 Flash** | $0.50/$3 | — |

### The Surprising Finding

**Gemini 3 Flash might be better than Sonnet 4 for heartbeats:**
- Higher intelligence index (71.3 vs ~60)
- Better coding benchmarks
- 6x cheaper
- 3x faster

The only reason to keep Sonnet for heartbeats is consistency with the Claude ecosystem. But from pure performance/cost, Gemini 3 Flash wins.

### Final Recommendation

1. **Main conversations: Opus 4.5** — No change. Best reasoning, personality, agentic capability.

2. **Heartbeats: Could switch to Gemini 3 Flash** — Better benchmarks, much cheaper. Test this.

3. **Research synthesis: Gemini 3 Flash** — Already optimal choice.

4. **Bulk processing: Gemini 2.0/2.5 Flash** — When dealing with massive documents.

5. **Complex subagents: Opus 4.5** — When autonomy and tool use matter.

6. **Simple subagents: Gemini 3 Flash** — When task is straightforward.

---

## The Meta-Insight

The model landscape has shifted. Flash-tier models are now competitive with previous-generation flagship models. Gemini 3 Flash in particular offers:
- Flagship-level intelligence (71.3 index)
- Superior speed (3x faster)
- Fraction of the cost (83% cheaper)

For most tasks that don't require Opus-level reasoning, Gemini 3 Flash is the new optimal choice.

---

*Last updated: 2026-02-02*
*Sources: Google search results, Artificial Analysis, SWE-bench, τ2-bench, GPQA Diamond benchmarks*
