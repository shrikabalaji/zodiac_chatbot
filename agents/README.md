# AgentForge: Six AI Agent Personas

* **Name:** Shrika Balajii
* **Roll Number:** F26152
* **House:** Hufflepuff
* **Files:** Libra.md, Taurus.md, Aries.md, Pisces.md, Scorpio.md, Cancer.md, Shrika-F26152-Hufflepuff.md (this README)

## Agent Names (Assignment Role Name -> Persona Name)
* JARVIS (General Management) -> **LIBRA** (Libra.md)
* LEDGER (Finance) -> **TAURUS** (Taurus.md)
* ATLAS (Operations) -> **ARIES** (Aries.md)
* PULSE (Marketing) -> **PISCES** (Pisces.md)
* PRISM (Analytics) -> **SCORPIO** (Scorpio.md)
* NOVA (Human Resources) -> **CANCER** (Cancer.md)

## Design Choices
1. **Consistent structure:** All six personas use the same numbered 11-section layout required by the assignment, so another student can find any section quickly.
2. **An iterative Team Relay Loop, not one-shot answers:** R0 Frame (LIBRA + human) -> R1 Specialist v1 drafts -> R2 Cross-examination through Challenge Cards -> R3 Revised v2 drafts with SCORPIO re-auditing only what changed -> R4 Decision Brief -> Human Approval Gate -> R5 Debrief (only if the human supplies real outcomes). Every report carries a version number and an Iteration Log showing what changed and whether the verdict moved.
3. **Built-in stopping rules:** A maximum of 3 loops per question. If a full loop changes no verdict and no number, the loop stops; if it has not converged after loop 3, the disagreement goes to a human instead of being averaged away.
4. **Self-Challenge Pass:** Before sending anything, every agent asks what would make its answer wrong, what it assumed without a source, and which other agent would object, then revises.
5. **Shared team language:** The same five evidence tags (`[FACT]`, `[ASSUMPTION]`, `[MISSING]`, `[CONFLICT]`, `[HUMAN DECISION]`), a common Confidence rubric (HIGH / MEDIUM / LOW defined by evidence status), Challenge Cards between agents, and the same Handoff Card.
6. **A different higher-order lens per agent:** LIBRA rates decisions as one-way or two-way doors and sets tripwires; TAURUS runs reverse stress tests to find the exact failure point; ARIES accounts for slack and wargames the plan; PISCES writes kill and scale criteria before any test; SCORPIO red-teams its own verdicts with rival explanations and evidence half-lives; CANCER tests load week by week and single points of failure.
7. **No invented thresholds or facts:** Budget caps, target margins and working-hours limits must come from a human; otherwise the agent says CANNOT JUDGE and asks.
8. **Human approval everywhere:** LIBRA coordinates but never approves spending, hiring, publishing or launch, and every brief ends with a blank sign-off.
9. **Safe, checkable examples:** One fictional case ("Project Lantern") with invented figures whose arithmetic can be verified by hand; no real data, secrets or personal records.

## One Important Difference Between the Six Personas
The agents differ most in what they are allowed to conclude, and in how they challenge themselves. TAURUS, ARIES and CANCER give feasibility verdicts within their own area using supplied numbers; PISCES may only state customer claims that have earned a place on the Claim Ladder; SCORPIO judges the soundness of evidence, never whether a plan is a good idea; and only LIBRA sees the whole picture, presenting disagreements as choices for a human instead of resolving them itself.