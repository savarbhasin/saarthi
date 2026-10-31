const IST = "Asia/Kolkata";

const stamp = new Intl.DateTimeFormat("en-IN", {
  day: "numeric",
  month: "short",
  hour: "numeric",
  minute: "2-digit",
  timeZone: IST,
});
const clock = new Intl.DateTimeFormat("en-IN", { hour: "numeric", minute: "2-digit", timeZone: IST });
const date = new Intl.DateTimeFormat("en-IN", { weekday: "short", day: "numeric", month: "short", timeZone: IST });
// en-CA formats as YYYY-MM-DD, which compares cleanly.
const dayKey = new Intl.DateTimeFormat("en-CA", { timeZone: IST });

export const when = (iso: string) => stamp.format(new Date(iso));
export const time = (iso: string) => clock.format(new Date(iso));

export function dayLabel(iso: string) {
  const day = dayKey.format(new Date(iso));
  const today = new Date();
  if (day === dayKey.format(today)) return "Today";
  if (day === dayKey.format(new Date(today.getTime() - 86_400_000))) return "Yesterday";
  return date.format(new Date(iso));
}

export function duration(seconds: number) {
  if (seconds < 60) return `${seconds}s`;
  return `${Math.floor(seconds / 60)}m ${seconds % 60}s`;
}
