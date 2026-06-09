from __future__ import annotations

from typing import Any


_SENSITIVE_KEYS = {
    "token",
    "secret",
    "password",
    "api_key",
    "hmac",
    "authorization",
}


def mask_phone(phone: str | None) -> str:
    if not phone:
        return "[empty]"
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) <= 4:
        return "*" * len(digits)
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


def mask_identifier(value: Any) -> str:
    text = str(value) if value is not None else ""
    if not text:
        return "[empty]"
    if len(text) <= 8:
        return "*" * len(text)
    return f"{text[:4]}...{text[-4:]}"


def sanitize_error_message(message: Any) -> str:
    text = str(message) if message is not None else ""
    lowered = text.lower()
    for marker in _SENSITIVE_KEYS:
        if marker in lowered:
            return "[redacted-error]"
    return text


def redact_field(key: str, value: Any) -> Any:
    key_lower = key.lower()
    if any(sensitive in key_lower for sensitive in _SENSITIVE_KEYS):
        return "[REDACTED]"
    if "phone" in key_lower:
        return mask_phone(str(value) if value is not None else None)
    if key_lower.endswith("_id") or key_lower in {"tenant", "session"}:
        return mask_identifier(value)
    return value
