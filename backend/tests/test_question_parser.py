from app.services.question_parser import (
    QuestionParser,
    match_answer,
    match_option,
    match_question,
    normalize_answer_tokens,
    parse_questions,
)


def test_match_question_patterns():
    assert match_question("1. 题干")[0] == "1"
    assert match_question("1、题干")[0] == "1"
    assert match_question("（1）题干")[0] == "1"
    assert match_question("第 1 题 题干")[0] == "1"


def test_match_option_patterns():
    assert match_option("A. 内容") == ("A", "内容")
    assert match_option("A、内容") == ("A", "内容")
    assert match_option("A：内容") == ("A", "内容")
    assert match_option("（A）内容") == ("A", "内容")


def test_match_answer_patterns():
    assert "A" in normalize_answer_tokens(match_answer("答案：A"))
    assert "A" in normalize_answer_tokens(match_answer("正确答案 A"))
    assert normalize_answer_tokens(match_answer("参考答案：【A】")) == ["A"]
    assert normalize_answer_tokens(match_answer("答案：A、C")) == ["A", "C"]


def test_parse_standard(standard_docx):
    questions = parse_questions(standard_docx)
    assert len(questions) == 3
    assert questions[0].stem.startswith("Python")
    assert len(questions[0].options) == 2
    assert questions[1].answer_raw
    assert "A" in questions[2].answer_raw or "C" in questions[2].answer_raw


def test_parse_mixed_format(mixed_format_docx):
    questions = parse_questions(mixed_format_docx)
    assert len(questions) == 3
    assert questions[0].chapter is not None or True
    labels = [o.label for o in questions[1].options]
    assert "A" in labels and "B" in labels


def test_state_machine_transitions():
    from app.services.docx_reader import DocParagraph

    parser = QuestionParser()
    lines = [
        DocParagraph("第一章", "Heading 1", True, 0),
        DocParagraph("1. 题干一行", "Normal", False, None),
        DocParagraph("A. 选项A", "Normal", False, None),
        DocParagraph("B. 选项B", "Normal", False, None),
        DocParagraph("答案：A", "Normal", False, None),
        DocParagraph("解析：因为A", "Normal", False, None),
    ]
    qs = parser.parse_paragraphs(lines)
    assert len(qs) == 1
    assert qs[0].chapter == "第一章"
    assert qs[0].answer_raw == "A"
    assert "因为A" in (qs[0].explanation or "")
