// Adapted from Aceternity UI's Terminal, without the key sounds: types each command, then prints
// its output, once it scrolls into view.
import { useEffect, useMemo, useRef, useState } from "react";
import { useInView } from "motion/react";
import { cn } from "./cn";

type TokenType = "command" | "flag" | "string" | "number" | "path" | "comment" | "default";

function tokenize(text: string) {
  let first = true;
  return text.split(/(\s+)/).map((word): { type: TokenType; value: string } => {
    if (/^\s+$/.test(word)) return { type: "default", value: word };
    if (word.startsWith("#")) return { type: "comment", value: word };
    const type: TokenType = word.startsWith("-")
      ? "flag"
      : /^["'].*["']$/.test(word)
        ? "string"
        : /^\d+$/.test(word)
          ? "number"
          : /[/~]/.test(word) || word.startsWith(".")
            ? "path"
            : first
              ? "command"
              : "default";
    first = false;
    return { type, value: word };
  });
}

const COLORS: Record<TokenType, string> = {
  command: "text-[#ff8a4c]",
  flag: "text-[#f59f00]",
  string: "text-[#a9e34b]",
  number: "text-[#ffd8a8]",
  path: "text-[#ffc078]",
  comment: "text-[#7d7468]",
  default: "text-[#e9e2d6]",
};

export function Terminal({
  commands,
  outputs = {},
  username = "saarthi",
  title,
  className,
  typingSpeed = 38,
  delayBetweenCommands = 700,
  initialDelay = 400,
}: {
  commands: string[];
  outputs?: Record<number, string[]>;
  username?: string;
  title?: string;
  className?: string;
  typingSpeed?: number;
  delayBetweenCommands?: number;
  initialDelay?: number;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const inView = useInView(containerRef, { once: true });

  const [lines, setLines] = useState<{ type: "command" | "output"; content: string }[]>([]);
  const [typed, setTyped] = useState("");
  const [commandIdx, setCommandIdx] = useState(0);
  const [charIdx, setCharIdx] = useState(0);
  const [outputIdx, setOutputIdx] = useState(-1);
  const [phase, setPhase] = useState<"idle" | "typing" | "executing" | "outputting" | "pausing" | "done">("idle");
  const [cursor, setCursor] = useState(true);

  const command = commands[commandIdx] || "";
  const output = useMemo(() => outputs[commandIdx] || [], [outputs, commandIdx]);
  const last = commandIdx === commands.length - 1;

  useEffect(() => {
    if (!inView || phase !== "idle") return;
    const t = setTimeout(() => setPhase("typing"), initialDelay);
    return () => clearTimeout(t);
  }, [inView, phase, initialDelay]);

  useEffect(() => {
    if (phase !== "typing") return;
    if (charIdx >= command.length) {
      const t = setTimeout(() => setPhase("executing"), 120);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => {
      setTyped(command.slice(0, charIdx + 1));
      setCharIdx((c) => c + 1);
    }, typingSpeed + Math.random() * 30);
    return () => clearTimeout(t);
  }, [phase, charIdx, command, typingSpeed]);

  useEffect(() => {
    if (phase !== "executing") return;
    setLines((prev) => [...prev, { type: "command", content: command }]);
    setTyped("");
    if (output.length > 0) {
      setOutputIdx(0);
      setPhase("outputting");
    } else setPhase(last ? "done" : "pausing");
  }, [phase, command, output.length, last]);

  useEffect(() => {
    if (phase !== "outputting") return;
    if (outputIdx < output.length) {
      const t = setTimeout(() => {
        setLines((prev) => [...prev, { type: "output", content: output[outputIdx] }]);
        setOutputIdx((i) => i + 1);
      }, 160);
      return () => clearTimeout(t);
    }
    const t = setTimeout(() => setPhase(last ? "done" : "pausing"), 300);
    return () => clearTimeout(t);
  }, [phase, outputIdx, output, last]);

  useEffect(() => {
    if (phase !== "pausing") return;
    const t = setTimeout(() => {
      setCharIdx(0);
      setOutputIdx(-1);
      setCommandIdx((c) => c + 1);
      setPhase("typing");
    }, delayBetweenCommands);
    return () => clearTimeout(t);
  }, [phase, delayBetweenCommands]);

  useEffect(() => {
    const interval = setInterval(() => setCursor((v) => !v), 530);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (contentRef.current) contentRef.current.scrollTop = contentRef.current.scrollHeight;
  }, [lines, phase]);

  const prompt = (
    <span>
      <span className="text-[#ff8a4c]">{username}</span>
      <span className="text-[#7d7468]">:~$</span>{" "}
    </span>
  );

  return (
    <div ref={containerRef} className={cn("w-full font-mono text-xs", className)}>
      <div className="overflow-hidden border border-[#332e27] bg-[#1a1713]">
        <div className="flex items-center gap-2 border-b border-[#332e27] px-4 py-2.5">
          <div className="flex gap-1.5">
            <span className="size-2.5 bg-[#d9480f]" />
            <span className="size-2.5 bg-[#f59f00]" />
            <span className="size-2.5 bg-[#2b8a3e]" />
          </div>
          <span className="flex-1 truncate text-center text-[#a69d90]">{title ?? `${username} — bash`}</span>
          <span className="w-[42px]" />
        </div>
        <div ref={contentRef} className="h-72 overflow-y-auto p-4 leading-relaxed [scrollbar-width:none]">
          {lines.map((line, i) => (
            <div key={i} className="whitespace-pre-wrap">
              {line.type === "command" ? (
                <>
                  {prompt}
                  {tokenize(line.content).map((t, j) => (
                    <span key={j} className={COLORS[t.type]}>
                      {t.value}
                    </span>
                  ))}
                </>
              ) : (
                <span className="text-[#a69d90]">{line.content}</span>
              )}
            </div>
          ))}
          {phase !== "idle" && phase !== "executing" && (
            <div className="whitespace-pre-wrap">
              {prompt}
              {phase === "typing" &&
                tokenize(typed).map((t, j) => (
                  <span key={j} className={COLORS[t.type]}>
                    {t.value}
                  </span>
                ))}
              <span className={cn("ml-0.5 inline-block h-4 w-2 bg-[#e9e2d6] align-middle", phase !== "typing" && !cursor && "opacity-0")} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
