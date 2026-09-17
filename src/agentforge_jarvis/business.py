"""Auditable domain tools. All arithmetic is Python, never delegated to a language model."""

from __future__ import annotations

import math

from .models import AgentReport, Scenario


def action(owner: str, task: str, gate: str) -> dict[str, str]:
    return {"owner": owner, "task": task, "gate": gate}


def report(
    domain: str,
    headline: str,
    recommendation: str,
    metrics: dict,
    evidence: list[str],
    risks: list[str],
    actions: list[dict],
    assumptions: list[str] | None = None,
    details: list[dict] | None = None,
    status: str = "review",
) -> AgentReport:
    return AgentReport(
        domain=domain,
        headline=headline,
        recommendation=recommendation,
        metrics=metrics,
        evidence=evidence,
        risks=risks,
        actions=actions,
        assumptions=["All source inputs are fictional workshop data."] + (assumptions or []),
        details=details or [],
        status=status,
    )


def analyze(domain: str, s: Scenario, upstream: dict[str, AgentReport]) -> AgentReport:
    if domain == "analytics":
        n = sum(x.responses for x in s.signals)
        positive = sum(x.positive for x in s.signals)
        rate = positive / n
        previous = sum(x.previous_positive_rate * x.responses for x in s.signals) / n
        # Wilson interval is a descriptive teaching interval, not a representative-market claim.
        z = 1.96
        center = (rate + z * z / (2 * n)) / (1 + z * z / n)
        half = z * math.sqrt(rate * (1 - rate) / n + z * z / (4 * n * n)) / (1 + z * z / n)
        rows = [
            {
                "channel": x.channel,
                "responses": x.responses,
                "positive_pct": round(x.positive / x.responses * 100, 2),
                "change_pp": round((x.positive / x.responses - x.previous_positive_rate) * 100, 2),
            }
            for x in s.signals
        ]
        return report(
            domain,
            f"{rate:.1%} positive intent across {n} responses",
            "Use channel-level signals to design a small controlled launch. Track conversion, repeat purchase, complaints and contribution margin weekly.",
            {
                "responses": n,
                "positive_pct": round(rate * 100, 2),
                "trend_pp": round((rate - previous) * 100, 2),
                "interval_low_pct": round((center - half) * 100, 2),
                "interval_high_pct": round((center + half) * 100, 2),
            },
            [
                f"scenario.signals: {positive}/{n} positive responses; weighted previous rate {previous:.4f}.",
                "95% Wilson binomial interval, z=1.96; descriptive only.",
            ],
            ["Convenience samples can overstate demand; responses are not sales."]
            + (
                ["Positive intent declined against the supplied prior baseline."]
                if rate < previous
                else []
            ),
            [
                action(
                    "Analytics",
                    "Measure purchases / eligible trial participants by channel",
                    "Weekly review with channel denominators",
                )
            ],
            [
                "Responses are treated as independent for the interval; representativeness is unverified."
            ],
            rows,
        )

    if domain == "marketing":
        analytics = upstream.get("analytics")
        rows = sorted(s.signals, key=lambda x: x.positive / x.responses, reverse=True)
        total_positive = sum(x.positive for x in rows)
        allocation = []
        remaining = s.marketing_budget
        for i, x in enumerate(rows):
            amount = (
                round(
                    s.marketing_budget
                    * (x.positive / total_positive if total_positive else 1 / len(rows)),
                    2,
                )
                if i < len(rows) - 1
                else round(remaining, 2)
            )
            remaining -= amount
            allocation.append(
                {
                    "channel": x.channel,
                    "budget_inr": amount,
                    "positive_pct": round(x.positive / x.responses * 100, 2),
                    "draft_message": "A millet snack for your workday. Explore ingredients before you try.",
                }
            )
        hold = s.labelling_concern
        return report(
            domain,
            "Resolve customer trust before promotion"
            if hold
            else f"Start with {rows[0].channel.lower()}",
            "Pause promotional claims until ingredient and allergen information is reviewed; test revised copy with customers."
            if hold
            else "Run a measured sampling pilot with the strongest observed channel; review conversion before expanding spend.",
            {
                "campaign_budget_inr": s.marketing_budget,
                "allocated_inr": round(sum(x["budget_inr"] for x in allocation), 2),
                "channels": len(rows),
                "trust_gate": "hold" if hold else "review",
            },
            [
                "scenario.signals and scenario.marketing_budget; allocation proportional to positive counts."
            ]
            + ([f"analytics hand-off: {analytics.headline}"] if analytics else []),
            ["Survey intent is not causal evidence of channel performance."]
            + (["Allergen labelling concern requires a human product review."] if hold else []),
            [
                action(
                    "Marketing",
                    "Approve labelled draft copy and run a controlled pilot",
                    "Customer trust and claim review before publication",
                )
            ],
            ["Budget allocation is a teaching heuristic; no ROI is established."],
            allocation,
            "hold" if hold else "review",
        )

    if domain == "hr":
        gap = max(0, s.required_fte - s.team_fte)
        required = {x.strip().lower() for x in s.required_skills if x.strip()}
        rows = []
        for candidate in s.candidates:
            skills = {x.strip().lower() for x in candidate.skills}
            coverage = len(skills & required) / len(required) if required else 0
            score = round(coverage * 60 + candidate.work_sample_score * 0.4, 2)
            rows.append(
                {
                    "candidate_id": candidate.candidate_id,
                    "skill_coverage_pct": round(coverage * 100, 2),
                    "work_sample_score": candidate.work_sample_score,
                    "review_score": score,
                    "missing_skills": ", ".join(sorted(required - skills)) or "None",
                    "decision": "Human review required",
                }
            )
        rows.sort(key=lambda x: (-x["review_score"], x["candidate_id"]))
        return report(
            domain,
            f"Close a {gap:g} FTE capacity gap",
            "Review the anonymous skills worksheet, calibrate work samples and assign training or temporary staffing. The worksheet does not make hiring decisions.",
            {
                "available_fte": s.team_fte,
                "required_fte": s.required_fte,
                "gap_fte": gap,
                "staffing_cost_inr": gap * s.hire_cost,
                "candidates": len(rows),
            },
            [
                f"scenario.team_fte={s.team_fte}; required_fte={s.required_fte}.",
                "Review score = 60% required-skill coverage + 40% work-sample score; only allowlisted candidate fields are accepted.",
            ],
            [
                "Skills and sample scores may still contain bias; protected-attribute exclusion does not establish fairness.",
                "No demographic parity claim can be made from this anonymous dataset.",
            ]
            + (
                ["No required skills supplied; define a job-relevant rubric before review."]
                if not required
                else []
            ),
            [
                action(
                    "HR",
                    "Calibrate the rubric with a human reviewer and check accessibility",
                    "No candidate rejection or offer from this score",
                ),
                action(
                    "HR",
                    f"Plan capacity for {gap:g} additional FTE",
                    "Finance approval of staffing allowance",
                ),
            ],
            [
                "Staffing cost is a one-time workshop planning allowance per additional FTE, not a salary estimate."
            ],
            rows,
        )

    if domain == "operations":
        production_days = math.ceil(s.units / s.production_per_day)
        completion = s.lead_days + production_days
        capacity = max(0, s.launch_days - s.lead_days) * s.production_per_day
        shortfall = max(0, s.units - capacity)
        return report(
            domain,
            "Delivery window at risk" if shortfall else "Production fits the launch window",
            f"Stage an initial release of at most {min(s.units, capacity):,} units. "
            + (
                "Qualify a backup supplier or extend the launch window before promising the balance."
                if shortfall
                else "Reserve production capacity and validate supplier readiness before commitments."
            ),
            {
                "production_days": production_days,
                "completion_day": completion,
                "buffer_days": s.launch_days - completion,
                "deliverable_units": min(s.units, capacity),
                "capacity_units": capacity,
                "shortfall_units": shortfall,
            },
            [
                f"Completion = {s.lead_days} lead days + ceil({s.units}/{s.production_per_day}) = {completion} days.",
                f"Capacity = max(0, {s.launch_days}-{s.lead_days}) × {s.production_per_day} = {capacity} units.",
            ],
            [
                "Daily capacity is assumed constant; downtime, transit and quality failures are not modelled."
            ]
            + ([f"{shortfall:,} units miss the launch window."] if shortfall else []),
            [
                action(
                    "Operations",
                    "Confirm supplier milestone and alternate capacity",
                    "Supplier confirmation before production release",
                )
            ],
            [
                "The lead-time and production phases are sequential; lead time includes delivery to production."
            ],
            [
                {"phase": "Supply lead time", "days": s.lead_days},
                {"phase": "Production", "days": production_days},
            ],
            "hold" if shortfall else "review",
        )

    if domain == "finance":
        marketing = upstream.get("marketing")
        hr = upstream.get("hr")
        operations = upstream.get("operations")
        campaign = marketing.metrics["allocated_inr"] if marketing else s.marketing_budget
        staffing = (
            hr.metrics["staffing_cost_inr"]
            if hr
            else max(0, s.required_fte - s.team_fte) * s.hire_cost
        )
        deliverable = (
            int(operations.metrics["deliverable_units"])
            if operations
            else min(s.units, max(0, s.launch_days - s.lead_days) * s.production_per_day)
        )
        fixed = s.fixed_cost + campaign + staffing
        cash = s.units * s.unit_cost + fixed
        margin = (s.price - s.unit_cost) / s.price * 100
        contribution = s.price - s.unit_cost
        break_even = math.ceil(fixed / contribution) if contribution > 0 else "Not achievable"
        rows = []
        for name, factor in [("Downside", 0.6), ("Base", 1), ("Upside", 1.4)]:
            sold = min(round(s.units * factor), deliverable)
            rows.append(
                {
                    "case": name,
                    "demand_units": round(s.units * factor),
                    "sold_units": sold,
                    "revenue_inr": sold * s.price,
                    "contribution_less_fixed_inr": round(sold * contribution - fixed, 2),
                    "cash_after_launch_inr": round(s.budget - cash + sold * s.price, 2),
                }
            )
        gap = max(0, cash - s.budget)
        hold = gap > 0 or margin < s.margin_target
        return report(
            domain,
            f"INR {gap:,.0f} funding gap" if gap else f"INR {s.budget - cash:,.0f} cash headroom",
            "Phase production or reallocate approved spend before launch; the full plan exceeds the current financial gates."
            if hold
            else "The planned production fits the cash budget. Authorize spend only after staffing, supply and customer-trust reviews.",
            {
                "budget_inr": s.budget,
                "cash_required_inr": cash,
                "funding_gap_inr": gap,
                "headroom_inr": s.budget - cash,
                "gross_margin_pct": round(margin, 2),
                "margin_target_pct": s.margin_target,
                "break_even_units": break_even,
                "fixed_and_launch_cost_inr": fixed,
            },
            [
                f"Cash required = {s.units:,} × INR {s.unit_cost:,.0f} + INR {s.fixed_cost:,.0f} fixed + INR {campaign:,.0f} marketing + INR {staffing:,.0f} staffing = INR {cash:,.0f}.",
                f"Gross margin = ({s.price:g}-{s.unit_cost:g})/{s.price:g} × 100.",
                f"Revenue is constrained to {deliverable} deliverable units by Operations.",
            ],
            ["Taxes, financing, returns and payment collection delays are excluded."]
            + (["Budget is insufficient for full upfront production."] if gap else [])
            + (["Gross margin is below the target."] if margin < s.margin_target else []),
            [
                action(
                    "Finance",
                    "Approve a cash plan and test downside sell-through",
                    "No spend approval until the funding and margin gates pass",
                )
            ],
            [
                "All units are financed upfront, unsold inventory retains its cost, and sold units collect cash immediately.",
                "Scenario contribution less fixed costs is not accounting net profit.",
            ],
            rows,
            "hold" if hold else "review",
        )

    if domain == "general-management":
        missing = [
            d
            for d in ["analytics", "marketing", "hr", "operations", "finance"]
            if d not in upstream
        ]
        holds = [d for d, r in upstream.items() if r.status == "hold"]
        decision = "HOLD" if holds or missing else "CONDITIONAL GO"
        conflicts = []
        if "finance" in holds:
            conflicts.append("Full launch scope conflicts with the Finance cash or margin gate.")
        if "operations" in holds:
            conflicts.append("Demand commitments conflict with the Operations delivery window.")
        if "marketing" in holds:
            conflicts.append("Promotion conflicts with the unresolved customer-trust review.")
        if missing:
            conflicts.append("Missing specialist reports: " + ", ".join(missing))
        rows = [{"agent": d, "gate": r.status, "finding": r.headline} for d, r in upstream.items()]
        return report(
            domain,
            f"{decision} · executive launch recommendation",
            "Resolve blocked gates, rerun the swarm and obtain human sign-off before launch."
            if decision == "HOLD"
            else "Proceed to a limited, human-approved pilot with weekly KPI review and explicit stop conditions.",
            {
                "decision": decision,
                "reports_received": len(upstream),
                "blocked_gates": len(holds) + len(missing),
            },
            [f"{d} hand-off: {r.headline}" for d, r in upstream.items()],
            conflicts
            or ["All agent outputs remain decision support; an accountable human owns the launch."],
            [
                action(
                    "General Management",
                    "Review every specialist gate and sign the executive package",
                    "Human approval required",
                ),
                action(
                    "Analytics",
                    "Review launch KPIs with the team after the pilot",
                    "Pause if trust, cash or delivery assumptions fail",
                ),
            ],
            ["No specialist hold can be overridden by the synthesis agent."],
            rows,
            "hold" if decision == "HOLD" else "review",
        )
    raise ValueError(f"Unknown domain: {domain}")
