// Adapted from Aceternity UI's Timeline: a saffron beam that fills as you scroll.
import { useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { motion, useScroll, useTransform } from "motion/react";
import { cn } from "./cn";

export type TimelineEntry = { step: string; title: string; content: ReactNode };

export function Timeline({ data, compact = false }: { data: TimelineEntry[]; compact?: boolean }) {
  const ref = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState(0);

  useLayoutEffect(() => {
    if (!ref.current) return;
    const observer = new ResizeObserver(([entry]) => setHeight(entry.contentRect.height));
    observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const { scrollYProgress } = useScroll({ target: containerRef, offset: ["start 10%", "end 50%"] });
  const beamHeight = useTransform(scrollYProgress, [0, 1], [0, height]);
  const beamOpacity = useTransform(scrollYProgress, [0, 0.1], [0, 1]);

  return (
    <div ref={containerRef} className="w-full">
      <div ref={ref} className="relative mx-auto max-w-6xl pb-10">
        {data.map((item) => (
          <div key={item.step} className={cn("flex justify-start pt-10 md:gap-10", !compact && "md:pt-32")}>
            <div className="sticky top-32 z-20 flex max-w-xs flex-col items-center self-start md:w-full md:flex-row lg:max-w-sm">
              <div className="absolute left-3 grid size-10 place-items-center bg-canvas">
                <div className="size-4 border border-accent bg-accent-soft" />
              </div>
              <div className="hidden md:block md:pl-20">
                <h3 className="text-4xl font-extrabold tracking-tight text-fg lg:text-5xl">{item.title}</h3>
              </div>
            </div>
            <div className="relative w-full pr-4 pl-20 md:pl-4">
              <div className="mb-4 md:hidden">
                <h3 className="text-2xl font-extrabold tracking-tight">{item.title}</h3>
              </div>
              {item.content}
            </div>
          </div>
        ))}
        <div
          style={{ height }}
          className="absolute top-0 left-8 w-[2px] overflow-hidden bg-[linear-gradient(to_bottom,transparent_0%,var(--line)_10%,var(--line)_90%,transparent_100%)]"
        >
          <motion.div
            style={{ height: beamHeight, opacity: beamOpacity }}
            className="absolute inset-x-0 top-0 w-[2px] bg-gradient-to-t from-accent from-0% via-[#f59f00] via-10% to-transparent"
          />
        </div>
      </div>
    </div>
  );
}
