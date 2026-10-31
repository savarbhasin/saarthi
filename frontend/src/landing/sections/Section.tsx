import type { ReactNode } from "react";
import { motion } from "motion/react";
import { cn } from "../ui/cn";

export function Section({ id, className, children }: { id?: string; className?: string; children: ReactNode }) {
  return (
    <section id={id} className={cn("relative scroll-mt-20 px-4 py-24 md:px-10 md:py-32", className)}>
      <div className="mx-auto max-w-6xl">{children}</div>
    </section>
  );
}

export function Heading({ title, lede, className }: { title: ReactNode; lede?: ReactNode; className?: string }) {
  return (
    <motion.div
      className={cn("max-w-3xl", className)}
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.6, ease: "easeOut" }}
    >
      <h2 className="text-4xl leading-[1.05] font-extrabold tracking-tight text-balance md:text-6xl">{title}</h2>
      {lede && <p className="mt-5 max-w-2xl text-lg leading-relaxed text-pretty text-muted">{lede}</p>}
    </motion.div>
  );
}

export function CtaLink({ href, children }: { href: string; children: ReactNode }) {
  return (
    <a
      href={href}
      className="group inline-flex items-center gap-2 border border-accent bg-accent px-6 py-3.5 text-[15px] font-bold text-accent-fg no-underline transition hover:brightness-105"
    >
      {children}
      <span aria-hidden className="transition-transform group-hover:translate-x-0.5">
        →
      </span>
    </a>
  );
}
