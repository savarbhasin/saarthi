// Adapted from Aceternity UI's Background Ripple Effect: a grid of cells; click one and a ripple
// spreads out from it.
import { useMemo, useState } from "react";
import { cn } from "./cn";

export function BackgroundRippleEffect({ rows = 13, cols = 30, cellSize = 56 }: { rows?: number; cols?: number; cellSize?: number }) {
  const [clicked, setClicked] = useState<{ row: number; col: number } | null>(null);
  const [rippleKey, setRippleKey] = useState(0);
  const cells = useMemo(() => Array.from({ length: rows * cols }, (_, i) => i), [rows, cols]);

  return (
    <div className="absolute inset-0 h-full w-full overflow-hidden">
      <div
        key={rippleKey}
        className="relative mx-auto mask-radial-from-20% mask-radial-at-top"
        style={{
          display: "grid",
          gridTemplateColumns: `repeat(${cols}, ${cellSize}px)`,
          gridTemplateRows: `repeat(${rows}, ${cellSize}px)`,
          width: cols * cellSize,
          height: rows * cellSize,
          marginLeft: "50%",
          transform: "translateX(-50%)",
        }}
      >
        {cells.map((i) => {
          const row = Math.floor(i / cols);
          const col = i % cols;
          const distance = clicked ? Math.hypot(clicked.row - row, clicked.col - col) : 0;
          return (
            <div
              key={i}
              className={cn(
                "border-[0.5px] border-line bg-surface opacity-40 transition-[opacity,background-color] duration-150 hover:bg-accent-soft hover:opacity-90",
                clicked && "animate-cell-ripple [animation-fill-mode:none]",
              )}
              style={
                clicked
                  ? ({ "--delay": `${distance * 55}ms`, "--duration": `${200 + distance * 80}ms` } as React.CSSProperties)
                  : undefined
              }
              onClick={() => {
                setClicked({ row, col });
                setRippleKey((k) => k + 1);
              }}
            />
          );
        })}
      </div>
    </div>
  );
}
