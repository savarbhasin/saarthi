import { useState, type FormEvent } from "react";
import { ApiError, api, type Fact } from "../api";
import { Icon } from "./Icon";
import { Button, Empty, Input, Loading, Notice, SectionLabel } from "./ui";
import { useLoad } from "../useLoad";

export function MemorySection() {
  const { data: facts, error, reload } = useLoad<Fact[]>("/memory");
  const [forgotten, setForgotten] = useState<string[]>([]);
  const [text, setText] = useState("");
  const [status, setStatus] = useState<{ kind: "ok" | "error"; text: string } | null>(null);

  if (error) return <Notice kind="error">{error}</Notice>;
  if (!facts) return <Loading />;


  const shown = facts.filter((fact) => !fact.id || !forgotten.includes(fact.id));
  const editable = facts.length === 0 || facts.some((fact) => fact.id);

  async function forget(id: string) {
    setForgotten([...forgotten, id]);
    try {
      await api(`/memory/${id}`, "DELETE");
    } catch {
      setForgotten((ids) => ids.filter((x) => x !== id));
      setStatus({ kind: "error", text: "Couldn't forget that. Try again." });
    }
  }

  async function add(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/memory", "POST", { text });
      setText("");
      setStatus({ kind: "ok", text: "Saved. It shows up here in a minute or so." });
      setTimeout(() => void reload(), 20_000);
    } catch (exc) {
      setStatus({ kind: "error", text: exc instanceof ApiError ? exc.message : "Couldn't save." });
    }
  }

  return (
    <>
      <SectionLabel id="memory">What Saarthi remembers</SectionLabel>
      <p className="-mt-1 mb-4 text-muted">
        Learned from your calls. Remove anything that's wrong or private, or add something yourself.
      </p>

      {status && <Notice kind={status.kind}>{status.text}</Notice>}

      {editable && (
        <form onSubmit={add} className="mb-6 flex flex-col gap-3 sm:flex-row">
          <Input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Tell Saarthi something to remember, e.g. My daughter's name is Priya"
            aria-label="Something to remember"
            maxLength={500}
          />
          <Button icon="plus" className="shrink-0">
            Remember
          </Button>
        </form>
      )}

      {shown.length === 0 ? (
        <Empty icon="brain" title="Nothing yet">
          Saarthi learns about you as you talk to it. You can also add things above.
        </Empty>
      ) : (
        <>
          <div className="mb-3 text-sm text-muted">
            {shown.length} {shown.length === 1 ? "thing" : "things"} Saarthi remembers
          </div>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {shown.map((fact, i) => (
              <div key={fact.id ?? i} className="flex flex-col justify-between gap-4 border border-line bg-surface p-4.5">
                <p className="text-[16px] leading-relaxed">{fact.text}</p>
                {fact.id && (
                  <button
                    onClick={() => forget(fact.id!)}
                    aria-label={`Forget: ${fact.text}`}
                    className="flex cursor-pointer items-center gap-1.5 self-start px-2 py-1 -ml-2 text-[13px] font-semibold text-muted transition-colors hover:bg-bad-soft hover:text-bad"
                  >
                    <Icon name="x" className="size-4" />
                    Forget
                  </button>
                )}
              </div>
            ))}
          </div>
        </>
      )}
    </>
  );
}
