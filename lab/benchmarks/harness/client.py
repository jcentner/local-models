"""Chat clients for models under test.

Two providers, one ``complete() -> Completion`` contract:

- ``OllamaClient`` (local daily driver) uses the native ``/api/chat`` endpoint so
  we keep full control over ``options`` - temperature, top_p, top_k, seed, and
  crucially ``num_ctx`` / ``think`` for long-reasoning models - plus native
  ``eval_count``/``eval_duration`` tok/s timing.
- ``OpenAICompatibleClient`` hits ``{base_url}/chat/completions`` (base_url already
  ends in ``/v1``). Covers hosted APIs (e.g. Z.AI GLM) AND a local model via
  Ollama's OpenAI shim on ``:11434/v1``. tok/s is queue-free when the server
  reports a llama.cpp ``timings.predicted_ms`` block; else it falls back to
  wall-based (queue-inflated at concurrency>1).

stdlib only. Cost is computed by the caller (run.py) from token totals + prices.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field


@dataclass
class SamplingConfig:
    temperature: float = 1.0
    top_p: float = 0.95
    top_k: int = 0           # 0 = disabled in Ollama (== top_k -1 elsewhere)
    num_predict: int = 4096  # max new tokens
    num_ctx: int = 8192      # context window; raise for long-CoT models
    seed: int | None = None
    think: bool | None = None  # None = model default; False disables CoT (thinking models)

    def to_options(self) -> dict:
        opts = {
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "num_predict": self.num_predict,
            "num_ctx": self.num_ctx,
        }
        if self.seed is not None:
            opts["seed"] = self.seed
        return opts


@dataclass
class ToolCall:
    """A normalized native tool call (provider-agnostic).

    ``arguments`` is always a parsed dict. ``id`` is the provider's call id
    (OpenAI needs it to match the tool result; Ollama has none, stays "").
    """
    name: str
    arguments: dict = field(default_factory=dict)
    id: str = ""


@dataclass
class Completion:
    text: str
    prompt_tokens: int = 0
    gen_tokens: int = 0
    gen_tok_per_s: float = 0.0
    wall_s: float = 0.0
    compute_s: float = 0.0   # queue-free generation compute (Ollama eval_duration / llama.cpp predicted_ms); 0 = unknown
    tool_calls: list = field(default_factory=list)   # list[ToolCall], native mode
    raw_message: dict = field(default_factory=dict)  # provider-native assistant msg to echo back


_XML_FUNC_RE = re.compile(r'<function\s+name="([^"]+)"\s*>(.*?)</function>', re.DOTALL)
_XML_PARAM_RE = re.compile(r'<param\s+name="([^"]+)"\s*>(.*?)</param>', re.DOTALL)


def parse_xml_tool_calls(text: str) -> tuple[list, str]:
    """Fallback parser for MiniCPM-style XML tool calls embedded in content:

        <function name="NAME"><param name="KEY">VALUE</param>...</function>

    Returns ``(calls, cleaned_text)`` - ``calls`` is a list[ToolCall] (param
    values kept as strings), ``cleaned_text`` is the content with the function
    blocks removed. Returns ``([], text)`` if none found. Used when a provider
    returns no native ``tool_calls`` but the model emitted XML calls in the text
    (e.g. MiniCPM5 served by SGLang without - or with a mismatched - tool-call
    parser). Guarded by a cheap substring check so non-XML models are untouched.
    """
    if not text or "<function name=" not in text:
        return [], text
    calls = []
    for i, m in enumerate(_XML_FUNC_RE.finditer(text)):
        args = {k: v.strip() for k, v in _XML_PARAM_RE.findall(m.group(2))}
        calls.append(ToolCall(name=m.group(1), arguments=args, id=f"xmlcall_{i}"))
    cleaned = _XML_FUNC_RE.sub("", text).strip()
    return calls, cleaned


@dataclass
class OllamaClient:
    """Minimal Ollama chat client. One request per sample (Ollama has no n=k)."""

    model: str
    base_url: str = "http://localhost:11434"
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    timeout: int = 600

    def complete(self, messages: list[dict], system: str | None = None,
                 tools: list[dict] | None = None) -> Completion:
        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        payload = {
            "model": self.model,
            "messages": msgs,
            "stream": False,
            "options": self.sampling.to_options(),
        }
        if tools:
            payload["tools"] = tools
        if self.sampling.think is not None:
            payload["think"] = self.sampling.think
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.URLError as e:  # pragma: no cover - network dependent
            raise RuntimeError(
                f"Ollama request to {self.base_url}/api/chat failed: {e}. "
                "Is `ollama serve` running and the model pulled?"
            ) from e
        wall = time.monotonic() - t0
        msg = body.get("message") or {}
        text = msg.get("content", "")
        gen_tokens = int(body.get("eval_count") or 0)
        eval_ns = int(body.get("eval_duration") or 0)
        tok_s = (gen_tokens / (eval_ns / 1e9)) if eval_ns else 0.0
        compute_s = eval_ns / 1e9   # queue-free generation compute (eval only; excludes prompt + queue wait)
        calls = []
        for tc in (msg.get("tool_calls") or []):
            fn = tc.get("function") or {}
            args = fn.get("arguments")
            if isinstance(args, str):  # some shims return a JSON string
                try:
                    args = json.loads(args)
                except (json.JSONDecodeError, ValueError):
                    args = {}
            if not isinstance(args, dict):  # guard: a list/scalar would crash apply()
                args = {}
            calls.append(ToolCall(name=fn.get("name", ""), arguments=args))
        if not calls:  # XML-in-content fallback (e.g. MiniCPM5 emitting <function ...>)
            xml_calls, cleaned = parse_xml_tool_calls(text)
            if xml_calls:
                calls, text = xml_calls, cleaned
                msg = {"role": "assistant", "content": cleaned,
                       "tool_calls": [{"function": {"name": c.name, "arguments": c.arguments}}
                                      for c in calls]}
        return Completion(
            text=text,
            prompt_tokens=int(body.get("prompt_eval_count") or 0),
            gen_tokens=gen_tokens,
            gen_tok_per_s=round(tok_s, 2),
            wall_s=round(wall, 2),
            compute_s=round(compute_s, 2),
            tool_calls=calls,
            raw_message=msg,
        )

    def tool_result_message(self, call: ToolCall, content: str) -> dict:
        """Build the Ollama-native tool-result message to append to history."""
        return {"role": "tool", "content": content, "tool_name": call.name}

    def describe(self) -> dict:
        return {"provider": "ollama", "model": self.model, "base_url": self.base_url,
                **asdict(self.sampling)}


@dataclass
class OpenAICompatibleClient:
    """OpenAI-compatible chat client (hosted APIs or Ollama's :11434/v1 shim).

    ``base_url`` must already include ``/v1`` (e.g. ``http://localhost:11434/v1``
    or ``https://api.z.ai/api/paas/v4``). The API key, when needed, is read from
    the environment variable named by ``api_key_env`` - never passed literally.
    """

    model: str
    base_url: str = "http://localhost:11434/v1"
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    api_key_env: str | None = None
    timeout: int = 600

    def _auth_header(self) -> dict:
        if not self.api_key_env:
            return {}
        key = os.environ.get(self.api_key_env)
        if not key:
            # localhost (Ollama shim) needs no key; a remote host does.
            host = self.base_url.split("//", 1)[-1]
            if host.startswith(("localhost", "127.0.0.1")):
                return {}
            raise RuntimeError(
                f"--api-key-env {self.api_key_env} is set but env var is empty; "
                f"export it (never put the key on the CLI) for {self.base_url}."
            )
        return {"Authorization": f"Bearer {key}"}

    def complete(self, messages: list[dict], system: str | None = None,
                 tools: list[dict] | None = None) -> Completion:
        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        s = self.sampling
        payload = {
            "model": self.model,
            "messages": msgs,
            "stream": False,
            "temperature": s.temperature,
            "top_p": s.top_p,
            "max_tokens": s.num_predict,
        }
        if tools:
            payload["tools"] = tools
        if s.seed is not None:
            payload["seed"] = s.seed
        if s.think is not None:
            # SGLang/transformers chat-template flag to toggle a hybrid model's
            # CoT (the openai-compatible analogue of Ollama's `think`). Servers
            # that don't support it ignore the unknown field.
            payload["chat_template_kwargs"] = {"enable_thinking": s.think}
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers={"Content-Type": "application/json", **self._auth_header()},
            method="POST",
        )
        t0 = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:  # pragma: no cover - network dependent
            detail = e.read().decode("utf-8", "replace")[:300]
            raise RuntimeError(
                f"OpenAI-compatible request to {self.base_url} failed: {e.code} {detail}"
            ) from e
        except urllib.error.URLError as e:  # pragma: no cover - network dependent
            raise RuntimeError(
                f"OpenAI-compatible request to {self.base_url} failed: {e}."
            ) from e
        wall = time.monotonic() - t0
        choices = body.get("choices") or [{}]
        msg = (choices[0] or {}).get("message") or {}
        text = msg.get("content", "") or ""
        usage = body.get("usage") or {}
        gen_tokens = int(usage.get("completion_tokens") or 0)
        # llama.cpp server reports queue-free generation timing in a top-level
        # ``timings`` block (predicted_ms = generation-only). Use it so tok/s is
        # queue-free under concurrency; hosted APIs without it fall back to wall.
        timings = body.get("timings") or {}
        compute_s = float(timings.get("predicted_ms") or 0.0) / 1000.0
        tok_s = (gen_tokens / compute_s) if compute_s else ((gen_tokens / wall) if wall else 0.0)
        calls = []
        for tc in (msg.get("tool_calls") or []):
            fn = tc.get("function") or {}
            raw = fn.get("arguments")
            if isinstance(raw, str):
                try:
                    args = json.loads(raw) if raw.strip() else {}
                except (json.JSONDecodeError, ValueError):
                    args = {}
            else:
                args = raw
            if not isinstance(args, dict):  # guard: a list/scalar would crash apply()
                args = {}
            calls.append(ToolCall(name=fn.get("name", ""), arguments=args, id=tc.get("id", "")))
        if not calls:  # XML-in-content fallback (e.g. MiniCPM5 over a parser-less SGLang)
            xml_calls, cleaned = parse_xml_tool_calls(text)
            if xml_calls:
                calls, text = xml_calls, cleaned
                msg = {"role": "assistant", "content": cleaned or None,
                       "tool_calls": [{"id": c.id, "type": "function",
                                       "function": {"name": c.name, "arguments": json.dumps(c.arguments)}}
                                      for c in calls]}
        return Completion(
            text=text,
            prompt_tokens=int(usage.get("prompt_tokens") or 0),
            gen_tokens=gen_tokens,
            gen_tok_per_s=round(tok_s, 2),
            wall_s=round(wall, 2),
            compute_s=round(compute_s, 2),
            tool_calls=calls,
            raw_message=msg,
        )

    def tool_result_message(self, call: ToolCall, content: str) -> dict:
        """Build the OpenAI-native tool-result message (matched by tool_call_id)."""
        return {"role": "tool", "tool_call_id": call.id, "content": content}

    def describe(self) -> dict:
        return {"provider": "openai-compatible", "model": self.model,
                "base_url": self.base_url, "api_key_env": self.api_key_env,
                **asdict(self.sampling)}


# Back-compat alias (older imports expect ChatClient = the Ollama client).
ChatClient = OllamaClient


def make_client(provider: str, model: str, base_url: str | None,
                sampling: SamplingConfig, api_key_env: str | None = None,
                timeout: int = 600):
    """Factory: pick a client by provider. ``base_url=None`` uses the provider default."""
    if provider == "ollama":
        return OllamaClient(model=model, base_url=base_url or "http://localhost:11434",
                            sampling=sampling, timeout=timeout)
    if provider == "openai-compatible":
        return OpenAICompatibleClient(
            model=model, base_url=base_url or "http://localhost:11434/v1",
            sampling=sampling, api_key_env=api_key_env, timeout=timeout)
    raise ValueError(f"unknown provider {provider!r} (expected ollama|openai-compatible)")
