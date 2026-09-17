# Day 2 Quizzes — Student Sheet

Name: ____________________  Team: ____________________

## Opening quiz (8:35–8:45)

Choose one answer unless the question asks for a sentence.

1. Which combination best defines an agent?
   - A. A chatbot name and avatar
   - B. A model, instructions, tools, and a goal
   - C. A database and a website
   - D. Six prompts in one file

2. What is the safest place for an OpenAI API key?
   - A. Inside an agent Markdown file
   - B. In a screenshot sent to the group
   - C. In the local `.env` file that is not committed
   - D. In `README.md`

3. What should an agent do when required evidence is missing?
   - A. Invent a reasonable value
   - B. State the gap and request or preserve human review
   - C. Hide the uncertainty
   - D. Copy another agent’s answer

4. A tool is best described as:
   - A. A callable capability that produces an observable result
   - B. A second system prompt
   - C. A model provider
   - D. A visual theme

5. Why do we test normal, ambiguous, and unsafe inputs?
   - A. To make the interface colorful
   - B. To test useful behavior, uncertainty, and boundaries
   - C. To increase token usage
   - D. To avoid writing instructions

6. Which command shows installed Ollama model tags?
   - A. `ollama list`
   - B. `ollama models`
   - C. `python models.py`
   - D. `git model`

7. In one sentence: what did your Day 1 agent do?

8. In one sentence: what decision must remain with a human?

## Closing quiz (4:05–4:15)

1. What is the orchestrator’s main job?
   - A. Make every answer longer
   - B. Control order, hand-offs, shared state, and stopping
   - C. Replace every specialist
   - D. Store API keys

2. In this app, where are the six student-editable role instructions?
   - A. `requirements.txt`
   - B. `.env`
   - C. `agents/*.md`
   - D. `static/style.css`

3. Which function combines a model, tools, and system instructions?
   - A. `create_agent(...)`
   - B. `add_edge(...)`
   - C. `ollama list`
   - D. `pip install(...)`

4. What does `@tool` do?
   - A. Turns a Python function into a capability an agent can call
   - B. Hides the function from the agent
   - C. Creates a user interface
   - D. Downloads a model

5. What does `add_edge("analytics", "finance")` express?
   - A. Finance runs before Analytics
   - B. The workflow can pass from Analytics to Finance
   - C. Both agents use different programming languages
   - D. Finance can edit the Analytics source code

6. Why did we run the same scenario before and after replacing prompts?
   - A. To keep other variables stable and isolate the prompt change
   - B. Because scenarios cannot be edited
   - C. To guarantee identical wording
   - D. To avoid observing tools

7. Which result should usually stay unchanged after only a prompt-file replacement?
   - A. The output tone
   - B. The report heading
   - C. Deterministic tool arithmetic from the same inputs
   - D. The order of words

8. In this classroom app, the six agents run as:
   - A. Six independent laptops
   - B. Six human interns
   - C. Roles orchestrated in one local Python process
   - D. Six databases

9. Name one failure mode in a multi-agent hand-off.

10. Write one sentence explaining why human review is still required.
