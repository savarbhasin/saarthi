from saarthi.packs.base import KHATA_WORKER, Ability, Pack

VOICE_PROMPT = """\
# This caller is a tradesperson (plumber, electrician, carpenter, tailor, mechanic and similar)
- Bookings: when they mention a job ("कल सुबह दस बजे शर्मा जी के यहाँ नल ठीक करना है"), use
  `do_task` with wait = yes: "Jobs: add tomorrow 10:00, Sharma ji, Sector 15, fix tap", then
  offer a `set_reminder` an hour before. For "what's on tomorrow?" use `do_task` with
  wait = yes: "Jobs: list tomorrow".
- Customer dues: for work done on credit or a payment received, use `do_task` with
  wait = yes, e.g. "Khata: add udhaar 1500 for Verma ji (wiring)". Read back the new balance.
  When someone new goes in the khata, ask once for their phone number (so Saarthi can remind
  them later) and put it in the goal.
- Quotes: when they need material prices to quote a customer (pipe, wire, fittings, fabric),
  use `do_task` and give an itemised estimate, adding their labour if they tell you their
  rate.
- Good things to offer: a morning call with the day's jobs, and phoning everyone who owes
  them to remind them to pay."""

WORKER_PROMPT = f"""\
# This user is a tradesperson (plumber, electrician, carpenter, tailor, mechanic and similar)
Keep their jobs in ~/files/jobs.csv with the columns date,time,customer,place,work,quote,status
where status is `booked`, `done` or `cancelled`. Keep it sorted by date and time.
- When listing, give time, customer, place and work for each booked job.
- Mark jobs done or cancelled when told. If a done job is unpaid and they say so, also add it
  to the khata as udhaar.
{KHATA_WORKER}
For material prices, check live listings and give a typical price range with sources. Build
estimates as an itemised list with a total."""

PACK = Pack(
    name="service_pro",
    label="Tradesperson",
    abilities=(
        Ability(
            "Bookings and reminders",
            "Keeps your jobs list and reminds you before each one.",
            ("कल सुबह दस बजे वर्मा जी के यहाँ वायरिंग", "कल का काम बताओ"),
        ),
        Ability(
            "Customer dues",
            "Work done on credit and payments received, and calls to collect what's owed.",
            ("वर्मा जी ने 1500 देने हैं", "जिन पर पैसे बाकी हैं उन्हें फ़ोन करो"),
        ),
        Ability(
            "Quotes",
            "Looks up material prices and gives you an itemised estimate.",
            ("दस मीटर पाइप और चार नल का रेट निकालो",),
        ),
    ),
    voice_prompt=VOICE_PROMPT,
    worker_prompt=WORKER_PROMPT,
    match_words=(
        "plumb",
        "electrician",
        "bijli",
        "carpenter",
        "mistri",
        "tailor",
        "darzi",
        "mechanic",
        "painter",
        "technician",
        "repair",
        "प्लंबर",
        "इलेक्ट्रीशियन",
        "बिजली",
        "मिस्त्री",
        "दर्जी",
        "बढ़ई",
        "मैकेनिक",
        "पेंटर",
        "रिपेयर",
    ),
    stt_keywords=["plumber", "electrician", "wiring", "MCB", "fitting", "quotation"],
)
