// A live task feed: each task runs its steps in turn, after Aceternity UI's Multi Step Loader,
// then hands over to the next, like the Tasks page of the web app.
import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useInView } from "motion/react";
import { cn } from "../ui/cn";
import { Heading, Section } from "./Section";

type Task = { title: string; said: string; steps: string[]; result: string };

const TASKS: Task[] = [
  {
    title: "Tomato rate at Azadpur",
    said: "आज आज़ादपुर में टमाटर का भाव?",
    steps: ["Open agmarknet.gov.in", "Find Azadpur mandi, Delhi", "Read today's tomato prices", "Compare with yesterday"],
    result: "₹1,800 – ₹2,200 a quintal, up ₹100 on yesterday.",
  },
  {
    title: "Trains to Jaipur tomorrow",
    said: "कल दिल्ली से जयपुर की ट्रेनें देखो",
    steps: ["Open the train timetable", "List tomorrow's trains", "Check sleeper and chair car seats", "Pick the three best"],
    result: "Ajmer Shatabdi at 6:10 am has seats. Two more in the evening.",
  },
  {
    title: "Remind 6 people about dues",
    said: "जिन पर उधार है सबको फ़ोन करो",
    steps: ["Read ~/files/khata.csv", "Find everyone who owes", "Call 6 people, 20 s apart", "Note every reply"],
    result: "3 paid, 2 will pay this week, 1 didn't pick up.",
  },
  {
    title: "Cheapest Redmi Note 14",
    said: "Redmi Note 14 का सबसे सस्ता दाम ढूँढो",
    steps: ["Search three shopping sites", "Add bank and exchange offers", "Check delivery to your pincode", "Compare the final prices"],
    result: "₹17,499 with a card offer, delivered by Friday.",
  },
];

const STEP_MS = 1100;

function Status({ state }: { state: "done" | "working" | "waiting" }) {
  const look = {
    done: "bg-ok-soft text-ok",
    working: "bg-accent-soft text-accent",
    waiting: "bg-soft text-muted",
  }[state];
  return (
    <span className={cn("inline-flex shrink-0 items-center gap-1.5 px-2 py-0.5 text-xs font-semibold", look)}>
      {state === "working" && (
        <span className="relative size-1.5 bg-accent">
          <span className="absolute inset-0 animate-ring bg-accent" />
        </span>
      )}
      {state === "done" ? "Done" : state === "working" ? "Working" : "Queued"}
    </span>
  );
}

export function LiveTasks() {
  const ref = useRef<HTMLDivElement>(null);
  const inView = useInView(ref, { margin: "-120px" });
  // Which task is running, and how many of its steps are finished (steps.length + 1 = result shown).
  const [active, setActive] = useState(0);
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (!inView) return;
    const task = TASKS[active];
    const finished = step > task.steps.length;
    const timer = setTimeout(
      () => {
        if (!finished) return setStep((s) => s + 1);
        setActive((a) => (a + 1) % TASKS.length);
        setStep(0);
      },
      finished ? 2600 : STEP_MS,
    );
    return () => clearTimeout(timer);
  }, [inView, active, step]);

  const task = TASKS[active];

  return (
    <Section id="live" className="border-t border-line bg-surface">
      <Heading
        title="Hang up. The work carries on."
        lede="Any call can start a task. Saarthi's worker picks it up, does it step by step on its own computer, and calls you when it's done. Watch every task as it happens."
      />

      <div ref={ref} className="mt-14 grid border border-line md:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <div className="border-b border-line md:border-r md:border-b-0">
          <div className="flex items-center justify-between border-b border-line px-5 py-3 text-sm font-semibold">
            Tasks
            <span className="font-mono text-xs font-normal text-muted">today</span>
          </div>
          <ul>
            {TASKS.map((t, i) => {
              // Tasks before the running one in this loop are done; later ones wait.
              const state = i < active ? "done" : i === active ? (step > t.steps.length ? "done" : "working") : "waiting";
              return (
                <li
                  key={t.title}
                  className={cn(
                    "flex items-center gap-3 border-b border-line px-5 py-4 transition-colors last:border-b-0",
                    i === active ? "bg-canvas" : "bg-surface",
                  )}
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-semibold">{t.title}</div>
                    <div className="mt-0.5 truncate text-sm text-muted">“{t.said}”</div>
                  </div>
                  <Status state={state} />
                </li>
              );
            })}
            <li className="flex items-center gap-3 px-5 py-4">
              <div className="min-w-0 flex-1">
                <div className="truncate font-semibold">BP medicine reminder</div>
                <div className="mt-0.5 text-sm text-muted">Every day at 8:00 am</div>
              </div>
              <span className="bg-soft px-2 py-0.5 text-xs font-semibold text-muted">Daily</span>
            </li>
          </ul>
        </div>

        <div className="flex min-h-[420px] flex-col bg-canvas p-6 md:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={task.title}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.35 }}
              className="flex flex-1 flex-col"
            >
              <h3 className="text-2xl font-extrabold tracking-tight md:text-3xl">{task.title}</h3>
              <p className="mt-1 text-muted">You said: “{task.said}”</p>

              <ol className="mt-7 grid gap-3.5">
                {task.steps.map((s, i) => {
                  const done = i < step;
                  const current = i === step;
                  return (
                    <li key={s} className={cn("flex items-center gap-3 text-[17px] transition-colors", done ? "text-fg" : current ? "font-semibold text-fg" : "text-muted/60")}>
                      <span
                        className={cn(
                          "grid size-6 shrink-0 place-items-center border text-xs font-bold transition-colors",
                          done ? "border-ok bg-ok text-surface" : current ? "border-accent text-accent" : "border-line",
                        )}
                      >
                        {done ? "✓" : current ? <span className="size-2 animate-pulse bg-accent" /> : null}
                      </span>
                      {s}
                    </li>
                  );
                })}
              </ol>

              <div className="mt-auto pt-7">
                <AnimatePresence>
                  {step > task.steps.length - 1 && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="flex items-start gap-3 border border-line bg-surface px-4 py-3.5"
                    >
                      <span className="grid size-8 shrink-0 place-items-center bg-accent-soft text-sm font-bold text-accent">सा</span>
                      <div>
                        <div className="text-xs font-semibold text-muted">{step > task.steps.length ? "Called you back" : "Calling you…"}</div>
                        <div className="mt-0.5 font-semibold">{task.result}</div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </Section>
  );
}
