import re

from saarthi.packs import elder_care, gig_driver, kirana, kisan, phal_sabzi, service_pro
from saarthi.packs.base import GENERAL, Pack

# Ties go to the earlier pack: a farmer who mentions the mandi is a kisan, not a sabziwala.
PACKS: dict[str, Pack] = {
    p.name: p
    for p in (
        GENERAL,
        kisan.PACK,
        phal_sabzi.PACK,
        kirana.PACK,
        service_pro.PACK,
        gig_driver.PACK,
        elder_care.PACK,
    )
}

# A match word must start a word ("ola" matches "ola chalata", not "chocolate").
_WORD_START = r"(?<![\wऀ-ॿ])"


def pack_for(name: str | None) -> Pack:
    return PACKS.get(name or "", GENERAL)


def _score(pack: Pack, text: str) -> int:
    return sum(bool(re.search(_WORD_START + re.escape(w), text)) for w in pack.match_words)


def pick_pack(occupation: str | None) -> Pack:
    text = (occupation or "").lower()
    best = max(PACKS.values(), key=lambda p: _score(p, text))
    return best if _score(best, text) else GENERAL


__all__ = ["PACKS", "Pack", "pack_for", "pick_pack"]
