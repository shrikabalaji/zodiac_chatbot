from __future__ import annotations

import json
import os
from dataclasses import dataclass
from threading import Lock
from typing import Any
from uuid import uuid4

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.rate_limiters import InMemoryRateLimiter

from .catalog import AGENTS

_limiter_lock = Lock()
_gemini_limiters: dict[float, InMemoryRateLimiter] = {}


def gemini_limiter():
    """All Gemini agents in this process share a paced request budget."""
    rpm = float(os.getenv("AGENTFORGE_GEMINI_RPM", "12"))
    with _limiter_lock:
        if rpm not in _gemini_limiters:
            _gemini_limiters[rpm] = InMemoryRateLimiter(
                requests_per_second=rpm / 60, check_every_n_seconds=0.1, max_bucket_size=1
            )
        return _gemini_limiters[rpm]


# The two live models switchable from the UI. Gemini/rehearsal remain valid
# for .env-based setups (and existing tests) but are not offered in the switcher.
SWITCHABLE_PROVIDERS = ("ollama", "openai")
DEFAULT_MODEL = {
    "ollama": "llama3.1",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-3.1-flash-lite",
}


@dataclass(frozen=True)
class Settings:
    provider: str = "rehearsal"
    model: str = ""

    @classmethod
    def from_env(cls):
        provider = os.getenv("AGENTFORGE_PROVIDER", "openai").lower()
        return cls(
            provider,
            os.getenv("AGENTFORGE_MODEL", DEFAULT_MODEL.get(provider, "")),
        )

    def error(self) -> str | None:
        if self.provider not in {"rehearsal", "gemini", "ollama", "openai"}:
            return "AGENTFORGE_PROVIDER must be rehearsal, ollama or openai."
        if self.provider != "rehearsal" and not self.model:
            return "Set AGENTFORGE_MODEL in your local .env and restart the server."
        if self.provider == "gemini" and not os.getenv("GEMINI_API_KEY"):
            return "Set GEMINI_API_KEY in your local .env and restart the server."
        if self.provider == "openai" and not os.getenv("OPENAI_API_KEY"):
            return "Set OPENAI_API_KEY in your local .env and restart the server."
        if self.provider == "gemini":
            try:
                if not 1 <= float(os.getenv("AGENTFORGE_GEMINI_RPM", "12")) <= 6000:
                    raise ValueError
            except ValueError:
                return "AGENTFORGE_GEMINI_RPM must be a number between 1 and 6000."
        return None

    def public(self):
        return {
            "provider": self.provider,
            "model": self.model or "Deterministic rehearsal",
            "configured": not self.error(),
            "error": self.error(),
            "live_verified": False,
            "framework": "LangChain create_agent + LangGraph",
            "switchable": list(SWITCHABLE_PROVIDERS),
            "default_models": DEFAULT_MODEL,
        }


