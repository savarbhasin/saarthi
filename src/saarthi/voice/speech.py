import re

# Text-to-speech reads every character, so markdown ("**", "#", "|") and links come out as
# noise. The worker is asked for plain spoken text; this is the safety net.
_LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")
_URL = re.compile(r"https?://\S+|www\.\S+")
_LINE_MARKERS = re.compile(r"^\s*(?:#{1,6}\s*|[-*•>]\s+|\d+[.)]\s+)", re.M)
_SYMBOLS = re.compile(r"[*_`#|~]+")
_SPACES = re.compile(r"\s+")


def speakable(text: str) -> str:
    text = _LINK.sub(r"\1", text)
    text = _URL.sub("", text)
    text = _LINE_MARKERS.sub("", text)
    text = _SYMBOLS.sub(" ", text)
    lines = [line.strip(" :-") for line in text.splitlines()]
    # Each list item or line becomes its own sentence instead of running into the next.
    joined = " ".join(_end_sentence(line) for line in lines if line)
    return _SPACES.sub(" ", joined).strip()


def _end_sentence(line: str) -> str:
    if line[-1] in ".!?।,;":
        return line
    return line + ("।" if _is_indic(line) else ".")


def _is_indic(line: str) -> bool:
    return any("ऀ" <= ch <= "෿" for ch in line)
