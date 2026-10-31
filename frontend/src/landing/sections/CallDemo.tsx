// A scripted call that plays on a loop: the caller asks, Saarthi answers, a task runs, and
// Saarthi rings back with the result.
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import { cn } from "../ui/cn";

type Turn = { who: "you" | "saarthi"; hi: string; en: string };

const TURNS: Turn[] = [
  { who: "you", hi: "आज आज़ादपुर में टमाटर का भाव क्या है?", en: "What's the tomato rate at Azadpur today?" },
  {
    who: "saarthi",
    hi: "आज टमाटर ₹1,800 से ₹2,200 क्विंटल चल रहा है, कल से थोड़ा ऊपर।",
    en: "₹1,800 to ₹2,200 a quintal, a little up from yesterday.",
  },
  { who: "you", hi: "जिन पर उधार है, सबको फ़ोन करके याद दिला दो।", en: "Call everyone who owes me and remind them." },
  {
    who: "saarthi",
    hi: "ठीक है, छह लोगों को फ़ोन लगाते हैं। हो जाने पर आपको कॉल करेंगे।",
    en: "Okay, calling six people. We'll ring you when it's done.",
  },
];

const PEOPLE: [string, string, "ok" | "warn" | "muted"][] = [
  ["Sharma ji", "Paid ₹450", "ok"],
  ["Gupta ji", "Will pay Sunday", "warn"],
  ["Khan bhai", "Paid ₹600", "ok"],
  ["Verma ji", "Pays on the 5th", "warn"],
  ["Rao ji", "No answer", "muted"],
  ["Mehta ji", "Paid ₹200", "ok"],
];

// How long each stage stays on screen: four turns, the calls, the call back.
const STAGES = [2600, 3600, 2800, 3400, 6400, 5200];

const TONE = { ok: "bg-ok-soft text-ok", warn: "bg-warn-soft text-warn", muted: "bg-soft text-muted" };

function Words({ text, className }: { text: string; className?: string }) {
  return (
    <span className={className}>
      {text.split(" ").map((word, i) => (
        <motion.span
          key={i}
          className="inline-block"
          initial={{ opacity: 0, filter: "blur(6px)", y: 4 }}
          animate={{ opacity: 1, filter: "blur(0px)", y: 0 }}
          transition={{ delay: i * 0.07, duration: 0.35 }}
        >
          {word}&nbsp;
        </motion.span>
      ))}
    </span>
  );
}

function Wave({ speaking }: { speaking: "you" | "saarthi" | null }) {
  return (
    <div className="flex h-7 items-center gap-[3px]" aria-hidden>
      {Array.from({ length: 14 }, (_, i) => (
        <span
          key={i}
          className={cn(
            "h-full w-[3px] origin-center transition-colors",
            speaking ? "animate-wave" : "scale-y-[0.15]",
            speaking === "saarthi" ? "bg-accent" : speaking === "you" ? "bg-fg" : "bg-line",
          )}
          style={{ animationDelay: `${((i * 37) % 11) * -0.1}s`, animationDuration: `${0.7 + ((i * 13) % 7) * 0.09}s` }}
        />
      ))}
    </div>
  );
}

function Calls({ running }: { running: boolean }) {
  const [done, setDone] = useState(0);
  useEffect(() => {
    if (!running) return;
    setDone(0);
    const timer = setInterval(() => setDone((d) => Math.min(d + 1, PEOPLE.length)), 900);
    return () => clearInterval(timer);
  }, [running]);

  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="border border-line bg-canvas">
      <div className="flex items-center justify-between border-b border-line px-3.5 py-2 text-xs">
        <span className="font-mono font-semibold tracking-wider text-accent uppercase">Task · Dues reminders</span>
        <span className="font-mono text-muted">
          {done}/{PEOPLE.length} called
        </span>
      </div>
      <ul className="divide-y divide-line">
        {PEOPLE.map(([name, result, tone], i) => (
          <li key={name} className="flex items-center justify-between px-3.5 py-1.5 text-sm">
            <span className="font-semibold">{name}</span>
            {i < done ? (
              <motion.span initial={{ opacity: 0, x: 8 }} animate={{ opacity: 1, x: 0 }} className={cn("px-2 py-0.5 text-xs font-semibold", TONE[tone])}>
                {result}
              </motion.span>
            ) : i === done ? (
              <span className="flex items-center gap-1.5 text-xs font-semibold text-accent">
                <span className="relative size-2 bg-accent">
                  <span className="absolute inset-0 animate-ring bg-accent" />
                </span>
                Calling
              </span>
            ) : (
              <span className="text-xs text-muted">Waiting</span>
            )}
          </li>
        ))}
      </ul>
    </motion.div>
  );
}

