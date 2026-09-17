# LangChain + LangGraph: the small code map

## Mental model

```text
model + instructions + tools = agent
agents + shared state + edges = multi-agent workflow
```

## The main pieces used here

| Piece | Plain-English job | Where to find it |
|---|---|---|
| `ChatOllama(...)` | Connects LangChain to the local Ollama model | `src/agentforge_jarvis/providers.py` |
| `ChatOpenAI(...)` | Optional cloud-model adapter with the same interface | `src/agentforge_jarvis/providers.py` |
| `@tool` | Turns a Python function into a capability an agent may call | `src/agentforge_jarvis/engine.py` |
| `create_agent(...)` | Combines the model, tools, and system instructions | `src/agentforge_jarvis/engine.py` |
| `agent.invoke(...)` | Sends messages into the agent loop and returns messages/tool results | `src/agentforge_jarvis/engine.py` |
| `StateGraph(...)` | Defines the shared state passed through the workflow | `src/agentforge_jarvis/engine.py` |
| `add_node(...)` | Adds one agent step to the graph | `src/agentforge_jarvis/engine.py` |
| `add_edge(...)` | Defines which step runs next | `src/agentforge_jarvis/engine.py` |
| `compile().invoke(...)` | Builds the graph and runs it | `src/agentforge_jarvis/engine.py` |
| `HumanMessage`, `AIMessage`, `ToolMessage` | Distinguish human input, model output, and observed tool output | `src/agentforge_jarvis/providers.py` |

## Simplified agent pattern

```python
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_ollama import ChatOllama

@tool
def calculate_evidence() -> str:
    """Return checked evidence for the agent."""
    return "checked result"

model = ChatOllama(model="your-approved-model")
agent = create_agent(
    model=model,
    tools=[calculate_evidence],
    system_prompt="Use the tool before recommending an action.",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Analyze this scenario."}]}
)
```

## Simplified graph pattern

```python
from langgraph.graph import START, END, StateGraph

graph = StateGraph(SharedState)
graph.add_node("analytics", run_analytics)
graph.add_node("finance", run_finance)
graph.add_edge(START, "analytics")
graph.add_edge("analytics", "finance")
graph.add_edge("finance", END)
result = graph.compile().invoke({"reports": {}})
```

## What the framework does not do automatically

- It does not make model output true.
- It does not guarantee the model will call the correct tool; the app checks required calls.
- It does not protect secrets placed in prompts or files.
- It does not turn six roles into six separate computers.
- It does not replace the human decision owner.

## Code-reading route

Read only these seven locations first:

1. root `app.py` — launch;
2. `catalog.py` — roles and dependencies;
3. `agents/*.md` — student-editable role instructions;
4. `agent_prompts.py` — file loader;
5. `providers.py` — Ollama/OpenAI adapter;
6. `engine.py` — agents and orchestration;
7. `business.py` — deterministic tools.

The HTTP service, database, voice interface, and UI are already available. They are supporting services, not the first code students need to understand.
