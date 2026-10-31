import { motion } from "motion/react";
import { Heading, Section } from "./Section";

// Each chore beside what Saarthi does about it, so the two sides read row by row.
const ROWS: [string, string, string][] = [
  ["Call Sharma ji about ₹450", "4 min", "Called. Paid ₹450."],
  ["Call Gupta ji, no answer, call again", "6 min", "Called. Will pay on Sunday."],
  ["Find yesterday's page in the khata", "10 min", "Khata kept by voice, balances read back."],
  ["Ask around for tomorrow's tomato rate", "12 min", "Rate call every morning at 6:00."],
  ["Call Khan bhai, Verma ji, Rao ji, Mehta ji", "18 min", "Four more calls, every reply noted."],
  ["Remember to take BP medicine", "forgot", "Reminder call every day at 8:00."],
];

function Bar({ width, className }: { width: string; className: string }) {
  return (
    <div className="h-2 w-full bg-soft">
      <motion.div
        className={`h-full ${className}`}
        initial={{ width: 0 }}
        whileInView={{ width }}
        viewport={{ once: true }}
        transition={{ duration: 1.2, ease: "easeOut", delay: 0.2 }}
      />
    </div>
  );
}

export function Evening() {
  return (
    <Section className="border-t border-line bg-surface">
      <Heading
        title="Your evening, given back."
        lede="One sentence to Saarthi replaces an evening of calls and searching."
      />

      <div className="mt-12 border border-line">
        <div className="grid border-b border-line md:grid-cols-2">
          <div className="hidden bg-soft px-6 py-4 font-mono text-xs font-semibold tracking-wider text-muted uppercase md:block">
            Without Saarthi
          </div>
          <div className="bg-accent-soft px-6 py-4 md:border-l md:border-line">
            <div className="font-mono text-xs font-semibold tracking-wider text-accent uppercase">With Saarthi, you say</div>
            <div className="mt-1.5 text-lg font-semibold">“जिन पर उधार है सबको फ़ोन करो, और कल सुबह 6 बजे टमाटर का भाव बताना।”</div>
            <div className="mt-0.5 text-sm text-muted">“Call everyone who owes me, and tell me the tomato rate at 6 tomorrow.”</div>
          </div>
        </div>

        <ul>
          {ROWS.map(([chore, time, done], i) => (
            <motion.li
              key={chore}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-40px" }}
              transition={{ delay: i * 0.06 }}
              className="grid border-b border-line md:grid-cols-2"
            >
              <div className="flex items-center justify-between gap-4 bg-soft px-6 pt-4 pb-1 md:py-4">
                <span className="text-muted line-through decoration-bad/50">{chore}</span>
                <span className="shrink-0 font-mono text-xs text-bad">{time}</span>
              </div>
              <div className="flex items-center gap-3 bg-surface px-6 pt-2 pb-4 md:border-l md:border-line md:py-4">
                <span className="grid size-5 shrink-0 place-items-center bg-ok-soft text-xs font-bold text-ok">✓</span>
                <span className="font-semibold">{done}</span>
              </div>
            </motion.li>
          ))}
        </ul>

        <div className="grid md:grid-cols-2">
          <div className="bg-soft px-6 py-5">
            <div className="mb-2 flex items-baseline justify-between">
              <span className="text-sm text-muted">Time on the phone</span>
              <span className="text-2xl font-extrabold text-bad">50 min · 9 calls</span>
            </div>
            <Bar width="100%" className="bg-bad/70" />
          </div>
          <div className="bg-surface px-6 py-5 md:border-l md:border-line">
            <div className="mb-2 flex items-baseline justify-between">
              <span className="text-sm text-muted">Time on the phone</span>
              <span className="text-2xl font-extrabold text-ok">2 min · 1 call</span>
            </div>
            <Bar width="4%" className="bg-ok" />
          </div>
        </div>
      </div>
    </Section>
  );
}
