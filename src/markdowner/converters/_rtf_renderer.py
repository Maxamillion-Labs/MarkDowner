# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""RTF renderer - converts IR to Markdown."""

from typing import List

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

        output_text = "\n".join(self._output)
        output_text = self._remove_leading_noise(output_text)
        output_text = self._fix_mojibake(output_text)
        return output_text

    MOJIBAKE_MAP = {
        'â€‘': '‑',  # U+2011 non-breaking hyphen
    }

    def _fix_mojibake(self, text: str) -> str:
        """Fix common mojibake patterns from incorrect encoding."""
        result = text
        for wrong, right in self.MOJIBAKE_MAP.items():
            result = result.replace(wrong, right)
        return result

    def _remove_leading_noise(self, text: str) -> str:
        """Remove leading noise (punctuation-only lines) from output."""
        lines = text.split("\n")
        if not lines:
            return text
        
        start_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                continue
            if self._is_meaningful_line(stripped):
                start_idx = i
                break
        else:
            start_idx = 0
        
        return "\n".join(lines[start_idx:])

    def _is_meaningful_line(self, line: str) -> bool:
        """Check if a line is meaningful (not punctuation-only noise)."""
        if not line:
            return True
        if line.startswith("#"):
            return True
        if line.startswith("-"):
            return True
        if line[0].isdigit() and ". " in line:
            return True
        has_alphanumeric = any(c.isalnum() for c in line)
        return has_alphanumeric

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
        
        # Fix list item markers: ". " -> "- "
        text = self._fix_list_markers(text)
        
        if para.is_heading and para.heading_level:
            prefix = "#" * para.heading_level + " "
            text = prefix + text
        self._output.append(text)

    def _fix_list_markers(self, text: str) -> str:
        """Convert RTF list markers (. ) to markdown (- )."""
        # Pattern: line starting with ". " (with optional leading whitespace)
        import re
        return re.sub(r'^(\s*)\. ', r'\1- ', text, flags=re.MULTILINE)

    def _render_list(self, lst: ListBlock) -> None:
        """Render a list to Markdown."""
        self._emit_blank_line()
        for i, items in enumerate(lst.items):
            text = self._render_inlines(items)
            if lst.ordered:
                self._output.append(f"{i + 1}. {text}")
            else:
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
