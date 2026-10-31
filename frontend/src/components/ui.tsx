import {
  useEffect,
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  type SelectHTMLAttributes,
  type TextareaHTMLAttributes,
} from "react";
import { Link } from "react-router-dom";
import { Icon, type IconName } from "./Icon";

const cx = (...classes: (string | false | undefined)[]) => classes.filter(Boolean).join(" ");

const BUTTON = {
  primary: "border-accent bg-accent text-accent-fg hover:brightness-105",
  quiet: "border-line bg-surface text-fg hover:bg-soft",
  danger: "border-line bg-surface text-bad hover:bg-bad-soft",
};

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: keyof typeof BUTTON;
  small?: boolean;
  icon?: IconName;
};

export function Button({ variant = "primary", small, icon, className, children, ...props }: ButtonProps) {
  return (
    <button
      className={cx(
        "inline-flex cursor-pointer items-center justify-center gap-2 border font-semibold transition-colors disabled:cursor-wait disabled:opacity-60",
        small ? "px-3 py-1.5 text-sm" : "px-4.5 py-2.5 text-[15px]",
        BUTTON[variant],
        className,
      )}
      {...props}
    >
      {icon && <Icon name={icon} />}
      {children}
    </button>
  );
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cx("mb-3 border border-line bg-surface px-5 py-4.5", className)}>{children}</div>;
}

export function Hero({ icon, title, lede, action }: { icon: IconName; title: string; lede: string; action?: ReactNode }) {
  return (
    <div className="mb-10 flex flex-col gap-4 sm:flex-row sm:items-center">
      <div className="flex flex-1 items-center gap-4">
        <div className="grid size-12 shrink-0 place-items-center bg-accent-soft text-accent">
          <Icon name={icon} className="size-6" />
        </div>
        <div>
          <h1 className="text-[26px] leading-tight font-bold tracking-tight">{title}</h1>
          <p className="mt-0.5 text-muted">{lede}</p>
        </div>
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

export function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/50 px-4 py-10 sm:py-16"
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div role="dialog" aria-modal="true" aria-label={title} className="w-full max-w-2xl border border-line bg-surface">
        <div className="flex items-center justify-between border-b border-line px-5 py-3.5">
          <h2 className="text-lg font-bold">{title}</h2>
          <button
            onClick={onClose}
            aria-label="Close"
            className="cursor-pointer p-1.5 text-muted transition-colors hover:bg-soft hover:text-fg"
          >
            <Icon name="x" />
          </button>
        </div>
        <div className="px-5 py-5">{children}</div>
      </div>
    </div>
  );
}

export function SectionLabel({ id, first, children }: { id?: string; first?: boolean; children: ReactNode }) {
  return (
    <h2 id={id} className={cx("mb-3 text-xs font-semibold tracking-[0.08em] text-muted uppercase", first ? "mt-0" : "mt-10")}>
      {children}
    </h2>
  );
}

export function Panel(props: { icon: IconName; title: string; more?: string; wide?: boolean; children: ReactNode }) {
  return (
    <section className={cx("flex min-h-0 flex-col border border-line bg-surface", props.wide && "lg:col-span-2")}>
      <div className="flex items-center gap-2 border-b border-line px-4.5 py-3 text-sm font-semibold">
        <span className="text-accent">
          <Icon name={props.icon} className="size-4" />
        </span>
        {props.title}
        {props.more && (
          <Link to={props.more} className="ml-auto text-sm font-medium text-accent no-underline hover:underline">
            See all
          </Link>
        )}
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto px-4.5 py-1">{props.children}</div>
    </section>
  );
}

export function PanelEmpty({ children }: { children: ReactNode }) {
  return <div className="py-4 text-sm text-muted">{children}</div>;
}

export function Item({ children }: { children: ReactNode }) {
  return <div className="border-b border-line py-3 last:border-b-0">{children}</div>;
}

const NOTICE = { ok: "bg-ok-soft text-ok", error: "bg-bad-soft text-bad", info: "border border-line bg-surface" };

export function Notice({ kind, children }: { kind: keyof typeof NOTICE; children: ReactNode }) {
  return (
    <div className={cx("mb-4 flex items-center gap-2.5 px-4 py-3 text-[15px]", NOTICE[kind])}>
      {kind !== "info" && <Icon name={kind === "ok" ? "check" : "alert"} />}
      <span>{children}</span>
    </div>
  );
}

export function Empty({ icon, title, children }: { icon: IconName; title: string; children: ReactNode }) {
  return (
    <div className="mb-3 flex flex-col items-center border border-dashed border-line px-5 py-10 text-center text-muted">
      <Icon name={icon} className="mb-2 size-7 text-accent" />
      <strong className="mb-0.5 text-fg">{title}</strong>
      {children}
    </div>
  );
}

const BADGE = { ok: "bg-ok-soft text-ok", warn: "bg-warn-soft text-warn", bad: "bg-bad-soft text-bad" };

export function Badge({ kind, children }: { kind?: keyof typeof BADGE; children: ReactNode }) {
  return (
    <span
      className={cx(
        "inline-flex items-center px-2 py-0.5 text-xs font-semibold whitespace-nowrap",
        kind ? BADGE[kind] : "bg-soft text-muted",
      )}
    >
      {children}
    </span>
  );
}

export function Loading() {
  return <div aria-label="Loading" className="mx-auto my-24 size-7 animate-spin border-3 border-line border-t-accent" />;
}

export function Label({ htmlFor, hint, first, children }: { htmlFor: string; hint?: string; first?: boolean; children: ReactNode }) {
  return (
    <label htmlFor={htmlFor} className={cx("mb-1.5 block text-sm font-semibold", first ? "mt-0" : "mt-4")}>
      {children}
      {hint && <span className="ml-1.5 text-[13px] font-normal text-muted">{hint}</span>}
    </label>
  );
}

const FIELD =
  "w-full border border-line bg-canvas px-3 py-2.5 text-[15px] text-fg transition-colors placeholder:text-muted/70 read-only:text-muted focus:border-accent focus:outline-none";

export function Input({ mono, className, ...props }: InputHTMLAttributes<HTMLInputElement> & { mono?: boolean }) {
  return <input className={cx(FIELD, mono && "font-mono text-sm", className)} {...props} />;
}

export function Select(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={FIELD} {...props} />;
}

export function Textarea({ mono, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { mono?: boolean }) {
  return <textarea className={cx(FIELD, "min-h-30 resize-y", mono && "font-mono text-sm")} {...props} />;
}

export function Pre({ children }: { children: ReactNode }) {
  return <pre className="mt-2.5 bg-canvas px-3.5 py-3 font-mono text-[13px] break-words whitespace-pre-wrap">{children}</pre>;
}
