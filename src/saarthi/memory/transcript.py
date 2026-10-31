import re

# Bolna transcripts are "assistant: ..." / "user: ..." turns, one per line, with long turns
# sometimes wrapping onto further lines.
TURN = re.compile(r"^(assistant|user)\s*:\s*", re.I)


def turns(transcript: str) -> list[tuple[str, str]]:
    parsed: list[tuple[str, str]] = []
    for line in transcript.splitlines():
        if not line.strip():
            continue
        if match := TURN.match(line):
            parsed.append((match[1].lower(), line[match.end() :].strip()))
        elif parsed:
            role, text = parsed[-1]
            parsed[-1] = (role, f"{text} {line.strip()}")
    return parsed


def for_memory(transcript: str) -> str:
    """The part of a call worth remembering about the caller.

    Saarthi's answers carry web results, prices and definitions that Supermemory would
    otherwise store as facts about the user. Keep everything the user said, plus Saarthi's
    questions so short answers ("Priya") keep their meaning ("what's your daughter's name?").
    """
    kept = [
        f"{role}: {text}"
        for role, text in turns(transcript)
        if role == "user" or text.rstrip().endswith(("?", "？"))
    ]
    has_user = any(line.startswith("user:") for line in kept)
    return "\n".join(kept) if has_user else ""
