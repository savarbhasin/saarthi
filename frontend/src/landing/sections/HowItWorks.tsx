import type { ReactNode } from "react";
import { motion } from "motion/react";
import { EncryptedText } from "../ui/encrypted-text";
import { Terminal } from "../ui/terminal";
import { Timeline } from "../ui/timeline";
import { cn } from "../ui/cn";
import { Heading, Section } from "./Section";

function Copy({ children }: { children: ReactNode }) {
  return <p className="mb-6 max-w-xl text-lg leading-relaxed text-pretty text-muted">{children}</p>;
}

const appear = (i = 0) => ({
  initial: { opacity: 0, y: 16 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-60px" },
  transition: { duration: 0.5, delay: i * 0.08 },
});

const GREETINGS = [
  ["hi", "नमस्ते रमेश जी! बताइए, क्या करना है?"],
  ["en", "Hello Ramesh ji! What can I do for you?"],
  ["ta", "வணக்கம் ரமேஷ் ஜி! என்ன செய்யணும்?"],
  ["bn", "নমস্কার রমেশ জি! কী করতে হবে?"],
];

function YouCall() {
  return (
    <>
      <Copy>
        Ring Saarthi from any phone. No app, no typing, no English needed. It knows you by your number and greets you
        by name, in the language you like.
      </Copy>
      <div className="grid gap-2 sm:grid-cols-2">
        {GREETINGS.map(([lang, text], i) => (
          <motion.div key={lang} {...appear(i)} className="flex items-start gap-3 border border-line bg-surface px-4 py-3">
            <span className="mt-0.5 font-mono text-xs font-semibold text-accent uppercase">{lang}</span>
            <span className="text-[15px]">{text}</span>
          </motion.div>
        ))}
      </div>
    </>
  );
}

const FACTS = [
  "Sells fruit at Azadpur mandi",
  "Daughter Priya, in class 8",
  "Likes short answers in Hindi",
  "Gupta ji's number: 98xxxxxx21",
  "BP medicine at 8 every morning",
  "UPI ID ramesh@okaxis",
];

function Remembers() {
  return (
    <>
      <Copy>
        Everything you mention, on every call: your family, your work, the people you deal with. Ask what it remembers,
        or tell it to forget. You can see and edit it all on the web.
      </Copy>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {FACTS.map((fact, i) => (
          <motion.div key={fact} {...appear(i)} className="border border-line bg-surface px-4 py-3">
            <div className="mb-1 font-mono text-[11px] font-semibold tracking-wider text-muted uppercase">Remembered</div>
            <EncryptedText
              text={fact}
              revealDelayMs={28}
              className="text-[15px] font-semibold"
              encryptedClassName="text-accent/70"
              revealedClassName="text-fg"
            />
          </motion.div>
        ))}
      </div>
    </>
  );
}

function Works() {
  return (
    <>
      <Copy>
        Behind every Saarthi is a worker with its own private computer: a browser, files and code. It looks things up,
        fills forms and keeps your ledgers. Hang up; it keeps going.
      </Copy>
      <Terminal
        title="ramesh's computer — saarthi worker"
        commands={[
          "browse agmarknet.gov.in --mandi Azadpur --crop Tomato",
          "python ~/files/khata.py --owed",
          "request_calls --people 6 --purpose 'dues reminder'",
        ]}
        outputs={{
          0: ["→ Tomato, Azadpur, today: ₹1,800 – ₹2,200 per quintal", "→ Yesterday: ₹1,700 – ₹2,100"],
          1: ["Sharma ji   450", "Gupta ji    340", "Khan bhai   600", "Verma ji   1500", "…  6 people owe ₹3,290 in all"],
          2: ["✓ 6 calls queued, 20 s apart, within calling hours", "✓ Will call Ramesh with the replies"],
        }}
      />
    </>
  );
}

const CONTACTS: [string, string, string][] = [
  ["Sharma ji", "Paid ₹450", "text-ok"],
  ["Gupta ji", "Sunday", "text-warn"],
  ["Khan bhai", "Paid ₹600", "text-ok"],
  ["Verma ji", "On the 5th", "text-warn"],
  ["Rao ji", "No answer", "text-muted"],
  ["Mehta ji", "Paid ₹200", "text-ok"],
];

function CallsPeople() {
  return (
    <>
      <Copy>
        Need to remind six people, ask a supplier for a rate, or tell your brother you'll be late? Saarthi makes the
        calls, says who it's calling for and why, and notes every answer.
      </Copy>
      <div className="grid grid-cols-2 gap-px border border-line bg-line sm:grid-cols-3">
        {CONTACTS.map(([name, reply, tone], i) => (
          <motion.div key={name} {...appear(i)} className="bg-surface px-4 py-3.5">
            <div className="flex items-center gap-2 font-semibold">
              <span className="grid size-7 place-items-center bg-soft text-xs font-bold">{name[0]}</span>
              {name}
            </div>
            <div className={cn("mt-1.5 text-sm font-semibold", tone)}>{reply}</div>
          </motion.div>
        ))}
      </div>
    </>
  );
}

function CallsBack() {
  return (
    <>
      <Copy>
        When the work is done, your phone rings. Saarthi tells you what happened in a few plain sentences, and the full
        result waits for you on the web.
      </Copy>
      <motion.div {...appear()} className="max-w-xl border border-line bg-surface">
        <div className="flex items-center gap-3 border-b border-line px-4 py-3">
          <span className="relative grid size-9 place-items-center bg-accent-soft font-bold text-accent">
            सा
          </span>
          <div>
            <div className="font-bold">Saarthi is calling…</div>
            <div className="text-xs text-muted">Task done · Dues reminders</div>
          </div>
        </div>
        <p className="px-4 py-4 text-[15px] leading-relaxed">
          "Six calls done. Sharma ji, Khan bhai and Mehta ji have paid. Gupta ji will pay on Sunday and Verma ji on the
          5th. Rao ji didn't pick up. Shall I try him again at seven?"
        </p>
      </motion.div>
    </>
  );
}

export function HowItWorks({ from = 0, to, compact = false }: { from?: number; to?: number; compact?: boolean }) {
  const entries = [
    { step: "01", title: "You call.", content: <YouCall /> },
    { step: "02", title: "It remembers.", content: <Remembers /> },
    { step: "03", title: "It gets to work.", content: <Works /> },
    { step: "04", title: "It calls people.", content: <CallsPeople /> },
    { step: "05", title: "It calls you back.", content: <CallsBack /> },
  ];
  return (
    <Section id="how">
      <Heading
        title="One call. The rest is Saarthi's job."
        lede="Saarthi means charioteer: the one who holds the reins so you can keep your eyes on the road."
      />
      <Timeline data={entries.slice(from, to ?? entries.length)} compact={compact} />
    </Section>
  );
}
