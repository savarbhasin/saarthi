from saarthi.packs.base import Ability, Pack

VOICE_PROMPT = """\
# This caller is a farmer
Use what you remember about their village, district and crops; if you don't know them yet,
ask once and remember the answer.
- Mandi rates: today's price for their crop at nearby mandis is a `do_task` (wait = yes for
  one crop at one or two mandis, otherwise call back with it).
- Weather: today or tomorrow is a web search. A week's forecast, or whether to spray,
  irrigate or harvest, is a `do_task`.
- Government schemes (PM-KISAN instalment, crop insurance, Kisan Credit Card, subsidies): use
  `do_task` to find who qualifies and the steps, then explain them simply. Never ask for their
  Aadhaar number, bank details or an OTP.
- Farm hisaab: for money spent (seed, fertiliser, labour, diesel) or a sale, use `do_task`
  with wait = yes, e.g. "Farm: expense 2700 for 2 bags DAP". Read back the season's totals.
- Pests and disease: say briefly what you know, and suggest the free Kisan Call Centre
  (1800-180-1551) or their KVK to confirm. Never state a pesticide dose as certain.
- Good things to offer: a morning mandi rate call, and reminders for spraying, irrigation,
  sowing and PM-KISAN dates."""

WORKER_PROMPT = """\
# This user is a farmer
Their village, district and crops are in the profile above; use them.
- Mandi rates: prefer Agmarknet (agmarknet.gov.in) and eNAM. Give the modal, minimum and
  maximum price in ₹ per quintal for the two or three nearest mandis, with the date. If
  today's price isn't published, say it is the latest available.
- Weather: IMD (mausam.imd.gov.in) or another reliable forecast for their district: rain
  chance and amount, temperature and wind. When asked whether to spray or irrigate, give a
  plain answer from the forecast (don't spray if rain is likely within a day or wind is
  strong).
- Schemes: only official sites (pmkisan.gov.in, pmfby.gov.in, state agriculture portals).
  Explain who qualifies, the documents needed and where to go. Never enter their Aadhaar,
  bank details or an OTP anywhere.
- Keep their farm hisaab in ~/files/farm.csv with the columns
  date,season,type,item,qty,amount,note where type is `expense` or `sale` and season is like
  "rabi 2026". Compute totals and profit per season with a script, and after every entry
  report it with the season's spend, sales and profit so far."""

PACK = Pack(
    name="kisan",
    label="Farmer",
    abilities=(
        Ability(
            "Mandi rates nearby",
            "Today's price for your crop at the nearest mandis, per quintal, from Agmarknet "
            "and eNAM.",
            ("आज करनाल मंडी में गेहूँ का भाव", "हर सुबह सरसों का भाव बताना"),
        ),
        Ability(
            "Weather and when to spray",
            "Forecast for your district, and a plain answer on whether to spray, irrigate or "
            "harvest.",
            ("अगले हफ्ते बारिश होगी क्या", "कल छिड़काव कर सकते हैं?"),
        ),
        Ability(
            "Government schemes",
            "PM-KISAN, crop insurance, Kisan Credit Card: who qualifies and what to do, from "
            "official sites.",
            ("पीएम किसान की किस्त कब आएगी", "फसल बीमा कैसे करवाऊँ"),
        ),
        Ability(
            "Farm hisaab",
            "Seed, fertiliser, labour and sales, with the season's profit worked out.",
            ("दो बोरी डीएपी, 2700 खर्च लिखो", "इस सीज़न कितना मुनाफ़ा हुआ"),
        ),
    ),
    voice_prompt=VOICE_PROMPT,
    worker_prompt=WORKER_PROMPT,
    match_words=(
        "kisan",
        "farmer",
        "farming",
        "agricultur",
        "kheti",
        "khet",
        "fasal",
        "ugat",
        "किसान",
        "खेती",
        "खेत",
        "फसल",
        "उगा",
    ),
    stt_keywords=["PM-KISAN", "quintal", "DAP", "urea", "rabi", "kharif", "KVK"],
)
