"""Run the eval suite against the research agent."""

import os
import json
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from anthropic import Anthropic

# Import your agent
from agent import run_agent
from eval_cases import EVAL_CASES

load_dotenv()
judge_client = Anthropic()
JUDGE_MODEL = "claude-haiku-4-5-20251001"  # cheap fast model for judging


def run_single_case(case: dict) -> dict:
    """Run the agent on one test case and capture metadata."""
    print(f"\n{'='*60}")
    print(f"Running case: {case['name']}")
    print(f"Request: {case['request'][:100]}...")
    
    # We need to track metadata the agent doesn't natively expose:
    # - number of tool calls
    # - total tokens used
    # We'll capture these by wrapping the agent run
    
    # For now, just call run_agent and capture the report
    try:
        report = run_agent(case["request"])
        return {
            "case_name": case["name"],
            "request": case["request"],
            "report": report or "",
            "success": report is not None,
            "error": None,
        }
    except Exception as e:
        return {
            "case_name": case["name"],
            "request": case["request"],
            "report": "",
            "success": False,
            "error": str(e),
        }


def check_must_include(report: str, terms: list[str]) -> tuple[bool, list[str]]:
    """Check that all required terms appear in the report (case-insensitive)."""
    report_lower = report.lower()
    missing = [t for t in terms if t.lower() not in report_lower]
    return len(missing) == 0, missing


def check_must_not_include(report: str, terms: list[str]) -> tuple[bool, list[str]]:
    """Check that none of the forbidden terms appear in the report."""
    report_lower = report.lower()
    found = [t for t in terms if t.lower() in report_lower]
    return len(found) == 0, found


def count_citations(report: str) -> int:
    """Count [Source: ...] style citations in the report."""
    import re
    return len(re.findall(r'\[Source[:\s][^\]]+\]', report))


def detect_refusal(report: str, refusal_keywords: list[str]) -> bool:
    """Check if the report shows signs of hedging or refusal."""
    report_lower = report.lower()
    return any(kw.lower() in report_lower for kw in refusal_keywords)


def llm_judge_grounded(report: str, request: str) -> dict:
    """Use Claude as a judge to assess whether the report is grounded.
    
    Returns a dict with score (1-5) and reasoning.
    """
    judge_prompt = f"""You are evaluating whether a research agent's report is well-grounded in its sources.

USER REQUEST: {request}

AGENT'S REPORT:
{report}

Score the report on this scale:
1 = Mostly hallucinated or unsupported claims
2 = Significant unsupported content
3 = Some unsupported content, mostly grounded
4 = Mostly grounded, occasional unsupported claim
5 = Fully grounded, all claims attributed to sources

Respond ONLY with valid JSON in this exact format:
{{"score": <1-5>, "reasoning": "<one sentence>"}}"""
    
    try:
        response = judge_client.messages.create(
            model=JUDGE_MODEL,
            max_tokens=200,
            messages=[{"role": "user", "content": judge_prompt}],
        )
        text = response.content[0].text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        return {"score": 0, "reasoning": f"Judge failed: {str(e)}"}


def evaluate_case(case: dict, run_result: dict) -> dict:
    """Score a case against its expectations."""
    expectations = case["expectations"]
    report = run_result["report"]
    checks = []
    
    # Check 1: Did the run succeed?
    checks.append({
        "name": "completed_successfully",
        "passed": run_result["success"],
        "detail": run_result.get("error", "ok"),
    })
    
    if not run_result["success"]:
        # If the agent errored, no point checking content
        return {
            "case_name": case["name"],
            "case_type": case["case_type"],
            "checks": checks,
            "all_passed": False,
            "report_excerpt": "",
        }
    
    # Check 2: Required terms present
    if expectations.get("must_include"):
        passed, missing = check_must_include(report, expectations["must_include"])
        checks.append({
            "name": "must_include",
            "passed": passed,
            "detail": f"Missing: {missing}" if not passed else "all present",
        })
    
    # Check 3: Forbidden terms absent
    if expectations.get("must_not_include"):
        passed, found = check_must_not_include(report, expectations["must_not_include"])
        checks.append({
            "name": "must_not_include",
            "passed": passed,
            "detail": f"Found forbidden: {found}" if not passed else "all absent",
        })
    
    # Check 4: Citation count
    if "min_citations" in expectations:
        cite_count = count_citations(report)
        passed = cite_count >= expectations["min_citations"]
        checks.append({
            "name": "min_citations",
            "passed": passed,
            "detail": f"{cite_count} citations (required: {expectations['min_citations']})",
        })
    
    # Check 5: Refusal/hedging for out-of-scope
    if expectations.get("should_refuse_or_hedge"):
        keywords = expectations.get("refusal_keywords", [])
        refused = detect_refusal(report, keywords)
        checks.append({
            "name": "refused_or_hedged",
            "passed": refused,
            "detail": "Refusal language detected" if refused else "No refusal/hedging found",
        })
    
    # Check 6: LLM-as-judge grounding score
    judge_result = llm_judge_grounded(report, case["request"])
    judge_passed = judge_result["score"] >= 3  # threshold of 3 out of 5
    checks.append({
        "name": "llm_judge_grounded",
        "passed": judge_passed,
        "detail": f"Score: {judge_result['score']}/5 — {judge_result['reasoning']}",
    })
    
    all_passed = all(c["passed"] for c in checks)
    
    return {
        "case_name": case["name"],
        "case_type": case["case_type"],
        "checks": checks,
        "all_passed": all_passed,
        "report_excerpt": report[:300] + "..." if len(report) > 300 else report,
    }


def main():
    print(f"\n{'#'*60}")
    print(f"# Eval suite — {len(EVAL_CASES)} cases")
    print(f"# Started: {datetime.now().isoformat()}")
    print(f"{'#'*60}\n")
    
    results = []
    for case in EVAL_CASES:
        run_result = run_single_case(case)
        eval_result = evaluate_case(case, run_result)
        results.append(eval_result)
        
        # Print case result
        status = "✓ PASS" if eval_result["all_passed"] else "✗ FAIL"
        print(f"\n{status}: {eval_result['case_name']}")
        for check in eval_result["checks"]:
            check_status = "  ✓" if check["passed"] else "  ✗"
            print(f"{check_status} {check['name']}: {check['detail']}")
    
    # Aggregate stats
    total = len(results)
    passed = sum(1 for r in results if r["all_passed"])
    
    print(f"\n{'#'*60}")
    print(f"# RESULTS: {passed}/{total} passed ({100*passed//total}%)")
    print(f"{'#'*60}")
    
    # Save full results to a JSON file for later analysis
    Path("results").mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = Path(f"results/eval_run_{timestamp}.json")
    results_file.write_text(json.dumps(results, indent=2))
    print(f"\nFull results saved to {results_file}")
    
    # Exit with non-zero if any failed (useful for CI later)
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()