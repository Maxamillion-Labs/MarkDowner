# SPDX-FileCopyrightText: 2024 MarkDowner Team
#
# SPDX-License-Identifier: MIT

"""RTF control word mappings."""

from enum import Enum
from typing import Callable, Dict, Optional


class ControlAction(Enum):
    """Action to take when encountering a control word."""
    NONE = "none"
    SET_BOLD = "set_bold"
    CLEAR_BOLD = "clear_bold"
    SET_ITALIC = "set_italic"
    CLEAR_ITALIC = "clear_italic"
    SET_UNDERLINE = "set_underline"
    CLEAR_UNDERLINE = "clear_underline"
    PARAGRAPH = "paragraph"
    LINE_BREAK = "line_break"
    TAB = "tab"
    SET_FONT = "set_font"
    DEST_SKIP = "dest_skip"
    UNICODE_CHAR = "unicode_char"
    SYMBOL_CHAR = "symbol_char"
    IGNORE = "ignore"
    HEADING = "heading"


CONTROL_WORD_MAP: Dict[str, ControlAction] = {
    "b": ControlAction.SET_BOLD,
    "b0": ControlAction.CLEAR_BOLD,
    "i": ControlAction.SET_ITALIC,
    "i0": ControlAction.CLEAR_ITALIC,
    "ul": ControlAction.SET_UNDERLINE,
    "ulnone": ControlAction.CLEAR_UNDERLINE,
    "par": ControlAction.PARAGRAPH,
    "line": ControlAction.LINE_BREAK,
    "tab": ControlAction.TAB,
    "u": ControlAction.UNICODE_CHAR,
    "cs": ControlAction.SET_BOLD,
    "cf": ControlAction.NONE,
    "fs": ControlAction.NONE,
    "f": ControlAction.SET_FONT,
    "colortbl": ControlAction.DEST_SKIP,
    "fonttbl": ControlAction.DEST_SKIP,
    "stylesheet": ControlAction.DEST_SKIP,
    "info": ControlAction.DEST_SKIP,
    "generator": ControlAction.DEST_SKIP,
    "author": ControlAction.DEST_SKIP,
    "title": ControlAction.DEST_SKIP,
    "subject": ControlAction.DEST_SKIP,
    "keywords": ControlAction.DEST_SKIP,
    "category": ControlAction.DEST_SKIP,
    "manager": ControlAction.DEST_SKIP,
    "company": ControlAction.DEST_SKIP,
    "operator": ControlAction.DEST_SKIP,
    "pict": ControlAction.DEST_SKIP,
    "object": ControlAction.DEST_SKIP,
    "shp": ControlAction.DEST_SKIP,
    "themedata": ControlAction.DEST_SKIP,
    "colorschememapping": ControlAction.DEST_SKIP,
    "xmlopenpkg": ControlAction.DEST_SKIP,
    "mhtml": ControlAction.DEST_SKIP,
    "htmltag": ControlAction.IGNORE,
    "*": ControlAction.DEST_SKIP,
    "pn": ControlAction.DEST_SKIP,
    "pntext": ControlAction.DEST_SKIP,
    "pnlvl": ControlAction.DEST_SKIP,
    "pntxtb": ControlAction.DEST_SKIP,
    "pntxta": ControlAction.DEST_SKIP,
}


def get_action(control_word: str) -> ControlAction:
    """Get the action for a control word."""
    return CONTROL_WORD_MAP.get(control_word, ControlAction.NONE)
