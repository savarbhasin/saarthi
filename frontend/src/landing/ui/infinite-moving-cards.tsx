// Adapted from Aceternity UI's Infinite Moving Cards: an endless marquee that pauses on hover.
import type { ReactNode } from "react";
import { cn } from "./cn";

export function InfiniteMovingCards({
  items,
  direction = "left",
  speed = 60,
  className,
}: {
  items: { key: string; node: ReactNode }[];
  direction?: "left" | "right";
  /** Seconds for one full loop. */
  speed?: number;
  className?: string;
}) {
  // Rendering the list twice lets the track slide by half its width and loop without a seam.
  const doubled = [...items.map((i) => ({ ...i, key: `a-${i.key}` })), ...items.map((i) => ({ ...i, key: `b-${i.key}` }))];
  return (
    <div
      className={cn(
        "relative overflow-hidden [mask-image:linear-gradient(to_right,transparent,white_12%,white_88%,transparent)]",
        className,
      )}
      style={
        {
          "--animation-duration": `${speed}s`,
          "--animation-direction": direction === "left" ? "forwards" : "reverse",
        } as React.CSSProperties
      }
    >
      <ul className="flex w-max min-w-full shrink-0 animate-scroll flex-nowrap gap-4 py-2 hover:[animation-play-state:paused]">
        {doubled.map((item, i) => (
          <li key={item.key} aria-hidden={i >= items.length || undefined} className="shrink-0">
            {item.node}
          </li>
        ))}
      </ul>
    </div>
  );
}
