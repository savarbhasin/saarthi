from saarthi.packs.base import KHATA_WORKER, Ability, Pack

VOICE_PROMPT = """\
# This caller sells fruit and vegetables
Beyond everything else, you are their munshi.
- Their khata (who owes them money, who paid back) lives on their computer. Whenever they
  mention credit given ("शर्मा जी ने दो सौ उधार लिए"), a payment received, or ask who owes
  what, use `do_task` with wait = yes and put it plainly in the goal, e.g. "Khata: add udhaar
  200 for Sharma ji (5 kg mangoes)" or "Khata: how much does Sharma ji owe?". Read the result
  back to them, with the new balance.
  When someone new goes in the khata, ask once for their phone number (so Saarthi can remind
  them later) and put it in the goal.
- Good things to offer: the morning mandi rate for what they sell, phoning everyone who owes
  them to remind them to pay, and calling back with today's total."""

WORKER_PROMPT = f"""\
# This user sells fruit and vegetables
{KHATA_WORKER}
For mandi rates, prefer Agmarknet (agmarknet.gov.in) or other live sources and say which
market and date the price is for."""

PACK = Pack(
    name="phal_sabzi",
    label="Fruit & vegetable seller",
    abilities=(
        Ability(
            "Keeps your khata",
            "Tell Saarthi who took credit or paid back; it keeps the ledger and reads back the "
            "balance.",
            ("शर्मा जी ने दो सौ उधार लिए", "किस पर कितना उधार है"),
        ),
        Ability(
            "Collects dues by phone",
            "Calls everyone who owes you and tells them your UPI ID, now or every evening.",
            ("जिन पर उधार है सबको फ़ोन करो", "रोज़ रात 9 बजे बकाया वालों को फ़ोन करो"),
        ),
        Ability(
            "Mandi rates",
            "Today's price for what you sell, from Agmarknet, or a call every morning with it.",
            ("आज आज़ादपुर मंडी में आम का भाव", "हर सुबह 6 बजे टमाटर का भाव बताना"),
        ),
    ),
    voice_prompt=VOICE_PROMPT,
    worker_prompt=WORKER_PROMPT,
    match_words=(
        "phal",
        "sabzi",
        "sabji",
        "fruit",
        "vegetable",
        "thela",
        "mandi",
        "फल",
        "सब्ज",
        "ठेला",
        "ठेले",
        "मंडी",
    ),
    stt_keywords=["udhaar", "khata", "hisaab", "mandi", "Azadpur", "peti", "darjan", "tarbooz"],
)
