from saarthi.voice.agents.base import AgentSpec
from saarthi.voice.context import MESSENGER_CONTEXT_KEYS
from saarthi.voice.tools import MESSENGER_TOOLS

MESSENGER = AgentSpec(
    name="saarthi-messenger",
    prompt_file="messenger.md",
    welcome_message="{{greeting}}",
    tools=MESSENGER_TOOLS,
    stt_keywords=["Saarthi", "UPI", "PhonePe", "Paytm", "GPay", "udhaar", "hisaab"],
    stt_context=(
        "An AI assistant phoning someone on behalf of a person they know, to pass on a message, "
        "ask a question or remind them of something. People speak Hindi, Hinglish or English."
    ),
    hangup_after_silence=10,
    max_call_seconds=240,
    context_keys=MESSENGER_CONTEXT_KEYS,
)
