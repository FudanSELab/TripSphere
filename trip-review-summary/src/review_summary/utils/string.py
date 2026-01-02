# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""String utilities."""

import html
import re


def clean_str(input: str) -> str:
    """Clean an input string by removing HTML escapes,
    control characters, and other unwanted characters.
    """
    result = html.unescape(input.strip())
    # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result)
