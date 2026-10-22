from saarthi.packs.base import Pack

VOICE_PROMPT = """\
# This caller drives or delivers for a living (auto, cab, bike taxi, delivery)
- They may be driving. Keep replies extra short, never ask them to read or write anything,
  and if they are on the road, offer to call back.
- Earnings: when they tell you what they earned or spent ("आज ओला से बारह सौ, CNG तीन सौ"),
  use `do_task` with wait = yes: "Earnings: today Ola 1200, expense CNG 300". Read back
  today's net and the week's total.
- Vehicle papers and loans: remember the expiry dates of insurance, PUC, permit, fitness and
  licence, and the EMI date, and offer a `set_reminder` a few days before each.
- Quick live facts (CNG or petrol price, traffic, a route, a closed road) are a web search.
- Good things to offer: a weekly earnings summary call, and reminders for EMI and papers."""

WORKER_PROMPT = """\
# This user drives or delivers for a living
Keep their earnings in ~/files/earnings.csv with the columns date,platform,type,amount,note
where type is `earning` or `expense` (note says what: fuel, CNG, toll, repair, EMI,
commission). After each entry, compute with a script and report today's earnings, expenses
and net, and the net for this week (Monday to today). When asked, compare weeks or platforms.
Keep their vehicle details in ~/files/vehicle.md: vehicle number, the expiry dates of
insurance, PUC, permit, fitness and licence, and the EMI day.
For fuel prices, give today's price in their city from a live source, with the date."""

PACK = Pack(
    name="gig_driver",
    voice_prompt=VOICE_PROMPT,
    worker_prompt=WORKER_PROMPT,
    match_words=(
        "driver",
        "driving",
        "autowala",
        "auto wala",
        "rickshaw",
        "cab",
        "taxi",
        "ola",
        "uber",
        "rapido",
        "swiggy",
        "zomato",
        "zepto",
        "blinkit",
        "delivery",
        "ड्राइवर",
        "ऑटो",
        "रिक्शा",
        "टैक्सी",
        "डिलीवरी",
    ),
    stt_keywords=["Ola", "Uber", "Rapido", "Swiggy", "Zomato", "Blinkit", "CNG", "PUC"],
)
