from dataclasses import dataclass

SESSION_PARAM = {
    "session": {
        "type": "string",
        "description": "The call session token from your instructions. Always pass it exactly.",
    }
}


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    properties: dict[str, dict]
    # Spoken while the tool runs. Bolna falls back to an English line when this is unset.
    pre_call_message: str = "एक सेकंड जी।"
    method: str = "POST"
    needs_session: bool = True

    @property
    def path(self) -> str:
        return f"/tools/{self.name}"

    def all_properties(self) -> dict[str, dict]:
        return {**SESSION_PARAM, **self.properties} if self.needs_session else self.properties


def to_bolna_api_tools(specs: list[ToolSpec], base_url: str, secret: str) -> dict:
    # Bolna fills `param` with Python %-formatting, which raises on a missing key, so every
    # property is marked required and tools treat "" as "not provided". Bolna also overwrites
    # params that share a name with a call context variable (see voice.context.CONTEXT_KEYS),
    # so only `session` may reuse one.
    tools, params = [], {}
    for spec in specs:
        properties = spec.all_properties()
        tool = {
            "name": spec.name,
            "description": spec.description,
            "key": "custom_task",
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": list(properties),
            },
        }
        params[spec.name] = {
            "method": spec.method,
            "url": f"{base_url.rstrip('/')}{spec.path}",
            "api_token": secret,
            "param": {name: f"%({name})s" for name in properties},
        }
        # Bolna stores this on both the tool and its params; set both so it is spoken.
        tool["pre_call_message"] = spec.pre_call_message
        params[spec.name]["pre_call_message"] = spec.pre_call_message
        tools.append(tool)
    return {"tools": tools, "tools_params": params}


def _text(description: str) -> dict:
    return {"type": "string", "description": description}


REPEAT = {
    "type": "string",
    "enum": ["none", "daily", "weekly"],
    "description": "Whether it repeats. 'none' for a one-off.",
}

ONBOARD_USER = ToolSpec(
    name="onboard_user",
    description=(
        "Register a new caller once you know their name, what work they do, and whether they "
        "agree that Saarthi can remember their information. Call only for new callers."
    ),
    pre_call_message="ठीक है जी, एक सेकंड।",
    properties={
        "caller_name": _text(
            "The name the caller told you, e.g. 'रमेश' or 'Savar'. If they spelled it letter "
            "by letter, join the letters into the name."
        ),
        "caller_work": _text(
            "What the caller does for a living, in their words, e.g. 'फल बेचता हूँ', "
            "'student', 'software engineer'. Empty string if they did not say."
        ),
        "caller_upi_id": _text(
            "Caller's UPI ID in English letters, lowercase, no spaces, like 'ramesh@okaxis'. "
            "Empty string if they did not give one."
        ),
        "caller_language": _text(
            "Code of the language the caller is speaking to you in: hi, en, bn, ta, te, mr, "
            "gu, kn, pa, ml."
        ),
        "consent": {
            "type": "string",
            "enum": ["yes", "no"],
            "description": "Whether the caller agreed that Saarthi may remember their details.",
        },
    },
)

DO_TASK = ToolSpec(
    name="do_task",
    description=(
        "Hand any real piece of work to your own computer, which has a web browser, files and "
        "code: looking things up on live websites, comparing prices, checking train or bus "
        "times, reading or filling forms, writing documents, calculations, research, anything "
        "multi-step. It works in the background. Either the caller holds (wait='yes', then "
        "wait_for_task) or Saarthi calls them back with the result. Give run_at to do it later "
        "(and repeat to do it regularly)."
    ),
    pre_call_message="ठीक है, मैं इस पर काम शुरू करता हूँ।",
    properties={
        "goal": _text(
            "The complete task in English, with every detail the caller gave (places, dates, "
            "budget, preferences), so it can be done without asking them again."
        ),
        "run_at": _text(
            "When to do it, as 'YYYY-MM-DD HH:MM' in Indian time. Empty string to start now."
        ),
        "repeat": REPEAT,
        "wait": {
            "type": "string",
            "enum": ["yes", "no"],
            "description": (
                "'yes' if the caller wants to hold on the line for the answer (then call "
                "wait_for_task), 'no' to call them back when it is done."
            ),
        },
    },
)

