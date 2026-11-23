import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, AsyncGenerator, Coroutine
import structlog
from openai import AsyncOpenAI

from app.core.config import get_settings

logger = structlog.get_logger()


class LLMProvider(ABC):
    @abstractmethod
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Coroutine[Any, Any, AsyncGenerator[str, None]]:
        pass


class OpenAICompatibleProvider(LLMProvider):
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.LLM_API_KEY,
            base_url=self.settings.LLM_BASE_URL,
            timeout=self.settings.LLM_TIMEOUT,
        )
        self.model = self.settings.LLM_MODEL

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"

        response = await self.client.chat.completions.create(**kwargs)
        return self._parse_response(response)

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"

        stream = await self.client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _parse_response(self, response) -> Dict[str, Any]:
        message = response.choices[0].message
        result: Dict[str, Any] = {
            "content": message.content or "",
            "tool_calls": [],
        }
        if message.tool_calls:
            for tc in message.tool_calls:
                result["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })
        return result


class NVIDIANIMProvider(LLMProvider):
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.LLM_API_KEY,
            base_url=self.settings.LLM_BASE_URL,
            timeout=self.settings.LLM_TIMEOUT,
        )
        self.model = self.settings.LLM_MODEL

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"

        response = await self.client.chat.completions.create(**kwargs)
        return self._parse_response(response)

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"

        stream = await self.client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _parse_response(self, response) -> Dict[str, Any]:
        message = response.choices[0].message
        result: Dict[str, Any] = {
            "content": message.content or "",
            "tool_calls": [],
        }
        if message.tool_calls:
            for tc in message.tool_calls:
                result["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })
        return result


class GroqProvider(LLMProvider):
    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.LLM_API_KEY,
            base_url=self.settings.LLM_BASE_URL,
            timeout=self.settings.LLM_TIMEOUT,
        )
        self.model = self.settings.LLM_MODEL

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"

        response = await self.client.chat.completions.create(**kwargs)
        return self._parse_response(response)

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ):
        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = tool_choice or "auto"

        stream = await self.client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _parse_response(self, response) -> Dict[str, Any]:
        message = response.choices[0].message
        result: Dict[str, Any] = {
            "content": message.content or "",
            "tool_calls": [],
        }
        if message.tool_calls:
            for tc in message.tool_calls:
                result["tool_calls"].append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments),
                })
        return result


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider_name = settings.LLM_PROVIDER.lower()

    if provider_name == "nvidia-nim":
        return NVIDIANIMProvider()
    elif provider_name == "groq":
        return GroqProvider()
    else:
        return OpenAICompatibleProvider()