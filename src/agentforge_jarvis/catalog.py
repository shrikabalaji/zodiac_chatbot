from __future__ import annotations

AGENTS = {
    "analytics": {
        "name": "PRISM",
        "label": "Analytics",
        "symbol": "◈",
        "color": "#69baff",
        "role": "Decision Intelligence Analyst",
        "goal": "Quantify demand signals, define KPIs, expose uncertainty and build decision evidence.",
        "inputs": ["channel survey", "previous positive rates", "launch targets"],
        "tool": "analyze_signals",
        "dependencies": [],
        "constraints": ["Show denominators", "Do not claim causality", "State sample limitations"],
    },
    "marketing": {
        "name": "PULSE",
        "label": "Marketing",
        "symbol": "◎",
        "color": "#c097ff",
        "role": "Market Insight Lead",
        "goal": "Analyze trend and sentiment; propose positioning and a measurable channel experiment.",
        "inputs": ["channel signals", "sentiment", "campaign budget"],
        "tool": "plan_marketing",
        "dependencies": ["analytics"],
        "constraints": [
            "No invented market claims",
            "Label draft copy",
            "Respect the campaign budget",
        ],
    },
    "hr": {
        "name": "NOVA",
        "label": "Human Resources",
        "symbol": "⟡",
        "color": "#f6bf77",
        "role": "People Readiness Partner",
        "goal": "Build a staffing plan and an auditable, skills-only candidate screening worksheet.",
        "inputs": ["capacity", "required skills", "anonymous work samples"],
        "tool": "screen_skills",
        "dependencies": ["analytics"],
        "constraints": [
            "Exclude protected attributes",
            "Human review of every candidate",
            "Never make final hiring decisions",
        ],
    },
    "operations": {
        "name": "ATLAS",
        "label": "Operations",
        "symbol": "⌘",
        "color": "#66d6bb",
        "role": "Supply and Delivery Planner",
        "goal": "Calculate supply-chain capacity, detect launch bottlenecks and propose a fallback.",
        "inputs": ["supplier lead time", "production rate", "launch window"],
        "tool": "assess_supply",
        "dependencies": ["analytics"],
        "constraints": [
            "Expose capacity shortfalls",
            "Name fallback owners",
            "No procurement commitments",
        ],
    },
    "finance": {
        "name": "LEDGER",
        "label": "Finance",
        "symbol": "▥",
        "color": "#ffe082",
        "role": "Commercial Scenario Analyst",
        "goal": "Calculate launch cash needs, contribution margin, break-even and downside/base/upside scenarios.",
        "inputs": ["unit economics", "campaign plan", "people plan", "delivery capacity"],
        "tool": "model_finances",
        "dependencies": ["marketing", "hr", "operations"],
        "constraints": [
            "Arithmetic comes from tools",
            "Show assumptions",
            "Business simulation only",
        ],
    },
    "general-management": {
        "name": "JARVIS",
        "label": "General Management",
        "symbol": "✧",
        "color": "#82ede1",
        "role": "Strategy Integrator",
        "goal": "Reconcile all five specialist reports into a conditional executive decision with owners and review gates.",
        "inputs": ["all specialist reports", "conflicts", "decision rights"],
        "tool": "synthesize_strategy",
        "dependencies": ["analytics", "marketing", "hr", "operations", "finance"],
        "constraints": [
            "Do not hide conflicts",
            "Do not override failed gates",
            "Require human launch approval",
        ],
    },
}

ORDER = list(AGENTS)
CHALLENGES = [
    {
        "id": "baseline",
        "name": "Baseline launch",
        "description": "The original 12-week Company Launch Swarm.",
    },
    {
        "id": "budget-cut",
        "name": "Budget −25%",
        "description": "Reconcile a 25% cut to the launch cash budget.",
    },
    {
        "id": "supply-delay",
        "name": "Supplier +14 days",
        "description": "The primary supplier reports a two-week delay.",
    },
    {
        "id": "sentiment-shift",
        "name": "Customer trust alert",
        "description": "Allergen labelling concern; positive survey counts fall 30%.",
    },
    {
        "id": "demand-surge",
        "name": "Demand +40%",
        "description": "Fulfil 40% more units within the same launch window.",
    },
]

RUBRIC = [
    {
        "name": "Business relevance",
        "weight": 25,
        "check": "Actionable decision that addresses the changed scenario.",
    },
    {
        "name": "Agent orchestration",
        "weight": 25,
        "check": "Working roles, shared state, hand-offs and dependencies.",
    },
    {
        "name": "Reliability and evidence",
        "weight": 20,
        "check": "Traceable tools, tested arithmetic and stated assumptions.",
    },
    {
        "name": "Responsible AI",
        "weight": 15,
        "check": "Bias, privacy, prompt injection and unsupported claims reviewed.",
    },
    {
        "name": "Communication and reflection",
        "weight": 15,
        "check": "Clear demo, individual reflection and next steps.",
    },
]
