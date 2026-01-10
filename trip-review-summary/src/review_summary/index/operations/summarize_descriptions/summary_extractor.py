import json
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from tiktoken import encoding_name_for_model

from review_summary.prompts.index.summarize_descriptions import SUMMARIZE_PROMPT
from review_summary.tokenizer.tiktoken import TiktokenTokenizer

# These tokens are used in the prompt
ENTITY_NAME_KEY = "entity_name"
DESCRIPTION_LIST_KEY = "description_list"
MAX_LENGTH_KEY = "max_length"


@dataclass
class SummarizationResult:
    id: str | tuple[str, str]
    description: str


class SummaryExtractor:
    def __init__(
        self,
        chat_model: ChatOpenAI,
        max_summary_length: int,
        max_input_tokens: int,
        summarization_prompt: str | None = None,
    ):
        """Init method definition."""
        self._model = chat_model
        encoding_name = encoding_name_for_model(chat_model.model_name)
        self._tokenizer = TiktokenTokenizer(encoding_name)
        self._summarization_prompt = summarization_prompt or SUMMARIZE_PROMPT
        self._max_summary_length = max_summary_length
        self._max_input_tokens = max_input_tokens

    async def __call__(
        self, id: str | tuple[str, str], descriptions: list[str]
    ) -> SummarizationResult:
        """Call method definition."""
        result = ""
        if len(descriptions) == 0:
            result = ""
        elif len(descriptions) == 1:
            result = descriptions[0]
        else:
            result = await self._summarize_descriptions(id, descriptions)

        return SummarizationResult(id=id, description=result or "")

    async def _summarize_descriptions(
        self, id: str | tuple[str, str], descriptions: list[str]
    ) -> str:
        """Summarize descriptions into a single description."""
        sorted_id = sorted(id) if isinstance(id, list) else id

        # Sort description lists
        if len(descriptions) > 1:
            descriptions = sorted(descriptions)

        # Iterate over descriptions, adding all until the max input tokens is reached
        usable_tokens = self._max_input_tokens - self._tokenizer.num_tokens(
            self._summarization_prompt
        )
        descriptions_collected: list[str] = []
        result = ""

        for i, description in enumerate(descriptions):
            usable_tokens -= self._tokenizer.num_tokens(description)
            descriptions_collected.append(description)

            # If buffer is full, or all descriptions have been added, summarize
            if (usable_tokens < 0 and len(descriptions_collected) > 1) or (
                i == len(descriptions) - 1
            ):
                # Calculate result (final or partial)
                result = await self._summarize_descriptions_with_llm(
                    sorted_id, descriptions_collected
                )

                # If we go for another loop, reset values to new
                if i != len(descriptions) - 1:
                    descriptions_collected = [result]
                    usable_tokens = (
                        self._max_input_tokens
                        - self._tokenizer.num_tokens(self._summarization_prompt)
                        - self._tokenizer.num_tokens(result)
                    )

        return result

    async def _summarize_descriptions_with_llm(
        self, id: str | tuple[str, str] | list[str], descriptions: list[str]
    ) -> str:
        """Summarize descriptions using the LLM."""
        response = await self._model.ainvoke(
            self._summarization_prompt.format(
                **{
                    ENTITY_NAME_KEY: json.dumps(id, ensure_ascii=False),
                    DESCRIPTION_LIST_KEY: json.dumps(
                        sorted(descriptions), ensure_ascii=False
                    ),
                    MAX_LENGTH_KEY: self._max_summary_length,
                }
            ),
        )
        return response.text