export function CallDemo() {
  const [stage, setStage] = useState(0);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const timer = setTimeout(() => setStage((s) => (s + 1) % STAGES.length), STAGES[stage]);
    return () => clearTimeout(timer);
  }, [stage]);

  useEffect(() => {
    if (stage === 0) setSeconds(0);
    const timer = setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => clearInterval(timer);
  }, [stage]);

  const turns = TURNS.slice(0, Math.min(stage + 1, TURNS.length));
  const calling = stage === 4;
  const callback = stage === 5;
  const speaking = stage < TURNS.length ? TURNS[stage].who : callback ? "saarthi" : null;
  const clock = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;

  return (
    <div className="relative w-full border border-line bg-surface">
      <div className="flex items-center gap-3 border-b border-line px-4 py-3">
        <div className="relative grid size-10 shrink-0 place-items-center bg-accent-soft font-bold text-accent">
          सा
        </div>
        <div className="min-w-0 flex-1">
          <div className="font-bold">Saarthi</div>
          <div className="font-mono text-xs text-muted">
            {callback ? "Calling you back…" : calling ? "Hung up · working on it" : `On call · ${clock}`}
          </div>
        </div>
        <Wave speaking={speaking} />
      </div>

      <div className="flex h-[400px] flex-col justify-end gap-3 overflow-hidden p-4 [mask-image:linear-gradient(to_bottom,transparent,black_18%)]">
        <AnimatePresence initial={false}>
          {!callback &&
            turns.map((turn) => (
              <motion.div
                key={turn.hi}
                layout
                exit={{ opacity: 0 }}
                className={cn("max-w-[88%]", turn.who === "you" ? "self-end text-right" : "self-start")}
              >
                <div className="mb-1 font-mono text-[11px] font-semibold tracking-wider text-muted uppercase">
                  {turn.who === "you" ? "आप · You" : "सारथी · Saarthi"}
                </div>
                <div
                  className={cn(
                    "inline-block px-3.5 py-2.5 text-left text-[15px] leading-snug",
                    turn.who === "you" ? "bg-fg text-canvas" : "border border-accent/40 bg-accent-soft text-fg",
                  )}
                >
                  <Words text={turn.hi} />
                  <div className={cn("mt-1 text-xs", turn.who === "you" ? "text-canvas/60" : "text-muted")}>{turn.en}</div>
                </div>
              </motion.div>
            ))}
          {calling && (
            <motion.div key="calls" layout exit={{ opacity: 0 }}>
              <Calls running={calling} />
            </motion.div>
          )}
          {callback && (
            <motion.div key="callback" layout initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} className="self-start">
              <div className="mb-1 font-mono text-[11px] font-semibold tracking-wider text-muted uppercase">सारथी · Saarthi</div>
              <div className="border border-accent/40 bg-accent-soft px-3.5 py-2.5 text-[15px] leading-snug">
                <Words text="सबको फ़ोन हो गया। शर्मा जी, खान भाई और मेहता जी ने पैसे दे दिए। गुप्ता जी रविवार को देंगे।" />
                <div className="mt-1 text-xs text-muted">
                  Everyone's been called. Sharma ji, Khan bhai and Mehta ji paid. Gupta ji will pay on Sunday.
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
