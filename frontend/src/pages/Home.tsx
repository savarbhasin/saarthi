import { Link } from "react-router-dom";
import type { Home as HomeData } from "../api";
import { Badge, Item, Loading, Notice, Panel, PanelEmpty } from "../components/ui";
import { duration, when } from "../format";
import { useLoad } from "../useLoad";

const STATS: [keyof HomeData["stats"], string, string | null][] = [
  ["tasks_done", "Tasks done", "/tasks"],
  ["calls_this_week", "Calls this week", null],
  ["minutes_talked", "Minutes talked", null],
  ["people_called", "People called for you", null],
];

const OUTREACH: Record<string, { label: string; kind?: "ok" | "warn" | "bad" }> = {
  queued: { label: "Queued", kind: "warn" },
  calling: { label: "Calling", kind: "warn" },
  done: { label: "Talked", kind: "ok" },
  no_answer: { label: "No answer" },
  failed: { label: "Failed", kind: "bad" },
};

const STAT = "block border border-line bg-surface px-4.5 py-3.5 text-fg no-underline";
const itemSub = "mt-0.5 text-sm text-muted";
const meta = "mt-0.5 text-[13px] text-muted";

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <>
      <b className="block text-3xl leading-none font-bold">{value}</b>
      <span className="mt-1.5 block text-[13px] font-medium text-muted">{label}</span>
    </>
  );
}

export function Home() {
  const { data: home, error } = useLoad<HomeData>("/home");
  if (error) return <Notice kind="error">{error}</Notice>;
  if (!home) return <Loading />;

  const [working, ...moreWorking] = home.working;

  return (
    // On desktop the whole page fits the screen: panels share the leftover height and scroll inside.
    <div className="flex flex-col md:h-[calc(100dvh-4.5rem)]">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-[30px] leading-tight font-bold tracking-tight">नमस्ते, {home.name || "दोस्त"}</h1>
          <p className="mt-1 text-muted">Here's what Saarthi has been up to for you.</p>
        </div>
        {working && (
          <Link
            to="/tasks"
            className="flex max-w-lg min-w-0 items-center gap-3 bg-warn-soft px-4 py-3 text-warn no-underline"
          >
            <span className="size-2 shrink-0 animate-pulse bg-warn" />
            <span className="min-w-0 truncate">
              <b>Working on it:</b> {working.goal}
            </span>
            {moreWorking.length > 0 && <span className="shrink-0 font-semibold">+{moreWorking.length}</span>}
          </Link>
        )}
      </div>

      <div className="mb-5 grid shrink-0 grid-cols-2 gap-3 lg:grid-cols-4">
        {STATS.map(([key, label, to]) =>
          to ? (
            <Link key={key} to={to} className={`${STAT} transition-colors hover:border-accent`}>
              <Stat value={home.stats[key]} label={label} />
            </Link>
          ) : (
            <div key={key} className={STAT}>
              <Stat value={home.stats[key]} label={label} />
            </div>
          ),
        )}
      </div>

      <div className="grid gap-4 md:min-h-0 md:flex-1 md:grid-cols-2 md:grid-rows-2">
        <Panel icon="tasks" title="Recent tasks" more="/tasks">
          {home.recent_tasks.length === 0 && <PanelEmpty>Nothing yet. Ask Saarthi on a call.</PanelEmpty>}
          {home.recent_tasks.map((task) => (
            <Item key={task.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="font-semibold">{task.goal}</div>
                <Badge kind={task.state === "done" ? "ok" : "bad"}>{task.state === "done" ? "Done" : "Failed"}</Badge>
              </div>
              {task.summary && <div className={itemSub}>{task.summary}</div>}
              <div className={meta}>{when(task.created_at)}</div>
            </Item>
          ))}
        </Panel>

        <Panel icon="calendar" title="Coming up" more="/schedule">
          {home.upcoming.length === 0 && <PanelEmpty>No reminders or scheduled jobs.</PanelEmpty>}
          {home.upcoming.map((routine) => (
            <Item key={routine.id}>{routine.text}</Item>
          ))}
        </Panel>


        <Panel icon="phone" title="Recent calls">
          {home.calls.length === 0 && <PanelEmpty>No calls yet.</PanelEmpty>}
          {home.calls.map((call) => (
            <Item key={call.id}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-semibold">{call.inbound ? "You called Saarthi" : "Saarthi called you"}</div>
                  <div className={meta}>{when(call.created_at)}</div>
                </div>
                <span className="text-sm text-muted tabular-nums">{duration(call.seconds)}</span>
              </div>
            </Item>
          ))}
        </Panel>

        <Panel icon="people" title="People Saarthi called for you">
          {home.outreach.length === 0 && (
            <PanelEmpty>Ask Saarthi to phone someone, like everyone who owes you money.</PanelEmpty>
          )}
          {home.outreach.map((call) => (
            <Item key={call.id}>
              <div className="flex items-start justify-between gap-3">
                <div className="font-semibold">{call.name}</div>
                <Badge kind={OUTREACH[call.status]?.kind}>{OUTREACH[call.status]?.label ?? call.status}</Badge>
              </div>
              {call.note && <div className={itemSub}>{call.note}</div>}
              <div className={meta}>{when(call.created_at)}</div>
            </Item>
          ))}
        </Panel>
      </div>
    </div>
  );
}
