import pandas as pd

class ContextBuilderResult:
    """A class to hold the results of the build_context."""

    context_chunks: str | list[str]
    context_records: dict[str, pd.DataFrame]
    llm_calls: int = 0
    prompt_tokens: int = 0
    output_tokens: int = 0