from review_summary.tokenizer.tiktoken import encoding_name_for_chat_model


def test_qwen_model_uses_compatible_fallback_encoding() -> None:
    assert encoding_name_for_chat_model("qwen-plus") == "cl100k_base"
