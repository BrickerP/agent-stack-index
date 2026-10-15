"""Provider adapters. Each adapter turns (model, prompt) into one HTTP call and a Completion.

Adding an API shape = add a builder pair to KINDS. Secrets and base URLs come from env vars named
in config/models.toml, never from files in this repository.
"""
from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field

from .config import Model, Provider, Workspace

RETRYABLE = {408, 409, 425, 429, 500, 502, 503, 504, 520, 522, 524, 529}
THINK = re.compile(r"<think>.*?</think>", re.S | re.I)


class ProviderError(Exception):
    def __init__(self, message: str, status: int | None = None, retryable: bool = False):
        super().__init__(message)
        self.status = status
        self.retryable = retryable


@dataclass
class Completion:
    text: str
    reported_model: str = ""
    usage: dict = field(default_factory=dict)
    finish_reason: str = ""
    status: int = 200
    latency_ms: int = 0
    attempts: int = 1


def _openai_chat(base, key, model: Model, prompt):
    body = {"model": model.route, "messages": [{"role": "user", "content": prompt}], **model.params}
    return f"{base}/chat/completions", {"Authorization": f"Bearer {key}"}, body


def _openai_chat_parse(data):
    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    return msg.get("content") or "", data.get("model", ""), data.get("usage") or {}, choice.get("finish_reason") or ""


def _openai_responses(base, key, model: Model, prompt):
    params = dict(model.params)
    if "max_tokens" in params:
        params["max_output_tokens"] = params.pop("max_tokens")
    return f"{base}/responses", {"Authorization": f"Bearer {key}"}, {"model": model.route, "input": prompt, **params}


def _openai_responses_parse(data):
    parts = []
    for item in data.get("output") or []:
        for content in item.get("content") or []:
            if content.get("type") in ("output_text", "text"):
                parts.append(content.get("text", ""))
    return "".join(parts), data.get("model", ""), data.get("usage") or {}, data.get("status", "")


def _anthropic(base, key, model: Model, prompt):
    params = {"max_tokens": 4000, **model.params}
    headers = {"x-api-key": key, "anthropic-version": "2023-06-01"}
    return f"{base}/messages", headers, {"model": model.route, "messages": [{"role": "user", "content": prompt}], **params}


def _anthropic_parse(data):
    text = "".join(c.get("text", "") for c in data.get("content") or [] if c.get("type") == "text")
    return text, data.get("model", ""), data.get("usage") or {}, data.get("stop_reason") or ""


KINDS = {
    "openai_chat": (_openai_chat, _openai_chat_parse),
    "openai_responses": (_openai_responses, _openai_responses_parse),
    "anthropic_messages": (_anthropic, _anthropic_parse),
}


def clean_text(text: str) -> str:
    return THINK.sub("", text or "").strip()


class HttpClient:
    """Calls real providers. One instance is shared by all worker threads."""

    def __init__(self, ws: Workspace, max_retries: int = 4):
        self.ws = ws
        self.max_retries = max_retries

    def complete(self, model: Model, prompt: str) -> Completion:
        provider: Provider = self.ws.providers[model.provider]
        if provider.kind not in KINDS:
            raise ProviderError(f"unknown provider kind {provider.kind}")
        base = os.environ.get(provider.base_url_env, "").rstrip("/")
        key = os.environ.get(provider.api_key_env, "")
        if not base or not key:
            raise ProviderError(f"set {provider.base_url_env} and {provider.api_key_env} in the environment")
        build, parse = KINDS[provider.kind]
        url, headers, body = build(base, key, model, prompt)
        started = time.monotonic()
        for attempt in range(1, self.max_retries + 2):
            try:
                status, data = _post(url, headers, body, provider.timeout_s)
                text, reported, usage, finish = parse(data)
                return Completion(
                    text=clean_text(text),
                    reported_model=reported,
                    usage=usage,
                    finish_reason=str(finish),
                    status=status,
                    latency_ms=int((time.monotonic() - started) * 1000),
                    attempts=attempt,
                )
            except ProviderError as exc:
                if not exc.retryable or attempt > self.max_retries:
                    raise
                time.sleep(min(60.0, 2 ** attempt + random.random()))
        raise ProviderError("unreachable")


def _post(url: str, headers: dict, body: dict, timeout: float):
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        if retry_after and retry_after.isdigit():
            time.sleep(min(60, int(retry_after)))
        raise ProviderError(f"HTTP {exc.code}: {detail}", exc.code, exc.code in RETRYABLE) from None
    except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
        raise ProviderError(f"network: {exc}", None, True) from None
    except json.JSONDecodeError as exc:
        raise ProviderError(f"bad JSON from provider: {exc}", None, True) from None


class FakeClient:
    """Deterministic client for tests and dry runs: answer(model, prompt) -> text."""

    def __init__(self, answer):
        self.answer = answer

    def complete(self, model: Model, prompt: str) -> Completion:
        return Completion(text=self.answer(model, prompt), reported_model=f"fake-{model.id}", latency_ms=1)
