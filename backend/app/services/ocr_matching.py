import re
from dataclasses import dataclass
from typing import Iterable, List, Optional


def normalize_text(value: str) -> str:
    if value is None:
        return ''
    value = value.upper()
    value = value.replace('\u00A0', ' ')
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_token(value: str) -> str:
    value = normalize_text(value)
    value = re.sub(r"[^A-Z0-9]", "", value)
    return value


def token_in_text(text: str, token: str) -> bool:
    if not token:
        return False
    normalized_text = normalize_token(text)
    normalized_token = normalize_token(token)
    if not normalized_token:
        return False
    return normalized_token in normalized_text


def find_first_token(text: str, candidates: Iterable[str]) -> Optional[str]:
    for candidate in candidates:
        if candidate and token_in_text(text, candidate):
            return candidate
    return None


_ORDER_NUMBER_RE = re.compile(r"\b(?:OT|WO|SO)?[- ]?\d{4,}\b", re.IGNORECASE)
_CODE_RE = re.compile(r"\b[A-Z0-9][A-Z0-9._-]{3,}\b", re.IGNORECASE)


def extract_order_like_tokens(text: str) -> List[str]:
    text = normalize_text(text)
    return list(dict.fromkeys([m.group(0).strip() for m in _ORDER_NUMBER_RE.finditer(text)]))


def extract_code_like_tokens(text: str) -> List[str]:
    text = normalize_text(text)
    tokens = [m.group(0).strip() for m in _CODE_RE.finditer(text)]
    tokens = [t for t in tokens if len(normalize_token(t)) >= 4]
    return list(dict.fromkeys(tokens))


@dataclass
class OcrValidationResult:
    raw_text: str
    avg_confidence: Optional[float]
    matched_order_number: Optional[str]
    matched_customer_name: Optional[str]
    matched_item_code: Optional[str]
    matched_work_order: Optional[str]

    def to_dict(self):
        return {
            'raw_text': self.raw_text,
            'avg_confidence': self.avg_confidence,
            'matched': {
                'order_number': self.matched_order_number,
                'customer_name': self.matched_customer_name,
                'item_code': self.matched_item_code,
                'work_order': self.matched_work_order,
            },
            'tokens': {
                'order_like': extract_order_like_tokens(self.raw_text),
                'code_like': extract_code_like_tokens(self.raw_text),
            }
        }
