import { motion } from "motion/react";
import { DottedGlowBackground } from "../ui/dotted-glow-background";
import { SIGN_IN } from "../links";
import { CallDemo } from "./CallDemo";
import { CtaLink } from "./Section";

const FACTS = [
  ["11", "languages, switch mid-call"],
  ["0", "apps to install"],
  ["Any", "phone, even a keypad one"],
];

const rise = (delay: number) => ({
  initial: { opacity: 0, y: 28 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] as const },
});

export function Hero() {
  return (
    <section id="top" className="relative isolate flex min-h-[100dvh] items-center px-4 pt-28 pb-20 md:px-10">
      <div className="pointer-events-none absolute inset-0 -z-10 mask-radial-from-10% mask-radial-at-[70%_40%] mask-b-from-50% opacity-90">
        <DottedGlowBackground
          gap={16}
          radius={1.4}
          colorLightVar="--muted"
          colorDarkVar="--muted"
          glowColorLightVar="--accent"
          glowColorDarkVar="--accent"
          opacity={0.55}
          speedMin={0.3}
          speedMax={1.1}
        />
      </div>

      <div className="mx-auto grid w-full max-w-6xl items-center gap-14 lg:grid-cols-[1.1fr_0.9fr]">
        <div>
          <motion.a
            {...rise(0)}
            href="https://bolna.ai"
            className="mb-7 inline-flex items-center gap-2.5 border border-line bg-surface px-3 py-1.5 text-sm font-semibold text-muted no-underline hover:text-fg"
          >
            <span className="relative size-2 bg-ok">
              <span className="absolute inset-0 animate-ring bg-ok" />
            </span>
            Live on Bolna Voice AI
          </motion.a>

          <motion.h1 {...rise(0.08)} className="text-[clamp(2.5rem,4.6vw,4.25rem)] leading-[0.98] font-extrabold tracking-tight">
            Don't download.
            <br />
            Just <span className="text-accent">call.</span>
          </motion.h1>

          <motion.p {...rise(0.18)} className="mt-7 max-w-xl text-lg leading-relaxed text-pretty text-muted md:text-xl">
            Saarthi is a personal AI agent you reach with an ordinary phone call. Say what you need in your own
            language. It remembers you, works on its own computer, phones people for you, and calls back when the job
            is done.
          </motion.p>

          <motion.div {...rise(0.28)} className="mt-9 flex flex-wrap items-center gap-3">
            <CtaLink href={SIGN_IN}>Set up your Saarthi</CtaLink>
            <a href="#how" className="px-4 py-3.5 text-[15px] font-semibold text-muted no-underline hover:text-fg">
              See how it works
            </a>
          </motion.div>

          <motion.dl {...rise(0.38)} className="mt-12 grid max-w-xl grid-cols-3 border-t border-line">
            {FACTS.map(([big, small]) => (
              <div key={small} className="border-r border-line py-4 pr-3 last:border-r-0 [&:not(:first-child)]:pl-4">
                <dt className="text-3xl font-extrabold tracking-tight">{big}</dt>
                <dd className="mt-0.5 text-sm text-muted">{small}</dd>
              </div>
            ))}
          </motion.dl>
        </div>

        <motion.div {...rise(0.25)} className="relative">
          {/* Corner ticks frame the call like a viewfinder. */}
          <span className="absolute -top-3 -left-3 size-6 border-t-2 border-l-2 border-accent" />
          <span className="absolute -right-3 -bottom-3 size-6 border-r-2 border-b-2 border-accent" />
          <CallDemo />
        </motion.div>
      </div>
    </section>
  );
}
