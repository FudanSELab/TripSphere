# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LocalSearch implementation."""

import logging
import time
from collections.abc import AsyncGenerator

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from review_summary.callbacks.query_callbacks import QueryCallbacks
from review_summary.prompts.query.local_search_system_prompt import (
    LOCAL_SEARCH_SYSTEM_PROMPT,
)
from review_summary.query.base import SearchResult
from review_summary.query.context_builder.conversation_history import (
    ConversationHistory,
)
from review_summary.query.structured_search.local_search.mixed_content import (
    LocalSearchMixedContext,
)
from review_summary.tokenizer.tokenizer import Tokenizer

logger = logging.getLogger(__name__)


class LocalSearch:
    """Search orchestration for local search mode."""

    def __init__(
        self,
        chat_model: ChatOpenAI,
        context_builder: LocalSearchMixedContext,
        tokenizer: Tokenizer,
        system_prompt: str | None = None,
        response_type: str = "multiple paragraphs",
        callbacks: list[QueryCallbacks] | None = None,
    ):
        self.chat_model = chat_model
        self.context_builder = context_builder
        self.tokenizer = tokenizer

        self.system_prompt = system_prompt or LOCAL_SEARCH_SYSTEM_PROMPT
        self.callbacks = callbacks or []
        self.response_type = response_type

    async def search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        target_id: str = "",
    ) -> SearchResult:
        """Build local search context that fits a single
        context window and generate answer for the user query."""
        start_time = time.time()
        search_prompt = ""
        llm_calls: dict[str, int] = {}
        prompt_tokens: dict[str, int] = {}
        output_tokens: dict[str, int] = {}
        context_result = await self.context_builder.build_context(
            query=query, conversation_history=conversation_history, target_id=target_id
        )
        llm_calls["build_context"] = context_result.llm_calls
        prompt_tokens["build_context"] = context_result.prompt_tokens
        output_tokens["build_context"] = context_result.output_tokens

        logger.debug("GENERATE ANSWER: %s. QUERY: %s", start_time, query)
        try:
            search_prompt = self.system_prompt.format(
                context_data=context_result.context_chunks,
                response_type=self.response_type,
            )

            full_response = ""
            async for chunk in self.chat_model.astream(
                [SystemMessage(content=search_prompt), HumanMessage(content=query)]
            ):
                full_response += chunk.text
                for callback in self.callbacks:
                    callback.on_llm_new_token(chunk.text)

            llm_calls["response"] = 1
            prompt_tokens["response"] = len(self.tokenizer.encode(search_prompt))
            output_tokens["response"] = len(self.tokenizer.encode(full_response))

            for callback in self.callbacks:
                callback.on_context(context_result.context_records)

            return SearchResult(
                response=full_response,
                context_data=context_result.context_records,
                context_text=context_result.context_chunks,
                completion_time=time.time() - start_time,
                llm_calls=sum(llm_calls.values()),
                prompt_tokens=sum(prompt_tokens.values()),
                output_tokens=sum(output_tokens.values()),
                llm_calls_categories=llm_calls,
                prompt_tokens_categories=prompt_tokens,
                output_tokens_categories=output_tokens,
            )

        except Exception:
            logger.exception("Exception in _asearch")
            return SearchResult(
                response="",
                context_data=context_result.context_records,
                context_text=context_result.context_chunks,
                completion_time=time.time() - start_time,
                llm_calls=1,
                prompt_tokens=len(self.tokenizer.encode(search_prompt)),
                output_tokens=0,
            )

    async def stream_search(
        self,
        query: str,
        conversation_history: ConversationHistory | None = None,
        target_id: str = "",
    ) -> AsyncGenerator[str, None]:
        """Build local search context that fits a single
        context window and generate answer for the user query."""
        start_time = time.time()

        context_result = await self.context_builder.build_context(
            query=query, conversation_history=conversation_history, target_id=target_id
        )
        logger.debug("GENERATE ANSWER: %s. QUERY: %s", start_time, query)
        search_prompt = self.system_prompt.format(
            context_data=context_result.context_chunks, response_type=self.response_type
        )

        for callback in self.callbacks:
            callback.on_context(context_result.context_records)

        async for chunk in self.chat_model.astream(
            [SystemMessage(content=search_prompt), HumanMessage(content=query)]
        ):
            for callback in self.callbacks:
                callback.on_llm_new_token(chunk.text)
            yield chunk.text
