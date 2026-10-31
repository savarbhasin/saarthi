import type { MouseEvent } from "react";
import { motion } from "motion/react";
import { LayoutTextFlip } from "../ui/layout-text-flip";
import { Section } from "./Section";

// The same profiles and phrases as the web app's guide (src/saarthi/packs).
const PACKS = [
  {
    name: "किराना",
    label: "Kirana store",
    line: "Keeps the khata, writes the supplier's order list, and phones everyone who owes you.",
    says: ["गुप्ता जी ने 340 का सामान उधार लिया", "चीनी खत्म हो रही है, दस किलो लिख लो"],
  },
  {
    name: "किसान",
    label: "Farmer",
    line: "Mandi rates nearby, when to spray, which schemes you qualify for, and the season's hisaab.",
    says: ["आज करनाल मंडी में गेहूँ का भाव", "कल छिड़काव कर सकते हैं?"],
  },
  {
    name: "फल-सब्ज़ी",
    label: "Fruit & veg seller",
    line: "Today's mandi price every morning at six, and a call each evening to whoever hasn't paid.",
    says: ["हर सुबह 6 बजे टमाटर का भाव बताना", "किस पर कितना उधार है"],
  },
  {
    name: "ड्राइवर",
    label: "Driver / delivery",
    line: "Hands-free earnings log, fuel prices and routes, and a nudge before papers or EMI fall due.",
    says: ["आज ओला से बारह सौ, सीएनजी तीन सौ", "एयरपोर्ट जाने का रास्ता खाली है?"],
  },
  {
    name: "कारीगर",
    label: "Tradesperson",
    line: "Your bookings with reminders, itemised quotes from material prices, and calls to collect dues.",
    says: ["कल सुबह दस बजे वर्मा जी के यहाँ वायरिंग", "दस मीटर पाइप और चार नल का रेट निकालो"],
  },
  {
    name: "बुज़ुर्ग",
    label: "Elder care",
    line: "Medicine on time, BP and sugar readings, patient help with pension and bills, and OTP warnings.",
    says: ["रोज़ सुबह 8 बजे बीपी की दवाई याद दिलाना", "किसी ने ओटीपी माँगा है"],
  },
];

// After Aceternity UI's Card Spotlight: a soft saffron light follows the pointer across the card.
function track(event: MouseEvent<HTMLElement>) {
  const rect = event.currentTarget.getBoundingClientRect();
  event.currentTarget.style.setProperty("--x", `${event.clientX - rect.left}px`);
  event.currentTarget.style.setProperty("--y", `${event.clientY - rect.top}px`);
}

export function Work() {
  return (
    <Section id="work" className="border-t border-line bg-surface">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="max-w-4xl"
      >
        <h2 className="flex flex-wrap items-center gap-x-4 gap-y-2 text-4xl leading-[1.1] font-extrabold tracking-tight md:text-6xl">
          <span>Saarthi for</span>
          <LayoutTextFlip words={["kirana stores", "farmers", "sabzi sellers", "drivers", "electricians", "our elders"]} />
        </h2>
        <p className="mt-5 max-w-2xl text-lg leading-relaxed text-muted">
          Tell Saarthi what you do, and it picks up the know-how for your trade on top of everything else it does.
        </p>
      </motion.div>

      <div className="mt-14 grid gap-px border border-line bg-line md:grid-cols-2 lg:grid-cols-3">
        {PACKS.map((pack, i) => (
          <motion.article
            key={pack.label}
            onMouseMove={track}
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true, margin: "-40px" }}
            transition={{ delay: (i % 3) * 0.1 }}
            className="group relative flex flex-col overflow-hidden bg-surface p-6 md:p-7"
          >
            <div className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100 [background:radial-gradient(360px_circle_at_var(--x)_var(--y),var(--accent-soft),transparent_70%)]" />
            <div className="relative flex items-baseline justify-between gap-3">
              <h3 className="text-3xl font-extrabold whitespace-nowrap">{pack.name}</h3>
              <span className="text-right font-mono text-xs font-semibold tracking-wider text-muted uppercase">{pack.label}</span>
            </div>
            <p className="relative mt-3 leading-relaxed text-muted">{pack.line}</p>
            <ul className="relative mt-auto grid gap-1.5 pt-6">
              {pack.says.map((say) => (
                <li key={say} className="bg-canvas px-3 py-2 text-[15px] transition-colors group-hover:bg-surface">
                  <span className="font-bold text-accent">“</span>
                  {say}
                  <span className="font-bold text-accent">”</span>
                </li>
              ))}
            </ul>
          </motion.article>
        ))}
      </div>
    </Section>
  );
}
