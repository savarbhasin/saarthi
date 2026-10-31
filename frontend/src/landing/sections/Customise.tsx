import type { ReactNode } from "react";
import { motion } from "motion/react";
import { cn } from "../ui/cn";
import { SIGN_IN } from "../links";
import { Heading, Section } from "./Section";

// After Aceternity UI's Bento Grid: one tile per page of the web app, each with a live-looking
// preview of it.
function Tile({ title, detail, className, children, i }: { title: string; detail: string; className?: string; children: ReactNode; i: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-40px" }}
      transition={{ duration: 0.5, delay: (i % 3) * 0.08 }}
      className={cn("group flex flex-col bg-surface p-6 transition-colors hover:bg-canvas", className)}
    >
      <div className="min-h-0 flex-1">{children}</div>
      <h3 className="mt-6 text-lg font-bold">{title}</h3>
      <p className="mt-1 text-[15px] text-muted">{detail}</p>
    </motion.div>
  );
}

const mono = "font-mono text-[13px]";

function SkillPreview() {
  return (
    <div className="border border-line bg-canvas">
      <div className="flex items-center gap-2 border-b border-line px-3.5 py-2">
        <strong className={mono}>weekly-report</strong>
        <span className="bg-ok-soft px-1.5 py-0.5 text-[11px] font-semibold text-ok">On</span>
        <span className="ml-auto text-xs text-muted">When I ask for my weekly sales report</span>
      </div>
      <ol className={cn(mono, "grid gap-1 px-3.5 py-3 text-muted")}>
        <li>1. Read ~/files/khata.csv</li>
        <li>2. Total udhaar and payments for the last 7 days</li>
        <li>3. Name the three people who owe the most</li>
      </ol>
    </div>
  );
}

function ConnectorPreview() {
  return (
    <ul className="grid gap-1.5">
      {[
        ["google-sheets", "HTTP"],
        ["notion", "HTTP"],
        ["memory", "Local"],
      ].map(([name, kind], i) => (
        <li key={name} className="flex items-center gap-2 border border-line bg-canvas px-3 py-2">
          <span className={cn(mono, "font-semibold")}>{name}</span>
          <span className="bg-soft px-1.5 py-0.5 text-[11px] font-semibold text-muted">{kind}</span>
          <span className={cn("ml-auto size-2", i < 2 ? "bg-ok" : "bg-line")} />
        </li>
      ))}
    </ul>
  );
}

function InstructionsPreview() {
  return (
    <div className={cn(mono, "border border-line bg-canvas px-3.5 py-3 leading-relaxed")}>
      My UPI ID is ramesh@okaxis.
      <br />
      Always give prices for Azadpur mandi.
      <br />
      Keep answers very short.
      <span className="ml-0.5 inline-block h-4 w-[7px] translate-y-0.5 animate-pulse bg-accent" />
    </div>
  );
}

function SchedulePreview() {
  return (
    <ul className="divide-y divide-line border border-line bg-canvas text-sm">
      {[
        ["Every day", "6:00", "Tomato rate at Azadpur"],
        ["Every day", "8:00", "BP medicine"],
        ["Sundays", "9:00", "Weather for the week"],
      ].map(([when, time, what]) => (
        <li key={what} className="flex items-center gap-3 px-3.5 py-2">
          <span className="w-10 font-mono font-semibold text-accent tabular-nums">{time}</span>
          <span className="flex-1 truncate">{what}</span>
          <span className="text-xs text-muted">{when}</span>
        </li>
      ))}
    </ul>
  );
}

function MemoryPreview() {
  return (
    <div className="flex flex-wrap gap-1.5">
      {["Sells fruit at Azadpur", "Daughter Priya", "Hindi, short answers", "Gupta ji's number"].map((fact) => (
        <span key={fact} className="group/fact flex items-center gap-2 border border-line bg-canvas px-2.5 py-1.5 text-sm">
          {fact}
          <span className="text-xs text-muted transition-colors group-hover/fact:text-bad">✕</span>
        </span>
      ))}
    </div>
  );
}

function LoginPreview() {
  return (
    <div className="grid gap-2">
      <div className="flex items-center gap-2 border border-line bg-canvas px-3.5 py-2.5">
        <span className="text-sm text-muted">+91</span>
        <span className="font-mono text-sm">98765 43210</span>
      </div>
      <div className="flex items-center gap-2 text-sm text-muted">
        <span className="relative size-2 bg-accent">
          <span className="absolute inset-0 animate-ring bg-accent" />
        </span>
        Saarthi is calling you with a code…
      </div>
      <div className="grid grid-cols-6 gap-1.5">
        {"482913".split("").map((digit, i) => (
          <span key={i} className="grid h-10 place-items-center border border-line bg-canvas font-mono text-lg font-bold">
            {digit}
          </span>
        ))}
      </div>
    </div>
  );
}

export function Customise() {
  return (
    <Section id="customise">
      <Heading
        title="Your voice runs it. The web fine-tunes it."
        lede="Sign in with your phone number to teach Saarthi your routines, plug in your tools, and see everything it's done for you."
      />

      <div className="mt-14 grid gap-px border border-line bg-line md:grid-cols-2 lg:grid-cols-3">
        <Tile i={0} className="lg:col-span-2" title="Skills" detail="Write down how you like a job done, step by step. When a task matches, Saarthi follows your steps.">
          <SkillPreview />
        </Tile>
        <Tile i={1} title="No password" detail="Enter your number and Saarthi calls you with a six-digit code.">
          <LoginPreview />
        </Tile>
        <Tile i={2} title="Instructions" detail="Things Saarthi should always know, on every call and every task.">
          <InstructionsPreview />
        </Tile>
        <Tile i={3} title="Connectors" detail="Plug in MCP servers to give the worker more tools: sheets, notes, your own APIs.">
          <ConnectorPreview />
        </Tile>
        <Tile i={4} title="Schedule" detail="Every reminder and routine you've set by voice, in one list.">
          <SchedulePreview />
        </Tile>
        <Tile i={5} className="lg:col-span-2" title="Memory" detail="See what Saarthi remembers about you. Add a fact, or forget one with a click.">
          <MemoryPreview />
        </Tile>
        <a
          href={SIGN_IN}
          className="group flex flex-col justify-between bg-accent-soft p-6 no-underline transition-colors hover:bg-surface"
        >
          <span className="text-[15px] text-muted">Open the web app</span>
          <span className="mt-8 flex items-end justify-between text-2xl font-extrabold text-fg">
            Sign in
            <span className="text-accent transition-transform group-hover:translate-x-1">→</span>
          </span>
        </a>
      </div>
    </Section>
  );
}
