from app.providers.whatsapp.factory import get_whatsapp_provider
from app.providers.whatsapp.waha import WahaWhatsAppProvider
from app.providers.whatsapp.evolution import EvolutionWhatsAppProvider


def test_factory_returns_waha_by_default(monkeypatch):
    from app.providers.whatsapp import factory

    monkeypatch.setattr(factory.settings, "WHATSAPP_PROVIDER", "waha")
    provider = get_whatsapp_provider()

    assert isinstance(provider, WahaWhatsAppProvider)


def test_factory_returns_evolution_when_configured(monkeypatch):
    from app.providers.whatsapp import factory

    monkeypatch.setattr(factory.settings, "WHATSAPP_PROVIDER", "evolution")
    provider = get_whatsapp_provider()

    assert isinstance(provider, EvolutionWhatsAppProvider)


def test_factory_supports_case_insensitive_provider_name(monkeypatch):
    from app.providers.whatsapp import factory

    monkeypatch.setattr(factory.settings, "WHATSAPP_PROVIDER", "WAHA")
    provider = get_whatsapp_provider()

    assert isinstance(provider, WahaWhatsAppProvider)


def test_factory_supports_case_insensitive_evolution(monkeypatch):
    from app.providers.whatsapp import factory

    monkeypatch.setattr(factory.settings, "WHATSAPP_PROVIDER", "EVOLUTION")
    provider = get_whatsapp_provider()

    assert isinstance(provider, EvolutionWhatsAppProvider)


def test_factory_raises_for_unsupported_provider(monkeypatch):
    from app.providers.whatsapp import factory

    monkeypatch.setattr(factory.settings, "WHATSAPP_PROVIDER", "unknown")

    try:
        get_whatsapp_provider()
        assert False, "Expected RuntimeError for unsupported provider"
    except RuntimeError as exc:
        assert "Unsupported WhatsApp provider" in str(exc)
        assert "waha" in str(exc)
        assert "evolution" in str(exc)


def test_factory_error_lists_all_supported_providers(monkeypatch):
    from app.providers.whatsapp import factory

    monkeypatch.setattr(factory.settings, "WHATSAPP_PROVIDER", "invalid")

    try:
        get_whatsapp_provider()
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        error_msg = str(exc)
        # Ensure all providers are listed in error message
        assert "evolution" in error_msg.lower()
        assert "waha" in error_msg.lower()
