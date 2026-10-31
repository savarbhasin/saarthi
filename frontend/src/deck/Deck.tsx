import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import type { MouseEvent, ReactNode } from "react";
import { Customise } from "../landing/sections/Customise";
import { Evening } from "../landing/sections/Evening";
import { Finale } from "../landing/sections/Finale";
import { Hero } from "../landing/sections/Hero";
import { HowItWorks } from "../landing/sections/HowItWorks";
import { LiveTasks } from "../landing/sections/LiveTasks";
import { Phrases } from "../landing/sections/Phrases";
import { Work } from "../landing/sections/Work";

// One landing-page section (or a slice of one) per slide, in page order.
const SLIDES: { render: () => ReactNode }[] = [
  { render: () => <Hero /> },
  { render: () => <HowItWorks from={0} to={3} compact /> },
  { render: () => <HowItWorks from={3} to={5} compact /> },
  { render: () => <LiveTasks /> },
  { render: () => <Work /> },
  { render: () => <Evening /> },
  { render: () => <Customise /> },
  { render: () => <Phrases /> },
  { render: () => <Finale /> },
];

// Room left at the bottom of the window for the deck chrome.
const CHROME = 56;

function useViewport() {
  const [vp, setVp] = useState(() => ({ w: window.innerWidth, h: window.innerHeight }));
  useEffect(() => {
    function onResize() {
      setVp({ w: window.innerWidth, h: window.innerHeight });
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  return vp;
}

function Slide({ children }: { children: ReactNode }) {
  const vp = useViewport();
  const ref = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(0);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el) return;
    const read = () => setHeight(el.scrollHeight);
    const observer = new ResizeObserver(read);
    observer.observe(el);
    read();
    return () => observer.disconnect();
  }, []);

  // Slide content is built for a scrolling page, so shrink it until it fits like a slide.
  const scale = height > 0 ? Math.min(1, (vp.h - CHROME) / height) : 1;

  return (
    <div className="flex h-[calc(100vh-3.5rem)] w-full items-center justify-center overflow-hidden">
      <div style={{ height: height * scale }} className="relative w-full">
        <div
          ref={ref}
          data-slide
          style={{ transform: `scale(${scale})`, transformOrigin: "top center" }}
          className="w-full"
        >
          {children}
        </div>
      </div>
    </div>
  );
}

export function Deck() {
  const [index, setIndex] = useState(0);
  const count = SLIDES.length;
  const go = useCallback(
    (next: number) => setIndex(Math.min(count - 1, Math.max(0, next))),
    [count],
  );

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.metaKey || event.ctrlKey || event.altKey) return;
      const key = event.key;
      if (key === "f" || key === "F") {
        event.preventDefault();
        if (document.fullscreenElement) void document.exitFullscreen();
        else void document.documentElement.requestFullscreen();
        return;
      }
      let next: number | null = null;
      if (key === "ArrowRight" || key === "PageDown" || key === " ") next = index + 1;
      else if (key === "ArrowLeft" || key === "PageUp" || key === "Backspace") next = index - 1;
      else if (key === "Home") next = 0;
      else if (key === "End") next = count - 1;
      else {
        const digit = Number(key);
        if (digit >= 1 && digit <= count) go(digit - 1);
        return;
      }
      event.preventDefault();
      go(next);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, index, count]);

  function pick(next: number) {
    return (event: MouseEvent<HTMLButtonElement>) => {
      event.currentTarget.blur();
      go(next);
    };
  }

  const { render } = SLIDES[index];

  return (
    <div className="fixed inset-0 overflow-hidden bg-canvas text-fg">
      <AnimatePresence>
        <motion.div
          key={index}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.22, ease: "easeOut" }}
        >
          <Slide>{render()}</Slide>
        </motion.div>
      </AnimatePresence>

      <div className="absolute inset-x-0 bottom-0 z-10 flex select-none items-center justify-between gap-4 px-4 pb-3 md:px-6">
        <div className="text-sm font-extrabold tracking-tight">सारथी</div>
        <div className="flex items-center gap-1.5" aria-label="Slides">
          {SLIDES.map((_, n) => (
            <button
              key={n}
              aria-label={`Slide ${n + 1}`}
              aria-current={n === index}
              onClick={pick(n)}
              className={`h-1.5 w-4 transition-colors ${
                n === index ? "bg-accent" : "bg-line hover:bg-muted"
              }`}
            />
          ))}
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold tabular-nums text-muted">
            {index + 1} / {count}
          </span>
          <button
            aria-label="Previous slide"
            onClick={pick(index - 1)}
            className="grid h-8 w-8 place-items-center border border-line bg-surface text-muted transition-colors hover:text-fg"
          >
            ←
          </button>
          <button
            aria-label="Next slide"
            onClick={pick(index + 1)}
            className="grid h-8 w-8 place-items-center border border-line bg-surface text-muted transition-colors hover:text-fg"
          >
            →
          </button>
        </div>
      </div>

      <motion.div
        className="pointer-events-none absolute inset-x-0 bottom-0 h-[2px] origin-left bg-accent"
        initial={false}
        animate={{ width: `${((index + 1) / count) * 100}%` }}
        transition={{ duration: 0.3, ease: "easeOut" }}
      />
    </div>
  );
}
