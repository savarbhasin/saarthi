import { motion } from "motion/react";
import { BackgroundRippleEffect } from "../ui/background-ripple-effect";
import { TextHoverEffect } from "../ui/text-hover-effect";
import { APP, SIGN_IN } from "../links";
import { CtaLink } from "./Section";

export function Finale() {
  return (
    <>
      <section className="relative isolate flex min-h-[640px] items-center justify-center overflow-hidden border-t border-line px-4 py-28">
        <BackgroundRippleEffect />
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="pointer-events-none relative z-10 mx-auto max-w-3xl text-center"
        >
          <h2 className="text-5xl leading-[1.05] font-extrabold tracking-tight text-balance md:text-7xl">
            Your saarthi is <span className="text-accent">one call</span> away.
          </h2>
          <p className="mx-auto mt-6 max-w-xl text-lg text-muted">
            Krishna held Arjun's reins so he could face the battle. Saarthi holds your to-do list so you can get on with
            your day.
          </p>
          <div className="pointer-events-auto mt-10 flex flex-wrap justify-center gap-3">
            <CtaLink href={SIGN_IN}>Set up your Saarthi</CtaLink>
          </div>
          <p className="mt-6 text-xs text-muted">Click anywhere on the grid.</p>
        </motion.div>
      </section>

      <footer className="border-t border-line bg-surface px-4 pt-10 pb-8 md:px-10">
        <div className="mx-auto max-w-6xl">
          <div className="-mx-4 h-[clamp(9rem,26vw,22rem)] md:-mx-10">
            <TextHoverEffect text="सारथी" viewBox="0 0 300 110" />
          </div>
          <div className="mt-4 flex flex-col gap-4 border-t border-line pt-6 text-sm text-muted sm:flex-row sm:items-center sm:justify-between">
            <span>
              <b className="text-fg">सारथी Saarthi</b> · Built on{" "}
              <a href="https://bolna.ai" className="font-semibold text-fg">
                Bolna
              </a>{" "}
              for the Symphony Buildathon, 2026.
            </span>
            <nav className="flex gap-5">
              <a href="#how" className="text-muted no-underline hover:text-fg">
                How it works
              </a>
              <a href="#work" className="text-muted no-underline hover:text-fg">
                For your work
              </a>
              <a href={APP} className="font-semibold text-accent no-underline">
                Open the app
              </a>
            </nav>
          </div>
        </div>
      </footer>
    </>
  );
}
