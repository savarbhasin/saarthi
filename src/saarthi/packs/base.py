from dataclasses import dataclass, field


# A profile for one kind of user: extra instructions for the voice agent (how to talk to them,
# what to offer, what to hand off) and for the sandbox worker (how to do their work).
@dataclass(frozen=True)
class Pack:
    name: str
    voice_prompt: str = ""
    worker_prompt: str = ""
    # Word starts in the caller's description of their work that select this pack.
    match_words: tuple[str, ...] = ()
    # Bolna takes one keyword list for every caller, so keep each pack's list short.
    stt_keywords: list[str] = field(default_factory=list)


GENERAL = Pack(name="general")

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
  user's UPI ID."""
