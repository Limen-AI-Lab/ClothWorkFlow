"""
基于 LiteLLM 的 AWS Bedrock Chat Model 适配器
支持 Bearer Token 认证（AWS_BEARER_TOKEN_BEDROCK 环境变量）
"""

import json
from dataclasses import dataclass
from typing import Any, TypeVar, overload

import litellm
from pydantic import BaseModel

from browser_use.llm.base import BaseChatModel
from browser_use.llm.exceptions import ModelProviderError, ModelRateLimitError
from browser_use.llm.messages import BaseMessage
from browser_use.llm.openai.serializer import OpenAIMessageSerializer
from browser_use.llm.schema import SchemaOptimizer
from browser_use.llm.views import ChatInvokeCompletion, ChatInvokeUsage

T = TypeVar("T", bound=BaseModel)


@dataclass
class ChatLiteLLMBedrock(BaseChatModel):
    """
    通过 LiteLLM 调用 AWS Bedrock，支持 Bearer Token 认证。
    环境变量 AWS_BEARER_TOKEN_BEDROCK 和 AWS_REGION 需要提前设置。
    """

    model: str = "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0"
    max_tokens: int = 8192
    temperature: float | None = None
    top_p: float | None = None

    @property
    def provider(self) -> str:
        return "litellm_bedrock"

    @property
    def name(self) -> str:
        return self.model

    @overload
    async def ainvoke(
        self, messages: list[BaseMessage], output_format: None = None, **kwargs: Any
    ) -> ChatInvokeCompletion[str]: ...

    @overload
    async def ainvoke(
        self, messages: list[BaseMessage], output_format: type[T], **kwargs: Any
    ) -> ChatInvokeCompletion[T]: ...

    async def ainvoke(
        self,
        messages: list[BaseMessage],
        output_format: type[T] | None = None,
        **kwargs: Any,
    ) -> ChatInvokeCompletion[T] | ChatInvokeCompletion[str]:
        openai_messages = OpenAIMessageSerializer.serialize_messages(messages)

        params: dict[str, Any] = {
            "model": self.model,
            "messages": openai_messages,
            "max_tokens": self.max_tokens,
        }
        if self.temperature is not None:
            params["temperature"] = self.temperature
        if self.top_p is not None:
            params["top_p"] = self.top_p

        if output_format is not None:
            schema = SchemaOptimizer.create_optimized_json_schema(output_format)
            # 用 tool_choice 强制结构化输出
            params["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": "agent_output",
                        "description": "Structured output",
                        "parameters": schema,
                    },
                }
            ]
            params["tool_choice"] = {
                "type": "function",
                "function": {"name": "agent_output"},
            }

        try:
            response = await litellm.acompletion(**params)
        except litellm.RateLimitError as e:
            raise ModelRateLimitError(message=str(e), model=self.name) from e
        except Exception as e:
            raise ModelProviderError(message=str(e), model=self.name) from e

        choice = response.choices[0] if response.choices else None
        if choice is None:
            raise ModelProviderError(
                message="Empty response from Bedrock", model=self.name
            )

        # 解析 usage
        usage = None
        if response.usage:
            cached = None
            ptd = getattr(response.usage, "prompt_tokens_details", None)
            if ptd is not None:
                cached = getattr(ptd, "cached_tokens", None)
            usage = ChatInvokeUsage(
                prompt_tokens=response.usage.prompt_tokens or 0,
                prompt_cached_tokens=cached,
                prompt_cache_creation_tokens=None,
                prompt_image_tokens=None,
                completion_tokens=response.usage.completion_tokens or 0,
                total_tokens=response.usage.total_tokens or 0,
            )

        if output_format is None:
            return ChatInvokeCompletion(
                completion=choice.message.content or "",
                usage=usage,
                stop_reason=choice.finish_reason,
            )
        else:
            # 从 tool_calls 中提取结构化输出
            content = None
            if choice.message.tool_calls:
                content = choice.message.tool_calls[0].function.arguments
            elif choice.message.content:
                content = choice.message.content

            if not content:
                raise ModelProviderError(
                    message="No structured output in response", model=self.name
                )

            parsed = output_format.model_validate_json(
                content if isinstance(content, str) else json.dumps(content)
            )
            return ChatInvokeCompletion(
                completion=parsed,
                usage=usage,
                stop_reason=choice.finish_reason,
            )
