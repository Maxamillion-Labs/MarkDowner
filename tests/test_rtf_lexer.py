# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""Test RTF lexer."""

import time

import pytest

from markdowner.converters._rtf_lexer import RtfLexer, Token, TokenType, tokenize_rtf


class TestRtfLexer:
    """Test RTF lexer tokenization."""

    def test_simple_text_token(self):
        """Simple text should produce TEXT token."""
        lexer = RtfLexer(b"Hello World")
        tokens = list(lexer)
        assert tokens[0].type == TokenType.TEXT
        assert tokens[0].value == "Hello World"

    def test_group_braces(self):
        """Group braces should produce GROUP_START and GROUP_END."""
        lexer = RtfLexer(b"{}")
        tokens = list(lexer)
        assert tokens[0].type == TokenType.GROUP_START
        assert tokens[1].type == TokenType.GROUP_END

    def test_control_word(self):
        """Control words should produce CONTROL_WORD tokens."""
        lexer = RtfLexer(b"\\par")
        tokens = list(lexer)
        assert tokens[0].type == TokenType.CONTROL_WORD
        assert tokens[0].value == "par"

    def test_control_word_with_param(self):
        """Control word with parameter."""
        lexer = RtfLexer(b"\\fs24")
        tokens = list(lexer)
        assert tokens[0].type == TokenType.CONTROL_WORD
        assert tokens[0].value == "fs"
        assert tokens[0].param == 24

    def test_escaped_braces(self):
        """Escaped braces should produce CONTROL_SYMBOL."""
        lexer = RtfLexer(b"\\{")
        tokens = list(lexer)
        assert tokens[0].type == TokenType.CONTROL_SYMBOL
        assert tokens[0].value == "{"

    def test_escaped_backslash(self):
        """Escaped backslash."""
        lexer = RtfLexer(b"\\\\")
        tokens = list(lexer)
        assert tokens[0].type == TokenType.CONTROL_SYMBOL
        assert tokens[0].value == "\\"

    def test_unicode_control(self):
        """Unicode control word."""
        lexer = RtfLexer(b"\\u233")
        tokens = list(lexer)
        assert tokens[0].type == TokenType.CONTROL_WORD
        assert tokens[0].value == "u"
        assert tokens[0].param == 233

    def test_simple_rtf_document(self):
        """Full RTF document tokenization."""
        content = b"{\\rtf1\\ansi Hello}"
        tokens = list(RtfLexer(content))
        token_types = [t.type for t in tokens]
        assert TokenType.GROUP_START in token_types
        assert TokenType.CONTROL_WORD in token_types
        assert TokenType.TEXT in token_types

    def test_tokenize_convenience_function(self):
        """tokenize_rtf convenience function."""
        tokens = tokenize_rtf(b"test")
        assert len(tokens) >= 1
        assert tokens[0].type == TokenType.TEXT

    def test_large_plain_text_tokenization_stays_bounded(self):
        """Large unformatted payloads should tokenize without per-byte backtracking."""
        payload = b"A" * (512 * 1024)
        started = time.perf_counter()
        tokens = tokenize_rtf(payload)
        elapsed = time.perf_counter() - started

        assert tokens[0].type == TokenType.TEXT
        assert tokens[0].value == "A" * (512 * 1024)
        assert elapsed < 1.0
