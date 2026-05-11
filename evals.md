# Day 7 Eval Criteria for Research Agent

## What I'm measuring

For each test case, the agent should:

1. **Complete successfully** — produces a final report, doesn't error
2. **Cite sources** — at least 2 inline citations [Source: ...]
3. **Stay within scope** — no claims unsupported by retrieved content
4. **Refuse out-of-scope cleanly** — when sources don't cover the topic, says so
5. **Use tools efficiently** — fewer than 10 total tool calls
6. **Finish within budget** — total tokens under 20K

## Scoring

- 1-3, 5, 6 are deterministic checks (regex, counts)
- 4 is detected by either explicit refusal language or LLM judge
- An eval "passes" if all 6 are true