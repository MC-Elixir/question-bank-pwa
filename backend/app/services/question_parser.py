from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from .docx_reader import DocParagraph, read_docx


class ParseState(Enum):
    WAITING = auto()
    READING_QUESTION = auto()
    READING_OPTIONS = auto()
    READING_ANSWER = auto()
    READING_EXPLANATION = auto()


QUESTION_PATTERNS = [
    re.compile(r"^第\s*(\d+)\s*题[、.．:：\s]*(.*)$"),
    re.compile(r"^（\s*(\d+)\s*）[、.．:：\s]*(.*)$"),
    re.compile(r"^\(\s*(\d+)\s*\)[、.．:：\s]*(.*)$"),
    re.compile(r"^(\d+)\s*[.．、]\s*(.*)$"),
]

OPTION_PATTERNS = [
    re.compile(r"^（\s*([A-Ha-h])\s*）[、.．:：\s]*(.*)$"),
    re.compile(r"^\(\s*([A-Ha-h])\s*\)[、.．:：\s]*(.*)$"),
    re.compile(r"^([A-Ha-h])\s*[.．、:：]\s*(.*)$"),
]

ANSWER_PATTERNS = [
    re.compile(r"^(?:正确答案|参考答案|答案)\s*[:：]?\s*【\s*([A-Ha-h对错是否√×YyNn,，、/\s]+)\s*】\s*$"),
    re.compile(r"^(?:正确答案|参考答案|答案)\s*[:：]?\s*([A-Ha-h对错是否√×YyNn,，、/\s]+)\s*$"),
]

EXPLANATION_PATTERNS = [
    re.compile(r"^(?:答案解析|解析|说明)\s*[:：]\s*(.*)$"),
]

CHAPTER_PATTERNS = [
    re.compile(r"^第[一二三四五六七八九十百零〇\d]+\s*章.*$"),
    re.compile(r"^[一二三四五六七八九十]+[、.．]\s*.+$"),
]

JUDGMENT_TRUE = {"对", "正确", "是", "√", "Y", "y", "T", "t", "TRUE", "True", "true"}
JUDGMENT_FALSE = {"错", "错误", "否", "×", "X", "x", "N", "n", "F", "f", "FALSE", "False", "false"}


@dataclass
class RawOption:
    label: str
    content: str


@dataclass
class RawQuestion:
    chapter: Optional[str] = None
    stem_parts: list[str] = field(default_factory=list)
    options: list[RawOption] = field(default_factory=list)
    answer_raw: Optional[str] = None
    explanation_parts: list[str] = field(default_factory=list)
    source_order: int = 0
    merged_flag: bool = False

    @property
    def stem(self) -> str:
        return "\n".join(p for p in self.stem_parts if p).strip()

    @property
    def explanation(self) -> Optional[str]:
        text = "\n".join(p for p in self.explanation_parts if p).strip()
        return text or None


def match_question(text: str) -> Optional[tuple[str, str]]:
    for pattern in QUESTION_PATTERNS:
        m = pattern.match(text)
        if m:
            return m.group(1), (m.group(2) or "").strip()
    return None


def match_option(text: str) -> Optional[tuple[str, str]]:
    for pattern in OPTION_PATTERNS:
        m = pattern.match(text)
        if m:
            return m.group(1).upper(), (m.group(2) or "").strip()
    return None


def match_answer(text: str) -> Optional[str]:
    for pattern in ANSWER_PATTERNS:
        m = pattern.match(text)
        if m:
            return m.group(1).strip()
    return None


def match_explanation(text: str) -> Optional[str]:
    for pattern in EXPLANATION_PATTERNS:
        m = pattern.match(text)
        if m:
            return (m.group(1) or "").strip()
    return None


def is_chapter_line(para: DocParagraph) -> bool:
    if para.is_heading:
        return True
    for pattern in CHAPTER_PATTERNS:
        if pattern.match(para.text):
            return True
    return False


