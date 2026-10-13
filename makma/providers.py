"""Provider boundary: bounded requests, structured validation and one repair."""
import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Protocol, TypeVar
from urllib.parse import urlparse
import httpx
from pydantic import BaseModel, ValidationError
from .config import Settings

T = TypeVar("T", bound=BaseModel)


class ProviderUnavailable(RuntimeError):
    pass


class InvalidModelOutput(RuntimeError):
    pass


@dataclass
class ModelSpec:
    name: str
    provider: str
    capabilities: list[str] = field(default_factory=lambda: ["reasoning", "coding", "structured"])
    context_length: int = 4096
    memory_mb: int | None = None
    tokens_per_second: float | None = None
    cost_per_million: float | None = None
    tool_support: bool = False
    vision_support: bool = False
    coding_score: float | None = None
    reasoning_score: float | None = None


@dataclass
class Completion:
    text: str
    tokens: int
    seconds: float
    model: str


class ModelProvider(Protocol):
    async def health(self) -> dict: ...
    async def complete(self, messages: list[dict], schema: dict, max_tokens: int) -> Completion: ...


def check_endpoint(url: str, allow_remote: bool):
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or parsed.username or parsed.password:
        raise ValueError("Provider endpoint must be an HTTP URL without embedded credentials")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"} and not allow_remote:
        raise ValueError("Remote models require MAKMA_REMOTE_MODELS=true; agent context leaves this machine")


def grammar_schema(value):
    """Keep structure, omit bounds unsupported by some llama.cpp grammar builds.

    All original constraints are still enforced by Pydantic after generation.
    Large maxLength values can exceed the grammar engine repetition limit.
    """
    if isinstance(value,dict):
        return {k:grammar_schema(v) for k,v in value.items() if k not in {"minLength","maxLength","minimum","maximum","minItems","maxItems","default"} and not (k=="title" and isinstance(v,str))}
    if isinstance(value,list):
        return [grammar_schema(v) for v in value]
    return value


class OllamaProvider:
    def __init__(self, settings: Settings, transport=None):
        self.settings = settings
        check_endpoint(settings.ollama_url, settings.remote_models)
        self.client = httpx.AsyncClient(base_url=settings.ollama_url, timeout=httpx.Timeout(240,connect=5), transport=transport, trust_env=False)

    async def health(self):
        try:
            response = await self.client.get("/api/tags", timeout=5)
            response.raise_for_status()
            models = [m["name"] for m in response.json().get("models", [])]
            return {"available": self.settings.model in models, "provider":"ollama", "model":self.settings.model, "installed_models":models, "detail": "Ready" if self.settings.model in models else "Configured model is not installed"}
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            return {"available":False, "provider":"ollama", "model":self.settings.model, "detail":f"Ollama unavailable: {type(exc).__name__}"}

    async def complete(self, messages, schema, max_tokens):
        start = time.perf_counter()
        try:
            response = await self.client.post("/api/chat", json={"model":self.settings.model,"messages":messages,"stream":False,"think":False,"format":grammar_schema(schema),"keep_alive":"5m","options":{"temperature":.3,"num_ctx":self.settings.context_length,"num_predict":max_tokens}})
            response.raise_for_status()
            value = response.json()
            return Completion(value["message"]["content"], int(value.get("prompt_eval_count",0))+int(value.get("eval_count",0)), time.perf_counter()-start,self.settings.model)
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            detail = exc.response.text[:500] if isinstance(exc,httpx.HTTPStatusError) else type(exc).__name__
            raise ProviderUnavailable(f"Ollama request failed: {detail}") from exc

    async def close(self):
        await self.client.aclose()


class OpenAICompatibleProvider:
    def __init__(self, settings: Settings, transport=None):
        check_endpoint(settings.openai_url, settings.remote_models)
        self.settings = settings
        self.client = httpx.AsyncClient(base_url=settings.openai_url.rstrip("/")+"/",headers={"Authorization":f"Bearer {settings.api_key}"} if settings.api_key else {}, timeout=240, transport=transport, trust_env=False)

    async def health(self):
        try:
            r = await self.client.get("models",timeout=5)
            r.raise_for_status()
            installed = [m["id"] for m in r.json()["data"]]
            return {"available":self.settings.model in installed,"provider":"openai-compatible","model":self.settings.model,"installed_models":installed}
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            return {"available":False,"detail":type(exc).__name__,"provider":"openai-compatible","model":self.settings.model}

    async def complete(self,messages,schema,max_tokens):
        start=time.perf_counter()
        try:
            r=await self.client.post("chat/completions",json={"model":self.settings.model,"messages":messages,"max_tokens":max_tokens,"temperature":.3,"response_format":{"type":"json_schema","json_schema":{"name":"makma_action","strict":True,"schema":schema}}})
            r.raise_for_status()
            v=r.json()
            return Completion(v["choices"][0]["message"]["content"],v.get("usage",{}).get("total_tokens",0),time.perf_counter()-start,self.settings.model)
        except (httpx.HTTPError, ValueError, KeyError) as exc:
            raise ProviderUnavailable(f"Compatible model request failed: {type(exc).__name__}") from exc

    async def close(self):
        await self.client.aclose()


class FutureVLLMProvider(OpenAICompatibleProvider):
    """vLLM's OpenAI-compatible serving adapter; no distributed scheduler yet."""


class MockProvider:
    """Explicit test double. Never selected implicitly when a real model fails."""
    def __init__(self, responses=()):
        self.responses=list(responses)
        self.calls=[]

    async def health(self):
        return {"available":True,"provider":"mock","model":"TEST DOUBLE"}

    async def complete(self,messages,schema,max_tokens):
        self.calls.append(messages)
        if not self.responses:
            raise ProviderUnavailable("Mock has no configured response")
        value=self.responses.pop(0)
        if isinstance(value,Exception):
            raise value
        return Completion(value if isinstance(value,str) else json.dumps(value),10,0,"mock")


class ModelRouter:
    def __init__(self, provider: ModelProvider, model: str, concurrency=1):
        self.provider=provider
        self.registry=[ModelSpec(name=model,provider=type(provider).__name__)]
        self.gate=asyncio.Semaphore(concurrency)

    def route(self, capability="reasoning"):
        matches=[m for m in self.registry if capability in m.capabilities]
        if not matches:
            raise ProviderUnavailable(f"No model supports {capability}")
        return min(matches,key=lambda m:m.cost_per_million if m.cost_per_million is not None else float("inf"))

    async def structured(self, messages, schema: type[T], max_tokens=1200, on_usage=None) -> T:
        async with self.gate:
            for attempt in range(2):
                completion=await self.provider.complete(messages,schema.model_json_schema(),max_tokens)
                if on_usage:
                    on_usage(completion)
                try:
                    return schema.model_validate_json(completion.text)
                except ValidationError as exc:
                    if attempt:
                        raise InvalidModelOutput("Structured output invalid after one repair; no action executed") from exc
                    messages=[*messages,{"role":"assistant","content":completion.text[:16000]},{"role":"user","content":"Return only JSON matching the supplied schema. Repair the structure; do not execute anything. Validation: "+str(exc)[:1500]}]
        raise InvalidModelOutput("No structured result")


def make_provider(settings):
    if settings.provider == "ollama":
        return OllamaProvider(settings)
    if settings.provider in {"openai-compatible", "vllm"}:
        return (FutureVLLMProvider if settings.provider == "vllm" else OpenAICompatibleProvider)(settings)
    raise ValueError("Use ollama, openai-compatible, or vllm. MockProvider is injection-only for tests.")
