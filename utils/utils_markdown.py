def code_block(text, language: str = "") -> str:
    return f"```{language}\n{text}\n```"


def code_inline(text) -> str:
    return f"<code>{text}</code>"
