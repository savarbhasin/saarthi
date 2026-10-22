from saarthi.packs import PACKS
from saarthi.voice.agents.base import AgentSpec
from saarthi.voice.context import CONTEXT_KEYS
from saarthi.voice.tools import MAIN_TOOLS

GENERAL_TERMS = ["Saarthi", "UPI", "PhonePe", "Paytm", "GPay", "WhatsApp", "IRCTC", "udhaar"]

MAIN = AgentSpec(
    name="saarthi-main",
    prompt_file="main.md",
    welcome_message="{{greeting}}",
    tools=MAIN_TOOLS,
    inbound=True,
    web_search=True,
    context_keys=CONTEXT_KEYS,
    stt_keywords=list(
        dict.fromkeys(GENERAL_TERMS + [w for p in PACKS.values() for w in p.stt_keywords])
    ),
    stt_context=(
        "Phone calls to a personal assistant in India. Callers speak Hindi or Hinglish and ask "
        "for help with tasks, information, reminders and their work: shops, farming, trades, "
        "driving and deliveries, health and medicines, and money owed to them."
    ),
)
