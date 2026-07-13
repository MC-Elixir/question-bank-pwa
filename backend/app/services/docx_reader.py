from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Union

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph


@dataclass
class DocParagraph:
    text: str
    style_name: str
    is_heading: bool
    outline_level: int | None = None


def _is_heading_style(style_name: str) -> bool:
    name = (style_name or "").lower()
    return name.startswith("heading") or name.startswith("标题")


def _outline_level(paragraph: Paragraph) -> int | None:
    try:
        style = paragraph.style
        if style is None:
            return None
        if style.type == WD_STYLE_TYPE.PARAGRAPH and hasattr(style, "base_style"):
            pass
        pPr = paragraph._element.pPr
        if pPr is not None and pPr.outlineLvl is not None:
            return int(pPr.outlineLvl.val)
        name = (style.name or "").lower()
        for i in range(1, 10):
            if f"heading {i}" in name or f"标题 {i}" in name or name == f"heading{i}":
                return i - 1
    except Exception:
        return None
    return None


def read_docx(source: Union[str, Path, BinaryIO]) -> list[DocParagraph]:
    """读取 Word 文档段落，保留样式信息供章节识别."""
    document = Document(source)
    result: list[DocParagraph] = []
    for para in document.paragraphs:
        text = (para.text or "").strip()
        if not text:
            continue
        style_name = para.style.name if para.style is not None else ""
        is_heading = _is_heading_style(style_name) or _outline_level(para) is not None
        result.append(
            DocParagraph(
                text=text,
                style_name=style_name or "",
                is_heading=is_heading,
                outline_level=_outline_level(para),
            )
        )
    return result


def read_docx_texts(source: Union[str, Path, BinaryIO]) -> list[str]:
    return [p.text for p in read_docx(source)]
