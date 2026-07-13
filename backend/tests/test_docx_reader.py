from app.services.docx_reader import read_docx, read_docx_texts


def test_read_standard_docx(standard_docx):
    paras = read_docx(standard_docx)
    assert len(paras) >= 10
    texts = [p.text for p in paras]
    assert any("Python 是一种解释型语言" in t for t in texts)
    assert any(p.is_heading or "第一章" in p.text for p in paras)


def test_read_docx_texts(mixed_format_docx):
    texts = read_docx_texts(mixed_format_docx)
    assert any("HTTP 默认端口" in t for t in texts)
