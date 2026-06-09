from app.core.config import get_settings
from app.providers.whatsapp.interface import WhatsAppProvider
from app.providers.whatsapp.waha import WahaWhatsAppProvider

settings = get_settings()

_SUPPORTED_PROVIDERS = {
    "waha": WahaWhatsAppProvider,
}


def get_whatsapp_provider() -> WhatsAppProvider:
    provider_key = (settings.WHATSAPP_PROVIDER or "waha").strip().lower()
    provider_cls = _SUPPORTED_PROVIDERS.get(provider_key)
    if provider_cls is None:
        supported = ", ".join(sorted(_SUPPORTED_PROVIDERS.keys()))
        raise RuntimeError(
            f"Unsupported WhatsApp provider '{provider_key}'. Supported providers: {supported}"
        )
    return provider_cls()