WAIT_FOR_TASK = ToolSpec(
    name="wait_for_task",
    description=(
        "Wait a few seconds for a task the caller is holding for. Returns the result when it "
        "is done, or 'still_working'; if still working, say one short line and call it again."
    ),
    pre_call_message="बस एक पल…",
    properties={"task": _text("The task id do_task gave you. Empty string for the latest.")},
)

TASK_STATUS = ToolSpec(
    name="task_status",
    description="Check on the caller's recent tasks: which are still running and what came back.",
    pre_call_message="एक सेकंड, देखता हूँ।",
    properties={},
)

TASK_DETAILS = ToolSpec(
    name="task_details",
    description=(
        "Get the full result of one of the caller's tasks, when they want more than the short "
        'summary ("aur batao", "tell me more", a number or name from it).'
    ),
    pre_call_message="एक सेकंड, देखता हूँ।",
    properties={"task": _text("The task id from their recent tasks. Empty string for the latest.")},
)

RECORD_OUTCOME = ToolSpec(
    name="record_outcome",
    description="Record how the call went, once, just before you say goodbye.",
    pre_call_message="ठीक है जी।",
    properties={
        "outcome": {
            "type": "string",
            "enum": [
                "agreed",
                "declined",
                "message_passed",
                "already_done",
                "disputed",
                "do_not_call",
                "call_later",
                "wrong_person",
                "other",
            ],
            "description": "What they said, in one word.",
        },
        "note": _text(
            "One short sentence for the person you are calling for, in the language given as "
            "their language, in its own script: what was said, with any date or amount they "
            "promised and any message for them, e.g. 'कल शाम सात बजे आ जाएँगे' or "
            "'शुक्रवार तक दो सौ रुपये भेज देंगे'."
        ),
    },
)

REMEMBER = ToolSpec(
    name="remember",
    description=(
        "Save something the caller wants you to remember about them for the future "
        "(preferences, people, important dates). Use when they say 'याद रखना' or share "
        "something clearly worth keeping."
    ),
    pre_call_message="याद रख लिया।",
    properties={"fact": _text("The fact to remember, as a short sentence in English.")},
)

RECALL = ToolSpec(
    name="recall",
    description="Search what you remember about the caller from past calls.",
    pre_call_message="एक सेकंड, याद करता हूँ।",
    properties={"query": _text("What to look for, in English, e.g. 'daughter's school'.")},
)

FORGET = ToolSpec(
    name="forget",
    description="Forget something when the caller asks you to ('ये भूल जाओ').",
    pre_call_message="ठीक है।",
    properties={"what": _text("What to forget, in English.")},
)

SET_REMINDER = ToolSpec(
    name="set_reminder",
    description=("Call the caller at a set time to remind them of something, once or regularly."),
    pre_call_message="ठीक है, लिख लेता हूँ।",
    properties={
        "message": _text("What to remind them about, in the language they speak to you in."),
        "remind_at": _text("When, as 'YYYY-MM-DD HH:MM' in Indian time."),
        "repeat": REPEAT,
    },
)

LIST_SCHEDULE = ToolSpec(
    name="list_schedule",
    description="List the caller's upcoming reminders and scheduled tasks.",
    pre_call_message="एक सेकंड जी।",
    properties={},
)

MAIN_TOOLS = [
    ONBOARD_USER,
    DO_TASK,
    WAIT_FOR_TASK,
    TASK_STATUS,
    TASK_DETAILS,
    REMEMBER,
    RECALL,
    FORGET,
    SET_REMINDER,
    LIST_SCHEDULE,
]

MESSENGER_TOOLS = [RECORD_OUTCOME]
