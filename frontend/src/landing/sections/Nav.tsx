// After Aceternity UI's Resizable Navbar: full width at the top, then it tightens into a framed
// bar once the page scrolls.
import { useState } from "react";
import { motion, useMotionValueEvent, useScroll } from "motion/react";
import { cn } from "../ui/cn";
import { SIGN_IN } from "../links";

const ITEMS = [
  ["How it works", "#how"],
  ["For your work", "#work"],
  ["Make it yours", "#customise"],
];

export function Nav() {
  const { scrollY } = useScroll();
  const [compact, setCompact] = useState(false);
  const [hovered, setHovered] = useState<number | null>(null);
  useMotionValueEvent(scrollY, "change", (y) => setCompact(y > 80));

  return (
    <header className="fixed inset-x-0 top-0 z-50 px-3 md:px-6">
      <motion.nav
        animate={{ maxWidth: compact ? 920 : 1240, y: compact ? 12 : 0 }}
        transition={{ type: "spring", stiffness: 200, damping: 40 }}
        className={cn(
          "mx-auto flex items-center justify-between gap-4 border px-3 py-2.5 transition-colors md:px-4",
          compact ? "border-line bg-surface/85 backdrop-blur-md" : "border-transparent bg-transparent",
        )}
      >
        <a href="#top" className="shrink-0 px-1 text-xl font-bold whitespace-nowrap text-fg no-underline">
          सारथी <span className="text-accent">Saarthi</span>
        </a>

        <div className="hidden items-center lg:flex" onMouseLeave={() => setHovered(null)}>
          {ITEMS.map(([label, href], i) => (
            <a
              key={href}
              href={href}
              onMouseEnter={() => setHovered(i)}
              className="relative px-4 py-2 text-sm font-semibold text-muted no-underline transition-colors hover:text-fg"
            >
              {hovered === i && <motion.span layoutId="nav-hover" className="absolute inset-0 bg-soft" />}
              <span className="relative">{label}</span>
            </a>
          ))}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <a href={SIGN_IN} className="hidden px-3 py-2 text-sm font-semibold text-muted no-underline hover:text-fg sm:block">
            Sign in
          </a>
          <a
            href={SIGN_IN}
            className="border border-accent bg-accent px-4 py-2 text-sm font-bold text-accent-fg no-underline transition hover:brightness-105"
          >
            Get started
          </a>
        </div>
      </motion.nav>
    </header>
  );
}
