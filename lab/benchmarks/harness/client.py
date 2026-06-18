"""Chat client for a local model served by Ollama (native /api/chat).

Uses the native Ollama endpoint (not /v1) so we get full control over
``options`` - temperature, top_p, top_k, seed, and crucially ``num_ctx`` for
long-reasoning models - plus token-timing fields for tok/s. stdlib only.
"""
from __future__ import annotations

import json
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
class Completion:
    text: str
    prompt_tokens: int = 0
    gen_tokens: int = 0
    gen_tok_per_s: float = 0.0
    wall_s: float = 0.0


@dataclass
class ChatClient:
    """Minimal Ollama chat client. One request per sample (Ollama has no n=k)."""

    model: str
    base_url: str = "http://localhost:11434"
    sampling: SamplingConfig = field(default_factory=SamplingConfig)
    timeout: int = 600

    def complete(self, messages: list[dict], system: str | None = None) -> Completion:
        msgs = ([{"role": "system", "content": system}] if system else []) + messages
        payload = {
            "model": self.model,
            "messages": msgs,
            "stream": False,
            "options": self.sampling.to_options(),
        }
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
        text = (body.get("message") or {}).get("content", "")
        gen_tokens = int(body.get("eval_count") or 0)
        eval_ns = int(body.get("eval_duration") or 0)
        tok_s = (gen_tokens / (eval_ns / 1e9)) if eval_ns else 0.0
        return Completion(
            text=text,
            prompt_tokens=int(body.get("prompt_eval_count") or 0),
            gen_tokens=gen_tokens,
            gen_tok_per_s=round(tok_s, 2),
            wall_s=round(wall, 2),
        )

    def describe(self) -> dict:
        return {"model": self.model, "base_url": self.base_url, **asdict(self.sampling)}
