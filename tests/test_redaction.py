from app.core.redaction import (mask_identifier, mask_phone, redact_field,
                                sanitize_error_message)


def test_mask_phone_hides_all_but_last_four():
    assert mask_phone("5511999998888") == "*********8888"


def test_mask_identifier_preserves_edges_only():
    raw = "tenant-12345678-90ab-cdef-1234-567890abcdef"
    masked = mask_identifier(raw)
    assert masked.startswith("tena...")
    assert masked.endswith("cdef")
    assert raw not in masked


def test_redact_field_for_sensitive_keys():
    assert redact_field("api_key", "abc") == "[REDACTED]"
    assert redact_field("phone", "5511999998888") == "*********8888"


def test_sanitize_error_message_redacts_secret_markers():
    assert sanitize_error_message("provider token expired") == "[redacted-error]"
    assert sanitize_error_message("generic timeout") == "generic timeout"
