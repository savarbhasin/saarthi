from dataclasses import dataclass, field


# Something Saarthi can do, shown on the web app's guide with phrases to try.
@dataclass(frozen=True)
class Ability:
    title: str
    detail: str
    examples: tuple[str, ...] = ()


# A profile for one kind of user: extra instructions for the voice agent (how to talk to them,
# what to offer, what to hand off) and for the sandbox worker (how to do their work).
@dataclass(frozen=True)
class Pack:
    name: str
    label: str = ""
    voice_prompt: str = ""
    worker_prompt: str = ""
    # Word starts in the caller's description of their work that select this pack.
    match_words: tuple[str, ...] = ()
    # Bolna takes one keyword list for every caller, so keep each pack's list short.
    stt_keywords: list[str] = field(default_factory=list)
    # What this pack adds on top of EVERYONE, for the web app's guide.
    abilities: tuple[Ability, ...] = ()


# What every user gets, whatever their pack.
EVERYONE = (
    Ability(
        "Answers anything",
        "Ask a question and get a short answer on the call, with live facts looked up when needed.",
        ("pernicious का मतलब क्या है", "आज सोने का भाव क्या है"),
    ),
    Ability(
        "Does real work on its own computer",
        "Research, compare prices, check trains, read sites and fill forms. Hold on for the "
        "answer, or hang up and Saarthi calls you back.",
        ("दिल्ली से जयपुर की कल की ट्रेनें देखो", "Redmi Note 14 का सबसे सस्ता दाम ढूँढो"),
    ),
    Ability(
        "Reminders and routines",
        "Saarthi calls you at the time you ask, once or every day or week, and can run a job "
        "on a schedule.",
        ("कल सुबह 7 बजे दवाई याद दिलाना", "हर रविवार सुबह मौसम बताना"),
    ),
    Ability(
        "Calls people for you",
        "Passes on a message, asks a question or reminds someone, then tells you what they said.",
        ("मेरे भाई को फ़ोन करके बोलो मैं शाम को आऊँगा",),
    ),
    Ability(
        "Remembers you",
        "Your family, work and preferences, from every call. Ask it to remember or forget "
        "anything.",
        ("याद रखना मेरी बेटी का नाम प्रिया है", "मेरे बारे में क्या याद है"),
    ),
    Ability(
        "Speaks your language",
        "Hindi, English, Bengali, Tamil, Telugu, Marathi and more. Switch any time mid-call.",
        ("Can we talk in English?", "தமிழில் பேசலாமா?"),
    ),
)

GENERAL = Pack(name="general", label="General")

# Shared by every pack whose users give goods or work on credit.
KHATA_WORKER = """\
You keep their khata (credit ledger) in ~/files/khata.csv with the columns
date,person,type,amount,note where type is `udhaar` (they gave credit) or `payment` (someone
paid them back) and amount is in rupees. Create it if it does not exist.
- To add an entry, append a row. Match the person to an existing name even if spelled
  differently (Sharma ji / sharmaji / Sharma) and reuse that spelling.
- A person's balance is the sum of their udhaar minus the sum of their payments. Compute it
  with a script, never by guessing.
- After every change, report the entry you wrote and that person's new balance.
- For "who owes what", list everyone with a positive balance, largest first, and the total.
- Save phone numbers they give for people in the khata to ~/files/contacts.csv.
- To remind people of their dues, `request_calls` with everyone who has a positive balance
  and a number; the purpose says what they owe and what for, and that they can pay to the
  user's UPI ID if you know it (from what you know about them above)."""
