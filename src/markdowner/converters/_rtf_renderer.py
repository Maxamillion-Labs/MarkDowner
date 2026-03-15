# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""RTF renderer - converts IR to Markdown."""

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


class RtfRenderer:
    """Renders RTF IR to Markdown."""

    def __init__(self, doc: Document):
        self.doc = doc
        self._output: list[str] = []
        self._blank_lines = 0

    def render(self) -> str:
        """Render document to Markdown string."""
        for block in self.doc.blocks:
            self._render_block(block)

        while self._output and self._output[-1] == "":
            self._output.pop()

        return "\n".join(self._output)

    def _render_block(self, block: Paragraph | ListBlock) -> None:
        """Render a block node."""
        if isinstance(block, Paragraph):
            self._render_paragraph(block)
        elif isinstance(block, ListBlock):
            self._render_list(block)

    def _render_paragraph(self, para: Paragraph) -> None:
        """Render a paragraph to Markdown."""
        if not para.inlines:
            return

        self._emit_blank_line()

        text = self._render_inlines(para.inlines)
        if para.is_heading and para.heading_level:
            prefix = "#" * para.heading_level + " "
            text = prefix + text
        self._output.append(text)

    def _render_list(self, lst: ListBlock) -> None:
        """Render a list to Markdown."""
        self._emit_blank_line()
        for items in lst.items:
            text = self._render_inlines(items)
            self._output.append(f"- {text}")

    def _render_inlines(self, inlines: list[InlineNode]) -> str:
        """Render inline elements to Markdown string."""
        result = []
        for inline in inlines:
            if isinstance(inline, TextInline):
                text = self._escape_markdown(inline.content)
                if inline.bold and inline.italic:
                    text = f"***{text}***"
                elif inline.bold:
                    text = f"**{text}**"
                elif inline.italic:
                    text = f"*{text}*"
                result.append(text)
            elif isinstance(inline, Emphasis):
                text = self._render_inlines(inline.children)
                if inline.bold and inline.italic:
                    result.append(f"***{text}***")
                elif inline.bold:
                    result.append(f"**{text}**")
                elif inline.italic:
                    result.append(f"*{text}*")
            elif isinstance(inline, LineBreak):
                result.append("  \n")
            elif isinstance(inline, Tab):
                result.append("    ")
            else:
                result.append(str(inline))
        return "".join(result)

    def _escape_markdown(self, text: str) -> str:
        """Escape minimal Markdown characters to preserve readability."""
        return text.replace("`", "\\`")

    def _emit_blank_line(self) -> None:
        """Emit a blank line, limiting to max 2 consecutive."""
        if self._blank_lines >= 2:
            return
        if self._output and self._output[-1] != "":
            self._output.append("")
            self._blank_lines += 1
        elif not self._output:
            pass
        else:
            self._blank_lines += 1


def render_to_markdown(doc: Document) -> str:
    """Convenience function to render RTF IR to Markdown."""
    return RtfRenderer(doc).render()