class RehearsalModel(BaseChatModel):
    """Scripted tool-calling model exercising the same LangChain loop without an LLM.

    This is explicitly a rehearsal adapter, not a substitute for testing a live provider.
    It executes actual domain tools and echoes evidence; it cannot interpret arbitrary intent.
    """

    domain: str

    @property
    def _llm_type(self) -> str:
        return "agentforge-deterministic-rehearsal"

    def bind_tools(self, tools, *, tool_choice=None, **kwargs: Any):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        last_user = max(
            (i for i, m in enumerate(messages) if isinstance(m, HumanMessage)), default=0
        )
        recent = messages[last_user:]
        query = str(messages[last_user].content)
        results = {m.name: m for m in recent if isinstance(m, ToolMessage)}
        name, args = "", {}
        if self.domain == "supervisor":
            if not results:
                aliases = {
                    "finance": ["finance", "cash", "budget", "margin"],
                    "marketing": ["marketing", "sentiment", "campaign"],
                    "hr": ["hr", "hire", "hiring", "candidate", "staff"],
                    "operations": ["operations", "supply", "supplier", "delivery"],
                    "analytics": ["analytics", "survey", "kpi", "trend"],
                }
                if any(term in query.lower() for term in ["note", "memory", "remember", "vault"]):
                    name, args = "search_memory", {"query": query}
                else:
                    domain = next(
                        (
                            d
                            for d, words in aliases.items()
                            if any(w in query.lower() for w in words)
                        ),
                        None,
                    )
                    name, args = (
                        ("consult_agent", {"domain": domain, "task": query})
                        if domain
                        else ("read_latest_run", {})
                    )
            else:
                result = next(iter(results.values()))
                data = json.loads(result.content)
                if result.name == "search_memory":
                    content = (
                        "I found these team notes:\n"
                        + "\n\n".join(f"[{x['source']}] {x['excerpt']}" for x in data)
                        if data
                        else "I don't have matching evidence in this team's Memory Vault. Add a note or ask about the launch scenario."
                    )
                else:
                    content = data.get(
                        "answer", "Run the Company Launch Swarm to generate a decision package."
                    )
                return ChatResult(
                    generations=[
                        ChatGeneration(
                            message=AIMessage(
                                content="[Rehearsal · scripted tool routing]\n" + content
                            )
                        )
                    ]
                )
        else:
            domain_tool = AGENTS[self.domain]["tool"]
            if "read_brief" not in results:
                name = "read_brief"
            elif domain_tool not in results:
                name = domain_tool
            elif "search_memory" not in results:
                name, args = "search_memory", {"query": query}
            else:
                data = json.loads(results[domain_tool].content)
                notes = json.loads(results["search_memory"].content)
                content = f"[Rehearsal · computed evidence]\n{data['headline']}\n\n{data['recommendation']}"
                if notes:
                    content += "\n\nTeam evidence:\n" + "\n".join(
                        f"[{n['source']}] {n['excerpt']}" for n in notes
                    )
                content += "\n\n" + "\n".join(data["evidence"])
                return ChatResult(generations=[ChatGeneration(message=AIMessage(content=content))])
        message = AIMessage(
            content="",
            tool_calls=[{"name": name, "args": args, "id": uuid4().hex, "type": "tool_call"}],
        )
        return ChatResult(generations=[ChatGeneration(message=message)])


def make_model(settings: Settings, domain: str):
    if error := settings.error():
        raise ValueError(error)
    if settings.provider == "rehearsal":
        return RehearsalModel(domain=domain)
    if settings.provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.model,
            api_key=os.environ["GEMINI_API_KEY"],
            rate_limiter=gemini_limiter(),
            temperature=0.2,
            max_retries=2,
            timeout=45,
            max_output_tokens=4096,
            **({"thinking_budget": 0} if settings.model.startswith("gemini-2.5") else {}),
        )
    if settings.provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=settings.model,
            api_key=os.environ["OPENAI_API_KEY"],
            temperature=0.2,
            max_retries=2,
            timeout=45,
            max_tokens=4096,
        )
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=settings.model,
        base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        temperature=0.2,
        num_predict=1600,
        client_kwargs={"timeout": 60},
    )


def public_error(error: Exception) -> str:
    """Classify provider failures without exposing raw request or credential data."""
    text = str(error).lower()
    if any(x in text for x in ("429", "resource_exhausted", "quota", "rate limit", "insufficient_quota")):
        return "Provider quota or rate limit reached. Check the project's usage dashboard, then retry."
    if any(
        x in text
        for x in ("api_key_invalid", "api key not valid", "incorrect api key", "403", "permission_denied", "leaked", "401", "unauthorized")
    ):
        return "The provider rejected this credential or its permissions. Update the server's local key and restart."
    if any(x in text for x in ("connection refused", "connect call failed", "could not connect", "econnrefused")):
        return "Could not reach the local Ollama server. Start it with 'ollama serve' and pull the configured model."
    if any(x in text for x in ("timeout", "timed out", "deadline")):
        return "The model request timed out. Check connectivity and retry."
    if any(x in text for x in ("404", "not_found", "not found")):
        return "The configured model is unavailable for this account. Check its model ID."
    if "required evidence" in text or "final answer" in text:
        return "The model did not complete the required tool-and-answer contract. Retry the agent."
    return "Agent execution failed. Check provider availability and configuration, then retry. No automatic fallback was used."
