# Lovable Challenge — Build “Agent Handoff Rescue”

## The challenge

Build a small browser game that teaches players how a multi-agent system routes evidence. The game should be playable in under three minutes and understandable without the creator explaining it.

## Required game loop

1. Show a fictional business scenario card.
2. Show one evidence card at a time.
3. Ask the player to route it to Analytics, Marketing, HR, Operations, Finance, or General Management.
4. Give immediate feedback explaining why the route is useful or risky.
5. Include at least one “Send back for missing evidence” option.
6. End with a score and one improvement tip.

## Copyable Lovable prompt

```text
Create a responsive single-page learning game called “Agent Handoff Rescue” for MBA students learning multi-agent AI systems.

Design: clean editorial classroom style, cream background, burgundy accents, black text, large readable type, no login, no database, and no external API. Keep it fast and accessible on laptops and phones.

Game flow:
1. Start screen with a short explanation and a Start Mission button.
2. Show a fictional business scenario.
3. Present 8 evidence cards one at a time.
4. For each card, the player chooses one destination: Analytics, Marketing, HR, Operations, Finance, General Management, or Send Back for Missing Evidence.
5. Immediately show concise feedback explaining the best routing choice. Allow Next Card after feedback.
6. Track score out of 8 and a three-life “evidence integrity” meter.
7. Final screen shows score, missed hand-offs, one personalized improvement tip, and Play Again.

Use these learning rules:
- Analytics receives raw demand signals and measurement questions.
- Marketing receives analyzed customer signals and campaign constraints.
- HR receives skills, staffing, and work-sample evidence.
- Operations receives supply, capacity, lead-time, and delivery evidence.
- Finance receives cost, cash, margin, and upstream plan evidence.
- General Management receives reconciled specialist reports, conflicts, and decision gates—not raw unsupported claims.
- Missing, ambiguous, personal, or unsupported information should be sent back for review.

Include a small “Why?” panel after every answer. Use only fictional data. Do not request names, email addresses, API keys, or personal data. Add keyboard focus states and sufficient color contrast.
```

## Team customization

After the first version works, each team must change at least two elements:

- replace two evidence cards with examples from its specialization;
- add one deliberately ambiguous card;
- improve one feedback explanation; or
- add a streak, timer, or house-points mechanic without removing accessibility.

## Peer test

Swap with another team. The tester records:

- one rule that was clear;
- one card that was ambiguous;
- one improvement to the feedback;
- whether the game worked without creator assistance.

If Lovable is unavailable, sketch the same screens on paper and run the cards manually. The learning outcome is the routing logic, not the platform.
