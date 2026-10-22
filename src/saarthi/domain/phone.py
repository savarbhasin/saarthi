import phonenumbers

from saarthi.config import get_settings


class InvalidPhone(ValueError):
    pass


def normalize_phone(raw: str, region: str | None = None) -> str:
    region = region or get_settings().default_region
    try:
        parsed = phonenumbers.parse(raw.strip(), region)
    except phonenumbers.NumberParseException as exc:
        raise InvalidPhone(raw) from exc
    if not phonenumbers.is_valid_number(parsed):
        raise InvalidPhone(raw)
    return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
