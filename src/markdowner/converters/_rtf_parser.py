# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""RTF parser - converts tokens to IR."""

from typing import List, Optional

from ._rtf_control_map import ControlAction, get_action
from ._rtf_ir import (
    Document,
    Emphasis,
    InlineNode,
    LineBreak,
    ListBlock,
    Paragraph,
    Tab,
    TextInline,
)
from ._rtf_lexer import RtfLexer, Token, TokenType


class RtfParser:
    """Parser for RTF tokens."""

    def __init__(self, content: bytes):
        self.lexer = RtfLexer(content)
        self.doc = Document()
        self._state_stack: List["RtfState"] = [RtfState()]
        self._dest_skip_depth = 0

    @property
    def _state(self) -> "RtfState":
        """Current state."""
        return self._state_stack[-1]

    def parse(self) -> Document:
        """Parse RTF content into IR."""
        for token in self.lexer:
            if token.type == TokenType.GROUP_START:
                self._state_stack.append(self._state.copy())
            elif token.type == TokenType.GROUP_END:
                if self._dest_skip_depth > 0 and len(self._state_stack) > 1:
                    self._dest_skip_depth -= 1
                if len(self._state_stack) > 1:
                    self._state_stack.pop()
                else:
                    self._finalize_paragraph()
            elif token.type == TokenType.CONTROL_WORD:
                self._handle_control_word(token)
            elif token.type == TokenType.CONTROL_SYMBOL:
                self._handle_control_symbol(token)
            elif token.type == TokenType.TEXT:
                self._handle_text(token)

        self._finalize_paragraph()
        return self.doc

    def _handle_control_word(self, token: Token) -> None:
        """Handle a control word token."""
        action = get_action(token.value)

        if self._dest_skip_depth > 0:
            return

        if action == ControlAction.DEST_SKIP:
            self._dest_skip_depth = 1
            return

        if action == ControlAction.IGNORE:
            return

        if action == ControlAction.SET_BOLD:
            self._state.bold = token.param != 0
        elif action == ControlAction.CLEAR_BOLD:
            self._state.bold = False
        elif action == ControlAction.SET_ITALIC:
            self._state.italic = token.param != 0
        elif action == ControlAction.CLEAR_ITALIC:
            self._state.italic = False
        elif action == ControlAction.SET_UNDERLINE:
            self._state.underline = token.param != 0
        elif action == ControlAction.CLEAR_UNDERLINE:
            self._state.underline = False
        elif action == ControlAction.PARAGRAPH:
            self._finalize_paragraph()
        elif action == ControlAction.LINE_BREAK:
            self._add_inline(LineBreak())
        elif action == ControlAction.TAB:
            self._add_inline(Tab())
        elif action == ControlAction.UNICODE_CHAR:
            if token.param is not None:
                char = chr(token.param)
                self._add_text(char)

    def _handle_control_symbol(self, token: Token) -> None:
        """Handle a control symbol token."""
        if self._dest_skip_depth > 0:
            return

        if token.value in ("{", "}"):
            return

        if token.value == "'":
            if token.param is not None:
                char = chr(token.param)
                self._add_text(char)
        else:
            self._add_text(token.value)

    def _handle_text(self, token: Token) -> None:
        """Handle a text token."""
        if self._dest_skip_depth > 0:
            return
        self._add_text(token.value)

    def _add_text(self, text: str) -> None:
        """Add text to current paragraph."""
        inline = TextInline(
            content=text,
            bold=self._state.bold,
            italic=self._state.italic,
            underline=self._state.underline,
        )
        self._state.current_paragraph.inlines.append(inline)

    def _add_inline(self, inline: InlineNode) -> None:
        """Add inline element to current paragraph."""
        self._state.current_paragraph.inlines.append(inline)

    def _finalize_paragraph(self) -> None:
        """Finalize current paragraph and add to document."""
        para = self._state.current_paragraph
        if para.inlines:
            para = self._detect_heading(para)
            self.doc.blocks.append(para)
        self._state.current_paragraph = Paragraph()

    def _detect_heading(self, para: Paragraph) -> Paragraph:
        """Detect if paragraph is a heading."""
        text = self._get_paragraph_text(para)
        if not text:
            return para
        if text.strip().startswith("#"):
            return para
        para.is_heading = False
        para.heading_level = None
        return para


    def _get_paragraph_text(self, para: Paragraph) -> str:
        """Get plain text from paragraph."""
        parts = []
        for inline in para.inlines:
            if isinstance(inline, TextInline):
                parts.append(inline.content)
        return "".join(parts)


class RtfState:
    """Parser state."""

    def __init__(self):
        self.bold = False
        self.italic = False
        self.underline = False
        self.current_paragraph = Paragraph()

    def copy(self) -> "RtfState":
        """Create a copy of state."""
        new_state = RtfState()
        new_state.bold = self.bold
        new_state.italic = self.italic
        new_state.underline = self.underline
        new_state.current_paragraph = self.current_paragraph
        return new_state


def parse_rtf(content: bytes) -> Document:
    """Convenience function to parse RTF content."""
    return RtfParser(content).parse()
