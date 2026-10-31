import { useMemo, useState } from "react";
import type { Task } from "../api";
import { Icon } from "../components/Icon";
import { Badge, Empty, Hero, Loading, Notice, Pre } from "../components/ui";
import { dayLabel, time } from "../format";
import { useLoad } from "../useLoad";

type Filter = "all" | Task["state"];

const STATE = {
  working: { badge: "warn", label: "Working" },
  done: { badge: "ok", label: "Done" },
  failed: { badge: "bad", label: "Failed" },
} as const;

const FILTERS: [Filter, string][] = [
  ["all", "All"],
  ["working", "Working"],
  ["done", "Done"],
  ["failed", "Failed"],
];

function matches(task: Task, words: string[]) {
  const text = `${task.goal} ${task.summary} ${task.result}`.toLowerCase();
  return words.every((word) => text.includes(word));
}

function groupByDay(tasks: Task[]) {
  const groups: [string, Task[]][] = [];
  for (const task of tasks) {
    const label = dayLabel(task.created_at);
    const last = groups[groups.length - 1];
    if (last && last[0] === label) last[1].push(task);
    else groups.push([label, [task]]);
  }
  return groups;
}

function TaskRow({ task }: { task: Task }) {
  const [open, setOpen] = useState(false);
  const expandable = Boolean(task.result);
  const toggle = () => expandable && setOpen(!open);

  return (
    <article
      role={expandable ? "button" : undefined}
      tabIndex={expandable ? 0 : undefined}
      aria-expanded={expandable ? open : undefined}
      onClick={toggle}
      onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && (e.preventDefault(), toggle())}
      className={`border-b border-line px-5 py-4 last:border-b-0 ${
        expandable ? "cursor-pointer transition-colors hover:bg-soft focus-visible:bg-soft focus-visible:outline-none" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0 flex-1">
          <div className="text-[15px] leading-snug text-muted">{task.goal}</div>
          {task.summary && <div className="mt-1.5 text-[16px] leading-relaxed">{task.summary}</div>}
        </div>
        <div className="flex shrink-0 flex-col items-end gap-1.5">
          <Badge kind={STATE[task.state].badge}>{STATE[task.state].label}</Badge>
          <span className="text-[13px] text-muted tabular-nums">{time(task.created_at)}</span>
        </div>
      </div>
      {expandable && (
        <div className="mt-2 flex items-center gap-1 text-[13px] font-medium text-muted">
          {open ? "Hide details" : "Show details"}
          <Icon name="chevron" className={`size-4 transition-transform ${open ? "rotate-180" : ""}`} />
        </div>
      )}
      {open && (
        // Selecting or copying the result shouldn't collapse it.
        <div onClick={(e) => e.stopPropagation()} className="cursor-text">
          <Pre>{task.result}</Pre>
        </div>
      )}
    </article>
  );
}

export function Tasks() {
  const { data: tasks, error } = useLoad<Task[]>("/tasks");
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<Filter>("all");

  const searched = useMemo(() => {
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    return (tasks ?? []).filter((task) => matches(task, words));
  }, [tasks, query]);

  if (error) return <Notice kind="error">{error}</Notice>;
  if (!tasks) return <Loading />;

  const count = (f: Filter) => (f === "all" ? searched.length : searched.filter((t) => t.state === f).length);
  const shown = filter === "all" ? searched : searched.filter((t) => t.state === filter);

  return (
    <>
      {/* Stays put while the list scrolls; the negative margins cover main's padding. */}
      <div className="sticky top-14 z-[5] -mx-4 -mt-6 mb-5 bg-canvas px-4 pt-6 pb-4 md:top-0 md:-mx-10 md:-mt-9 md:px-10 md:pt-9">
        <Hero icon="tasks" title="Tasks" lede="Everything you've asked Saarthi to do, newest first." />

        <div className="-mt-5 flex flex-col gap-3 sm:flex-row sm:items-center">
          <label className="flex flex-1 items-center gap-2.5 border border-line bg-surface px-3 focus-within:border-accent">
            <span className="text-muted">
              <Icon name="search" />
            </span>
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search tasks and results"
              aria-label="Search tasks"
              className="w-full bg-transparent py-2.5 text-[15px] outline-none placeholder:text-muted/70"
            />
          </label>
          <div className="flex border border-line bg-surface" role="tablist" aria-label="Filter by status">
            {FILTERS.map(([value, label]) => (
              <button
                key={value}
                role="tab"
                aria-selected={filter === value}
                onClick={() => setFilter(value)}
                className={`flex-1 cursor-pointer border-r border-line px-3.5 py-2.5 text-sm font-semibold whitespace-nowrap transition-colors last:border-r-0 ${
                  filter === value ? "bg-accent-soft text-accent" : "text-muted hover:bg-soft hover:text-fg"
                }`}
              >
                {label} <span className="ml-1 font-normal tabular-nums opacity-75">{count(value)}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {tasks.length === 0 && (
        <Empty icon="tasks" title="No tasks yet">
          Call Saarthi and ask for anything.
        </Empty>
      )}
      {tasks.length > 0 && shown.length === 0 && (
        <Empty icon="search" title="Nothing matches">
          Try other words, or a different status.
        </Empty>
      )}

      {groupByDay(shown).map(([day, group]) => (
        <section key={day} className="mb-6">
          <h2 className="mb-2 text-xs font-semibold tracking-[0.08em] text-muted uppercase">{day}</h2>
          <div className="border border-line bg-surface">
            {group.map((task) => (
              <TaskRow key={task.id} task={task} />
            ))}
          </div>
        </section>
      ))}
    </>
  );
}