def normalize_answer_tokens(raw: str) -> list[str]:
    if not raw:
        return []
    cleaned = raw.replace("，", ",").replace("、", ",").replace("/", ",").replace(" ", "")
    parts = [p for p in re.split(r"[,]+", cleaned) if p]
    if not parts:
        parts = [cleaned]
    result: list[str] = []
    for part in parts:
        if part in JUDGMENT_TRUE:
            result.append("对")
        elif part in JUDGMENT_FALSE:
            result.append("错")
        elif re.fullmatch(r"[A-Ha-h]+", part) and len(part) > 1:
            # 答案：AC 或 ABC
            result.extend(ch.upper() for ch in part)
        elif re.fullmatch(r"[A-Ha-h]", part):
            result.append(part.upper())
        else:
            result.append(part)
    # 去重保序
    seen = set()
    ordered: list[str] = []
    for item in result:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def infer_question_type(options: list[RawOption], answer: Optional[list[str]]) -> str:
    labels = {o.label.upper() for o in options}
    if labels and labels.issubset({"对", "错", "A", "B"}) and (
        labels == {"对", "错"}
        or (
            len(options) == 2
            and any("对" in o.content or "正确" in o.content for o in options)
            and any("错" in o.content or "错误" in o.content for o in options)
        )
    ):
        return "judgment"
    if answer and all(a in JUDGMENT_TRUE or a in JUDGMENT_FALSE or a in {"对", "错"} for a in answer):
        if not options or labels.issubset({"对", "错", "A", "B"}):
            return "judgment"
    if answer and len(answer) > 1:
        return "multiple_choice"
    if options and len(options) >= 2:
        return "single_choice"
    if options:
        return "single_choice"
    return "unknown"


class QuestionParser:
    """基于状态机的题目解析器."""

    def __init__(self) -> None:
        self.state = ParseState.WAITING
        self.current_chapter: Optional[str] = None
        self.current: Optional[RawQuestion] = None
        self.questions: list[RawQuestion] = []
        self._order = 0

    def _start_question(self, stem_rest: str) -> None:
        if self.current is not None:
            self.questions.append(self.current)
        self._order += 1
        self.current = RawQuestion(
            chapter=self.current_chapter,
            source_order=self._order,
        )
        if stem_rest:
            self.current.stem_parts.append(stem_rest)
        self.state = ParseState.READING_QUESTION

    def _flush(self) -> None:
        if self.current is not None:
            self.questions.append(self.current)
            self.current = None
        self.state = ParseState.WAITING

    def feed(self, para: DocParagraph) -> None:
        text = para.text.strip()
        if not text:
            return

        if is_chapter_line(para) and match_question(text) is None:
            self.current_chapter = text
            return

        q_match = match_question(text)
        opt_match = match_option(text)
        ans_match = match_answer(text)
        exp_match = match_explanation(text)

        if q_match is not None:
            _, stem_rest = q_match
            # 若上一题尚未结束且新题号出现，正常切题
            if self.current is not None and self.state in {
                ParseState.READING_QUESTION,
                ParseState.READING_OPTIONS,
            }:
                # 可能是题干中误匹配，但按规则优先视为新题
                pass
            self._start_question(stem_rest)
            return

        if self.current is None:
            # 等待态遇到非题号内容：若像选项/答案则忽略，否则可能是无题号题干
            if opt_match or ans_match or exp_match:
                return
            self._start_question(text)
            self.current.merged_flag = True  # 无题号，标记待审
            return

        if ans_match is not None:
            self.current.answer_raw = ans_match
            self.state = ParseState.READING_ANSWER
            return

        if exp_match is not None:
            if exp_match:
                self.current.explanation_parts.append(exp_match)
            self.state = ParseState.READING_EXPLANATION
            return

        if opt_match is not None:
            label, content = opt_match
            self.current.options.append(RawOption(label=label, content=content))
            self.state = ParseState.READING_OPTIONS
            return

        # 续行
        if self.state == ParseState.READING_QUESTION:
            self.current.stem_parts.append(text)
        elif self.state == ParseState.READING_OPTIONS:
            if self.current.options:
                last = self.current.options[-1]
                last.content = f"{last.content}\n{text}".strip()
            else:
                self.current.stem_parts.append(text)
        elif self.state == ParseState.READING_ANSWER:
            # 答案行后的非解析内容并入解析
            self.current.explanation_parts.append(text)
            self.state = ParseState.READING_EXPLANATION
        elif self.state == ParseState.READING_EXPLANATION:
            self.current.explanation_parts.append(text)
        else:
            self.current.stem_parts.append(text)
            self.state = ParseState.READING_QUESTION

    def parse_paragraphs(self, paragraphs: list[DocParagraph]) -> list[RawQuestion]:
        self.state = ParseState.WAITING
        self.current_chapter = None
        self.current = None
        self.questions = []
        self._order = 0
        for para in paragraphs:
            self.feed(para)
        self._flush()
        return self.questions

    def parse_file(self, source) -> list[RawQuestion]:
        return self.parse_paragraphs(read_docx(source))


def parse_questions(source) -> list[RawQuestion]:
    return QuestionParser().parse_file(source)
