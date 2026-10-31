// Adapted from Aceternity UI's Text Hover Effect: outlined text that draws itself in, with a
// saffron gradient revealed under the cursor.
import { useEffect, useId, useRef, useState } from "react";
import { motion } from "motion/react";

export function TextHoverEffect({ text, viewBox = "0 0 300 100" }: { text: string; viewBox?: string }) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [cursor, setCursor] = useState({ x: 0, y: 0 });
  const [hovered, setHovered] = useState(false);
  const [mask, setMask] = useState({ cx: "50%", cy: "50%" });
  const id = useId().replace(/:/g, "");

  useEffect(() => {
    if (!svgRef.current) return;
    const rect = svgRef.current.getBoundingClientRect();
    setMask({ cx: `${((cursor.x - rect.left) / rect.width) * 100}%`, cy: `${((cursor.y - rect.top) / rect.height) * 100}%` });
  }, [cursor]);

  const textProps = {
    x: "50%",
    y: "54%",
    textAnchor: "middle" as const,
    dominantBaseline: "middle" as const,
    strokeWidth: "0.4",
    className: "fill-transparent font-bold",
    style: { fontSize: 76, fontFamily: '"Noto Sans Devanagari", "Plus Jakarta Sans", sans-serif' },
  };

  return (
    <svg
      ref={svgRef}
      width="100%"
      height="100%"
      viewBox={viewBox}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      onMouseMove={(e) => setCursor({ x: e.clientX, y: e.clientY })}
      className="select-none"
      aria-label={text}
    >
      <defs>
        <linearGradient id={`grad-${id}`} gradientUnits="userSpaceOnUse">
          {hovered && (
            <>
              <stop offset="0%" stopColor="#f59f00" />
              <stop offset="35%" stopColor="#d9480f" />
              <stop offset="65%" stopColor="#c92a2a" />
              <stop offset="100%" stopColor="#f59f00" />
            </>
          )}
        </linearGradient>
        <motion.radialGradient
          id={`reveal-${id}`}
          gradientUnits="userSpaceOnUse"
          r="22%"
          initial={{ cx: "50%", cy: "50%" }}
          animate={mask}
          transition={{ duration: 0 }}
        >
          <stop offset="0%" stopColor="white" />
          <stop offset="100%" stopColor="black" />
        </motion.radialGradient>
        <mask id={`mask-${id}`}>
          <rect x="0" y="0" width="100%" height="100%" fill={`url(#reveal-${id})`} />
        </mask>
      </defs>
      <text {...textProps} className={`${textProps.className} stroke-line`} style={{ ...textProps.style, opacity: hovered ? 0.8 : 0 }}>
        {text}
      </text>
      <motion.text
        {...textProps}
        className={`${textProps.className} stroke-muted/50`}
        initial={{ strokeDashoffset: 1000, strokeDasharray: 1000 }}
        whileInView={{ strokeDashoffset: 0, strokeDasharray: 1000 }}
        viewport={{ once: true }}
        transition={{ duration: 4, ease: "easeInOut" }}
      >
        {text}
      </motion.text>
      <text {...textProps} stroke={`url(#grad-${id})`} strokeWidth="0.6" mask={`url(#mask-${id})`}>
        {text}
      </text>
    </svg>
  );
}
