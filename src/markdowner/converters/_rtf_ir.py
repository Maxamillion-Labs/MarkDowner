# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""RTF Intermediate Representation (IR) dataclasses."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TextInline:
    """Text content with inline formatting."""
    content: str
    bold: bool = False
    italic: bool = False
    underline: bool = False


@dataclass
class Emphasis:
    """Inline emphasis container."""
    children: List["InlineNode"] = field(default_factory=list)
    bold: bool = False
    italic: bool = False


@dataclass
class LineBreak:
    """Line break marker."""
    pass


@dataclass
class Tab:
    """Tab marker."""
    pass


InlineNode = TextInline | Emphasis | LineBreak | Tab


@dataclass
class Paragraph:
    """Paragraph block."""
    inlines: List[InlineNode] = field(default_factory=list)
    is_heading: bool = False
    heading_level: Optional[int] = None


@dataclass
class ListBlock:
    """List/block element."""
    items: List[List[InlineNode]] = field(default_factory=list)


@dataclass
class Document:
    """Root document container."""
    blocks: List["BlockNode"] = field(default_factory=list)


BlockNode = Paragraph | ListBlock
