import { useState, type FormEvent } from "react";
import { ApiError, api, type Skill } from "../api";
import { Icon } from "../components/Icon";
import { Badge, Button, Empty, Hero, Input, Label, Loading, Modal, Notice, Pre, Textarea } from "../components/ui";
import { useLoad } from "../useLoad";

const BLANK = { name: "", description: "", instructions: "" };
type Form = typeof BLANK;

function SkillForm({ initial, editing, onDone }: { initial: Form; editing: boolean; onDone: (saved: boolean) => void }) {
  const [form, setForm] = useState(initial);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const set = (field: keyof Form) => (event: { target: { value: string } }) =>
    setForm({ ...form, [field]: event.target.value });

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await api("/skills", "POST", form);
      onDone(true);
    } catch (exc) {
      setError(exc instanceof ApiError ? exc.message : "Couldn't save.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save}>
      {error && <Notice kind="error">{error}</Notice>}
      <Label htmlFor="name" hint="lowercase, e.g. weekly-report" first>
        Name
      </Label>
      <Input id="name" mono value={form.name} onChange={set("name")} readOnly={editing} required autoFocus={!editing} />
      <Label htmlFor="description" hint="Saarthi reads this to decide when to use it">
        When to use it
      </Label>
      <Input
        id="description"
        value={form.description}
        onChange={set("description")}
        placeholder="When I ask for my weekly sales report"
        required
        autoFocus={editing}
      />
      <Label htmlFor="instructions" hint="plain words or markdown">
        Steps
      </Label>
      <Textarea
        id="instructions"
        mono
        rows={10}
        value={form.instructions}
        onChange={set("instructions")}
        placeholder={
          "1. Read ~/files/khata.csv\n2. Total udhaar and payments for the last 7 days\n3. Name the three people who owe the most"
        }
        required
      />
      <div className="mt-5 flex justify-end gap-2.5">
        <Button type="button" variant="quiet" onClick={() => onDone(false)}>
          Cancel
        </Button>
        <Button icon="check" disabled={busy}>
          {editing ? "Save changes" : "Add skill"}
        </Button>
      </div>
    </form>
  );
}

export function Skills() {
  const { data: skills, error: loadError, reload } = useLoad<Skill[]>("/skills");
  const [openId, setOpenId] = useState<string | null>(null);
  // null: closed; otherwise the form's starting values and whether it edits an existing skill.
  const [modal, setModal] = useState<{ initial: Form; editing: boolean } | null>(null);

  if (loadError) return <Notice kind="error">{loadError}</Notice>;
  if (!skills) return <Loading />;

  async function toggle(skill: Skill) {
    await api(`/skills/${skill.id}`, "PATCH", { enabled: !skill.enabled });
    await reload();
  }

  async function remove(skill: Skill) {
    if (!confirm(`Delete ${skill.name}?`)) return;
    await api(`/skills/${skill.id}`, "DELETE");
    await reload();
  }

  async function closeModal(saved: boolean) {
    setModal(null);
    if (saved) await reload();
  }

  const addButton = (
    <Button icon="plus" onClick={() => setModal({ initial: BLANK, editing: false })}>
      Add skill
    </Button>
  );

  return (
    <>
      <Hero
        icon="skill"
        title="Skills"
        lede="Teach your worker how you like things done. When a task matches a skill, it follows your steps."
        action={addButton}
      />

      {skills.map((skill) => {
        const open = openId === skill.id;
        const toggleOpen = () => setOpenId(open ? null : skill.id);
        return (
          <div
            key={skill.id}
            role="button"
            tabIndex={0}
            aria-expanded={open}
            onClick={toggleOpen}
            onKeyDown={(e) => e.target === e.currentTarget && (e.key === "Enter" || e.key === " ") && (e.preventDefault(), toggleOpen())}
            className="mb-3 cursor-pointer border border-line bg-surface px-5 py-4.5 transition-colors hover:bg-soft focus-visible:bg-soft focus-visible:outline-none"
          >
            <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <strong className="font-mono">{skill.name}</strong>
                  <Badge kind={skill.enabled ? "ok" : undefined}>{skill.enabled ? "On" : "Off"}</Badge>
                </div>
                <div className="mt-1 text-sm text-muted">{skill.description}</div>
                <div className="mt-2 flex items-center gap-1 text-[13px] font-medium text-muted">
                  {open ? "Hide steps" : "Show steps"}
                  <Icon name="chevron" className={`size-4 transition-transform ${open ? "rotate-180" : ""}`} />
                </div>
              </div>
              {/* The buttons act on the skill; they shouldn't also open or close it. */}
              <div className="flex shrink-0 flex-wrap gap-2" onClick={(e) => e.stopPropagation()}>
                <Button small variant="quiet" onClick={() => setModal({ initial: skill, editing: true })}>
                  Edit
                </Button>
                <Button small variant="quiet" onClick={() => toggle(skill)}>
                  {skill.enabled ? "Turn off" : "Turn on"}
                </Button>
                <Button small variant="danger" onClick={() => remove(skill)}>
                  Delete
                </Button>
              </div>
            </div>
            {open && (
              <div onClick={(e) => e.stopPropagation()} className="cursor-text">
                <Pre>{skill.instructions}</Pre>
              </div>
            )}
          </div>
        );
      })}

      {skills.length === 0 && (
        <Empty icon="skill" title="No skills yet">
          <span>Add one, e.g. how to put together your weekly sales report.</span>
          <span className="mt-4">{addButton}</span>
        </Empty>
      )}

      {modal && (
        <Modal title={modal.editing ? `Edit ${modal.initial.name}` : "Add a skill"} onClose={() => void closeModal(false)}>
          <SkillForm
            initial={{ name: modal.initial.name, description: modal.initial.description, instructions: modal.initial.instructions }}
            editing={modal.editing}
            onDone={(saved) => void closeModal(saved)}
          />
        </Modal>
      )}
    </>
  );
}
