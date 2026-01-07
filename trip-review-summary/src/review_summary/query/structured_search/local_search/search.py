# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""LocalSearch implementation."""

import logging
import time
from collections.abc import AsyncGenerator
from typing import Any

from langchain_openai import ChatOpenAI

from review_summary.callbacks.query_callbacks import QueryCallbacks
from review_summary.prompts.query.local_search_system_prompt import (
    LOCAL_SEARCH_SYSTEM_PROMPT,
)
from review_summary.query.base import SearchResult
from review_summary.query.context_builder.conversation_history import (
    ConversationHistory,
)
from review_summary.query.model_wrraper.chat_model import ModelWrapper
from review_summary.query.structured_search.local_search.mixed_content import (
    LocalSearchMixedContext,
)
from review_summary.tokenizer.tokenizer import Tokenizer

logger = logging.getLogger(__name__)


class LocalSearch:
    """Search orchestration for local search mode."""

    def __init__(
        self,
        model: ChatOpenAI,
        context_builder: LocalSearchMixedContext,
        tokenizer: Tokenizer | None = None,
        system_prompt: str | None = None,
        response_type: str = "multiple paragraphs",
        callbacks: list[QueryCallbacks] | None = None,
        model_params: dict[str, Any] | None = None,
    ):
        self.model = model
        self.context_builder = context_builder
        self.tokenizer = tokenizer
        self.model_params = model_params

        self.system_prompt = system_prompt or LOCAL_SEARCH_SYSTEM_PROMPT
        self.callbacks = callbacks or []
        self.response_type = response_type

    async def search(
        self, query: str, conversation_history: ConversationHistory | None = None
    ) -> SearchResult:
        """Build local search context that fits a single
        context window and generate answer for the user query."""
        start_time = time.time()
        search_prompt = ""
        llm_calls, prompt_tokens, output_tokens = {}, {}, {}
        context_result = await self.context_builder.build_context(
            query=query, conversation_history=conversation_history
        )
        llm_calls["build_context"] = context_result.llm_calls
        prompt_tokens["build_context"] = context_result.prompt_tokens
        output_tokens["build_context"] = context_result.output_tokens

        logger.debug("GENERATE ANSWER: %s. QUERY: %s", start_time, query)
        model_wrapper = ModelWrapper(model=self.model)
        try:
            search_prompt = self.system_prompt.format(
                context_data=context_result.context_chunks,
                response_type=self.response_type,
            )
            history_messages = [
                {"role": "system", "content": search_prompt},
            ]

            full_response = ""
            async for response in model_wrapper.chat_stream(
                query=query, history=history_messages
            ):
                full_response += response
                for callback in self.callbacks:
                    callback.on_llm_new_token(response)

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
    ) -> AsyncGenerator:
        """Build local search context that fits a single
        context window and generate answer for the user query."""
        start_time = time.time()

        context_result = self.context_builder.build_context(
            query=query, conversation_history=conversation_history
        )
        logger.debug("GENERATE ANSWER: %s. QUERY: %s", start_time, query)
        search_prompt = self.system_prompt.format(
            context_data=context_result.context_chunks, response_type=self.response_type
        )
        history_messages = [
            {"role": "system", "content": search_prompt},
        ]

        model_wrapper = ModelWrapper(model=self.model)

        for callback in self.callbacks:
            callback.on_context(context_result.context_records)

        async for response in model_wrapper.chat_stream(
            query=query,
            history=history_messages,
        ):
            for callback in self.callbacks:
                callback.on_llm_new_token(response)
            yield response
