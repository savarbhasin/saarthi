from saarthi.packs.base import KHATA_WORKER, Pack

VOICE_PROMPT = """\
# This caller runs a kirana (general store)
Beyond everything else, you are their munshi and stock-keeper.
- Their customer khata lives on their computer. For credit given, a payment received, or who
  owes what, use `do_task` with wait = yes, e.g. "Khata: add udhaar 340 for Gupta ji (atta,
  oil)" or "Khata: who owes the most?". Read back the new balance.
  When someone new goes in the khata, ask once for their phone number (so Saarthi can remind
  them later) and put it in the goal.
- When something is running out or they want to order stock ("चीनी खत्म हो रही है, दस किलो
  मंगवानी है"), use `do_task` with wait = yes: "Order list: add sugar 10 kg". When they are
  ready to order, read the list back so they can give it to their supplier.
- Good things to offer: phoning everyone who owes them to remind them to pay, a morning
  reminder of what to order, and checking wholesale prices before they buy."""

WORKER_PROMPT = f"""\
# This user runs a kirana (general store)
{KHATA_WORKER}
Keep their order list in ~/files/order_list.csv with the columns item,qty,unit,supplier,added_on.
- Merge repeats of the same item by adding the quantities. Remove items when they say the
  stock arrived or the order was placed.
- When asked for the list, group it by supplier.
For wholesale prices, use public listings and say where and when each price is from."""

PACK = Pack(
    name="kirana",
    voice_prompt=VOICE_PROMPT,
    worker_prompt=WORKER_PROMPT,
    match_words=(
        "kirana",
        "kiryana",
        "parchun",
        "general store",
        "grocery",
        "provision",
        "किराना",
        "किराने",
        "परचून",
        "जनरल स्टोर",
    ),
    stt_keywords=["kirana", "parchun", "atta", "maida", "besan", "supplier"],
)
