"""One real LangChain tool-calling agent for the cumulative Day 1 checkpoints."""

from __future__ import annotations

import json
import os
from uuid import uuid4

from langchain.agents import create_agent
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import StructuredTool

from .catalog import AGENTS
from .checkpoint_tools import CHECKPOINT_TOOLS

BASE_CONTRACT = """You are an AgentForge teaching agent.
Call the supplied deterministic tool before answering.
Separate the tool evidence from your explanation, state one limitation, and retain human review.
Never invent values or claim that you made the final business decision."""


class CheckpointRehearsalModel(BaseChatModel):
    """Scripted offline model that still exercises LangChain's tool loop."""

    tool_name: str
    tool_args: dict

    @property
    def _llm_type(self):
        return "agentforge-checkpoint-rehearsal"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        if isinstance(messages[-1], ToolMessage):
            answer = AIMessage(
                content="REHEARSAL TOOL RESULT\n"
                + str(messages[-1].content)
                + "\nA human must review the result."
            )
        else:
            answer = AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": self.tool_name,
                        "args": self.tool_args,
                        "id": uuid4().hex,
                        "type": "tool_call",
                    }
                ],
            )
        return ChatResult(generations=[ChatGeneration(message=answer)])


def role_contract(domain: str) -> str:
    try:
        spec = AGENTS[domain]
    except KeyError as exc:
        raise ValueError(f"Unsupported domain: {domain}") from exc
    constraints = "; ".join(spec["constraints"])
    return (
        f"{BASE_CONTRACT}\nRole: {spec['role']}\nGoal: {spec['goal']}\n"
        f"Constraints: {constraints}"
    )


def checkpoint_tool(domain: str) -> StructuredTool:
    try:
        function = CHECKPOINT_TOOLS[domain]
        spec = AGENTS[domain]
    except KeyError as exc:
        raise ValueError(f"Unsupported domain: {domain}") from exc
    return StructuredTool.from_function(
        function,
        name=spec["tool"],
        description=f"Deterministic {spec['label']} checkpoint calculation.",
    )


def live_model(domain: str):
    key = os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=os.getenv("AGENTFORGE_MODEL", "gemini-3.1-flash-lite"),
        google_api_key=key,
        temperature=0,
    )


def run_checkpoint_agent(domain: str, payload: dict, *, live: bool = False) -> dict:
    tool = checkpoint_tool(domain)
    model = (
        live_model(domain)
        if live
        else CheckpointRehearsalModel(tool_name=tool.name, tool_args=payload)
    )
    agent = create_agent(model=model, tools=[tool], system_prompt=role_contract(domain))
    result = agent.invoke(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Use the required tool for this fictional input: " + json.dumps(payload),
                }
            ]
        },
        {"recursion_limit": 12},
    )
    evidence = [message for message in result["messages"] if isinstance(message, ToolMessage)]
    if len(evidence) != 1 or evidence[0].status == "error":
        raise RuntimeError("The required checkpoint tool did not complete successfully")
    return {
        "mode": "live" if live else "rehearsal",
        "domain": domain,
        "tool_name": tool.name,
        "tool_result": json.loads(evidence[0].content),
        "explanation": str(result["messages"][-1].content),
        "human_review_required": True,
    }
