"""
Markdown code block extraction utilities.

Features:
- Extract code blocks from markdown text
- Filter by programming language
- Multiple output formats (string/list/dict)
- Flexible fence handling (``` or ~~~)
- Robust regex pattern matching
"""

import re
from typing import Dict, List, Optional, Union


def extract_code_block(
    str_to_parse: str,
    return_as_list: bool = False,
    languages: Optional[List[str]] = None,
    categorize: bool = False,
) -> Union[str, List[str], Dict[str, List[str]]]:
    """
    Extract code blocks from Markdown-formatted text.

    Identifies code blocks enclosed by triple backticks (```) or tildes (~~~),
    extracts their content, and can filter by programming language. Provides
    multiple output formats for flexibility.

    Args:
        str_to_parse: Input string containing Markdown code blocks.
        return_as_list: If True, returns list of code blocks instead of string.
        languages: List of languages to filter code blocks. None for all.
        categorize: If True, returns dict mapping languages to code blocks.

    Returns:
        One of:
        - str: Concatenated code blocks separated by newlines
        - List[str]: List of individual code blocks
        - Dict[str, List[str]]: Language-categorized code blocks

    Examples:
        >>> text = '''
        ... ```python
        ... def hello():
        ...     print("Hello")
        ... ```
        ... ```java
        ... class Main {
        ...     public static void main() {}
        ... }
        ... ```
        ... '''
        >>> print(extract_code_block(text, languages=['python']))
        def hello():
            print("Hello")

        >>> blocks = extract_code_block(text, return_as_list=True)
        >>> len(blocks)
        2

        >>> by_lang = extract_code_block(text, categorize=True)
        >>> list(by_lang.keys())
        ['python', 'java']
    """
    code_blocks: List[str] = []
    code_dict: Dict[str, List[str]] = {}

    # Compile regex pattern
    pattern = re.compile(
        r"""
        ^(?P<fence>```|~~~)[ \t]*     # Opening fence with optional whitespace
        (?P<lang>[\w+-]*)[ \t]*\n     # Language identifier
        (?P<code>.*?)(?<=\n)          # Code content
        ^(?P=fence)[ \t]*$            # Matching closing fence
        """,
        re.MULTILINE | re.DOTALL | re.VERBOSE,
    )

    # Extract code blocks
    for match in pattern.finditer(str_to_parse):
        lang = match.group("lang") or "plain"
        code = match.group("code")

        if languages is None or lang in languages:
            if categorize:
                if lang not in code_dict:
                    code_dict[lang] = []
                code_dict[lang].append(code)
            else:
                code_blocks.append(code)

    # Return appropriate format
    if categorize:
        return code_dict
    elif return_as_list:
        return code_blocks
    else:
        return "\n\n".join(code_blocks)


__all__ = ["extract_code_block"]
