"""Test cases for the research agent eval suite."""

# Each case is a dict with:
# - name: short identifier
# - request: what to send to the agent
# - expectations: dict of properties we expect to be true
# - case_type: 'in_scope' or 'out_of_scope'

EVAL_CASES = [
    # === In-scope cases — sources should cover these ===
    {
        "name": "india_q_commerce_overview",
        "request": "Give me a brief on the current state of quick commerce in India.",
        "case_type": "in_scope",
        "expectations": {
            "min_citations": 2,
            "max_tool_calls": 10,
            "max_tokens": 20000,
            "must_include": ["India", "quick commerce"],
            "must_not_include": [],
        },
    },
    {
        "name": "compare_blinkit_zepto",
        "request": "Compare Blinkit and Zepto in terms of market position and unit economics.",
        "case_type": "in_scope",
        "expectations": {
            "min_citations": 2,
            "max_tool_calls": 10,
            "max_tokens": 20000,
            "must_include": ["Blinkit", "Zepto"],
            "must_not_include": [],
        },
    },
    {
        "name": "why_qcommerce_works_india",
        "request": "Why has quick commerce succeeded in India when it failed in the US?",
        "case_type": "in_scope",
        "expectations": {
            "min_citations": 2,
            "max_tool_calls": 10,
            "max_tokens": 20000,
            "must_include": ["density", "labor"],
            "must_not_include": [],
        },
    },
    
    # === Out-of-scope cases — sources don't cover these ===
    {
        "name": "mumbai_specific",
        "request": "Write me a strategic memo on q-commerce entry specifically in Mumbai. Cover market saturation, unit economics, and incumbent response in Mumbai specifically.",
        "case_type": "out_of_scope",
        "expectations": {
            "max_tool_calls": 10,
            "max_tokens": 20000,
            # The agent should refuse or hedge — these are signals it did
            "should_refuse_or_hedge": True,
            "refusal_keywords": ["don't have", "not covered", "no specific data", "limited information", "outside the scope", "do not have"],
            # Hallucination guardrail — these terms shouldn't appear if it's properly hedging
            "must_not_include_when_hedging": ["Mumbai's market saturation is", "Mumbai's unit economics are"],
        },
    },
    {
        "name": "europe_qcommerce",
        "request": "What's the state of quick commerce in Berlin and Paris?",
        "case_type": "out_of_scope",
        "expectations": {
            "max_tool_calls": 10,
            "max_tokens": 20000,
            "should_refuse_or_hedge": True,
            "refusal_keywords": ["don't have", "not covered", "no specific data", "limited", "outside"],
        },
    },
    
    # === Edge cases ===
    {
        "name": "trivial_question",
        "request": "What's quick commerce?",
        "case_type": "in_scope",
        "expectations": {
            "min_citations": 1,
            "max_tool_calls": 6,  # should be efficient for simple question
            "max_tokens": 15000,
            "must_include": ["quick commerce"],
            "must_not_include": [],
        },
    },
]