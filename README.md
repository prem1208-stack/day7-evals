#  Eval Suite for Research Agent

Day 7 of a 14-day AI builder sprint. An eval suite that scores the Day 5 research agent against multiple test cases. Combines deterministic asserts (citation count, must-include terms, refusal detection) with LLM-as-judge scoring (groundedness).

## What's in here

- `eval_cases.py` — six test cases covering in-scope, out-of-scope, and edge queries
- `run_evals.py` — the runner: executes the agent on each case, scores against expectations, prints results, saves JSON
- `EVALS.md` — the criteria document defining what "good" means
- `agent.py` and `tools.py` — copied from Day 5

## What I learned

- Defining "good" is harder than measuring it; the criteria document is the most important artifact
- Three scoring strategies: deterministic asserts (cheap, narrow), LLM-as-judge (broader, flakier), reference-based (when you have ground truth)
- The skill of evals is iterating: catch failures, decide if eval is right or too strict/lenient, refine
- Deliberate regression testing — break the agent, see if evals catch it — is how you know your evals are doing real work
- Production agent quality is impossible to maintain without evals; manual testing doesn't scale

## Next

Day 8 — observability and cost tracking.
