from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


QuestionType = Literal["single_choice", "multiple_choice", "judgment", "unknown"]
PracticeMode = Literal["sequence", "random", "wrong", "favorite", "unanswered"]


class OptionSchema(BaseModel):
    label: str
    content: str
    sort_order: int = 0


class ParsedQuestionSchema(BaseModel):
    chapter: Optional[str] = None
    question_type: QuestionType = "unknown"
    stem: str
    options: list[OptionSchema] = Field(default_factory=list)
    answer: Optional[list[str]] = None
    explanation: Optional[str] = None
    source_order: int = 0
    needs_review: bool = False
    issues: list[str] = Field(default_factory=list)
    content_hash: Optional[str] = None
    duplicate_of: Optional[int] = None


class ImportPreviewResponse(BaseModel):
    id: int
    bank_name: str
    status: str
    source_filename: Optional[str] = None
    question_count: int
    error_count: int
    questions: list[ParsedQuestionSchema]
    created_at: datetime
    bank_id: Optional[int] = None


class ImportConfirmRequest(BaseModel):
    questions: Optional[list[ParsedQuestionSchema]] = None


class QuestionBankSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    question_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuestionOut(BaseModel):
    id: int
    bank_id: int
    chapter: Optional[str] = None
    question_type: QuestionType
    stem: str
    options: list[OptionSchema] = Field(default_factory=list)
    answer: Optional[list[str]] = None
    explanation: Optional[str] = None
    source_order: int = 0
    needs_review: bool = False
    is_favorite: bool = False
    is_wrong: bool = False
    answered: bool = False

    model_config = {"from_attributes": True}


class AnswerRequest(BaseModel):
    answer: list[str]


class AnswerResponse(BaseModel):
    is_correct: bool
    correct_answer: Optional[list[str]] = None
    explanation: Optional[str] = None


class FavoriteRequest(BaseModel):
    is_favorite: bool = True


class BackupImportResult(BaseModel):
    banks: int
    questions: int
    message: str
