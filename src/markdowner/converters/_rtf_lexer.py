# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""RTF lexer - tokenizes RTF text into meaningful tokens."""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Iterator, Optional


class TokenType(Enum):
    """Types of tokens in RTF."""
    GROUP_START = "group_start"
    GROUP_END = "group_end"
    CONTROL_WORD = "control_word"
    CONTROL_SYMBOL = "control_symbol"
    TEXT = "text"
    EOF = "eof"


@dataclass(frozen=True)
class Token:
    """A token from the RTF source."""
    type: TokenType
    value: str
    param: Optional[int] = None
    position: int = 0


class RtfLexer:
    """Lexical analyzer for RTF documents."""

    CONTROL_PATTERN = re.compile(
        br"(?:(?P<group_start>\{)|"
        br"(?P<group_end>\})|"
        br"(?P<escaped_braces>\\[{}])|"
        br"(?P<escaped_backslash>\\\\)|"
        br"(?P<control_word>\\(?P<word>[a-zA-Z]+)(?P<param>-?\d+)?(?P<delim>[ ]?))|"
        br"(?P<control_symbol>\\(?P<sym>[^a-zA-Z{}\\]))(?:(?P<symparam>[0-9a-fA-F]{2}|\d+))?)",
        re.DOTALL
    )

    def __init__(self, content: bytes):
        self.content = content
        self.position = 0
        self.text_buffer: list[bytes] = []

    def _decode_text(self) -> str:
        """Decode accumulated text buffer to string."""
        if not self.text_buffer:
            return ""
        text = b"".join(self.text_buffer)
        self.text_buffer = []
        return text.decode("cp1252", errors="replace")

    def __iter__(self) -> Iterator[Token]:
        """Iterate through tokens."""
        while self.position < len(self.content):
            match = self.CONTROL_PATTERN.match(self.content, self.position)
            if not match:
                self.text_buffer.append(self.content[self.position:self.position + 1])
                self.position += 1
                continue

            text = self._decode_text()
            if text:
                yield Token(TokenType.TEXT, text, position=self.position)

            if match.group("group_start"):
                text = self._decode_text()
                if text:
                    yield Token(TokenType.TEXT, text, position=self.position)
                yield Token(TokenType.GROUP_START, "{", position=self.position)
                self.position = match.end()
                continue

            if match.group("group_end"):
                text = self._decode_text()
                if text:
                    yield Token(TokenType.TEXT, text, position=self.position)
                yield Token(TokenType.GROUP_END, "}", position=self.position)
                self.position = match.end()
                continue

            if match.group("escaped_braces"):
                escaped = match.group("escaped_braces").decode("ascii")
                if escaped == "\\{":
                    yield Token(TokenType.CONTROL_SYMBOL, "{", position=self.position)
                elif escaped == "\\}":
                    yield Token(TokenType.CONTROL_SYMBOL, "}", position=self.position)
                else:
                    yield Token(TokenType.CONTROL_SYMBOL, escaped, position=self.position)
                self.position = match.end()
                continue

            if match.group("escaped_backslash"):
                yield Token(
                    TokenType.CONTROL_SYMBOL,
                    "\\",
                    position=self.position
                )
                self.position = match.end()
                continue

            if match.group("control_word"):
                word = match.group("word").decode("ascii")
                param_str = match.group("param")
                param = int(param_str) if param_str else None
                yield Token(
                    TokenType.CONTROL_WORD,
                    word,
                    param=param,
                    position=self.position
                )
                self.position = match.end()
                continue

            if match.group("control_symbol"):
                sym = match.group("sym").decode("ascii")
                param_str = match.group("symparam")
                if param_str:
                    try:
                        param = int(param_str, 16) if sym == "'" else int(param_str)
                    except ValueError:
                        param = None
                else:
                    param = None
                yield Token(
                    TokenType.CONTROL_SYMBOL,
                    sym,
                    param=param,
                    position=self.position
                )
                self.position = match.end()
                continue

        text = self._decode_text()
        if text:
            yield Token(TokenType.TEXT, text, position=self.position)

        yield Token(TokenType.EOF, "", position=self.position)

    def tokenize(self) -> list[Token]:
        """Tokenize the entire RTF content."""
        return list(self)


def tokenize_rtf(content: bytes) -> list[Token]:
    """Convenience function to tokenize RTF content."""
    return RtfLexer(content).tokenize()
