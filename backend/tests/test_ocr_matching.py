from app.services.ocr_matching import normalize_token, token_in_text, extract_order_like_tokens


def test_normalize_token_removes_separators():
    assert normalize_token('AB-123') == 'AB123'
    assert normalize_token(' ab  123 ') == 'AB123'


def test_token_in_text_is_robust_to_separators():
    text = 'Orden: AB-123\nCliente: XYZ'
    assert token_in_text(text, 'AB123') is True
    assert token_in_text(text, 'AB-123') is True


def test_extract_order_like_tokens():
    text = 'OT 12345\nWO-7777\nSO 9999'
    tokens = extract_order_like_tokens(text)
    assert 'OT 12345' in tokens
