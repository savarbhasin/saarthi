// Adapted from Aceternity UI's Layout Text Flip: a word in a box that swaps, with the box
// resizing to fit.
import { useEffect, useState } from "react";
import { AnimatePresence, motion } from "motion/react";

export function LayoutTextFlip({ words, duration = 2400 }: { words: string[]; duration?: number }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setIndex((i) => (i + 1) % words.length), duration);
    return () => clearInterval(interval);
  }, [words.length, duration]);

  return (
    <motion.span layout className="relative inline-flex w-fit overflow-hidden border border-accent bg-accent-soft px-3 py-0.5 text-accent">
      <AnimatePresence mode="popLayout">
        <motion.span
          key={index}
          initial={{ y: -40, filter: "blur(10px)" }}
          animate={{ y: 0, filter: "blur(0px)" }}
          exit={{ y: 50, filter: "blur(10px)", opacity: 0 }}
          transition={{ duration: 0.5 }}
          className="inline-block whitespace-nowrap"
        >
          {words[index]}
        </motion.span>
      </AnimatePresence>
    </motion.span>
  );
}
