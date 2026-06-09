from app.providers.whatsapp.factory import get_whatsapp_provider
from app.providers.whatsapp.waha import WahaWhatsAppProvider


def test_factory_returns_waha_by_default(monkeypatch):
    from app.providers.whatsapp import factory

    monkeypatch.setattr(factory.settings, "WHATSAPP_PROVIDER", "waha")
    provider = get_whatsapp_provider()

    assert isinstance(provider, WahaWhatsAppProvider)


def test_factory_supports_case_insensitive_provider_name(monkeypatch):
    from app.providers.whatsapp import factory

    monkeypatch.setattr(factory.settings, "WHATSAPP_PROVIDER", "WAHA")
    provider = get_whatsapp_provider()

    assert isinstance(provider, WahaWhatsAppProvider)


def test_factory_raises_for_unsupported_provider(monkeypatch):
    from app.providers.whatsapp import factory

    monkeypatch.setattr(factory.settings, "WHATSAPP_PROVIDER", "unknown")

    try:
        get_whatsapp_provider()
        assert False, "Expected RuntimeError for unsupported provider"
    except RuntimeError as exc:
        assert "Unsupported WhatsApp provider" in str(exc)
        assert "waha" in str(exc)
