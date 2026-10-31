import { useEffect, useState, type FormEvent } from "react";
import { ApiError, api, type Me } from "../api";
import { Button, Hero, Input, Label, Loading, Notice, SectionLabel, Select, Textarea } from "../components/ui";
import { MemorySection } from "../components/MemorySection";
import { useLoad } from "../useLoad";

type Form = Pick<Me, "name" | "language" | "pack" | "occupation" | "custom_instructions">;

const sectionSub = "-mt-1 mb-3 text-muted";

export function Profile() {
  const { data: me, error: loadError } = useLoad<Me>("/me");
  const [form, setForm] = useState<Form | null>(null);
  const [status, setStatus] = useState<{ kind: "ok" | "error"; text: string } | null>(null);

  useEffect(() => {
    if (me) setForm(me);
  }, [me]);

  if (loadError) return <Notice kind="error">{loadError}</Notice>;
  if (!me || !form) return <Loading />;

  const set = (field: keyof Form) => (event: { target: { value: string } }) =>
    setForm({ ...form, [field]: event.target.value });

  async function save(event: FormEvent) {
    event.preventDefault();
    try {
      await api("/me", "PUT", form);
      setStatus({ kind: "ok", text: "Saved. Saarthi uses this from your next call." });
    } catch (exc) {
      setStatus({ kind: "error", text: exc instanceof ApiError ? exc.message : "Couldn't save." });
    }
  }

  return (
    <>
      <Hero icon="user" title="You" lede="Your details, how Saarthi should work for you, and what it remembers." />
      {status && <Notice kind={status.kind}>{status.text}</Notice>}

      <form onSubmit={save}>
        <div className="flex items-start justify-between gap-4">
          <div>
            <SectionLabel first>About you</SectionLabel>
            <p className={sectionSub}>Saarthi greets you and picks its know-how from this.</p>
          </div>
          <Button icon="check" className="shrink-0">
            Save
          </Button>
        </div>
        <div className="grid gap-x-5 sm:grid-cols-2">
          <div>
            <Label htmlFor="name">Name</Label>
            <Input id="name" value={form.name} onChange={set("name")} required />
          </div>
          <div>
            <Label htmlFor="language">Language Saarthi starts in</Label>
            <Select id="language" value={form.language} onChange={set("language")}>
              {Object.entries(me.options.languages).map(([code, label]) => (
                <option key={code} value={code}>
                  {label}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="occupation">Your work</Label>
            <Input id="occupation" value={form.occupation} onChange={set("occupation")} placeholder="e.g. फल बेचता हूँ" />
          </div>
          <div>
            <Label htmlFor="pack" hint="extra know-how for your work">
              Profile
            </Label>
            <Select id="pack" value={form.pack} onChange={set("pack")}>
              {Object.entries(me.options.packs).map(([name, label]) => (
                <option key={name} value={name}>
                  {label}
                </option>
              ))}
            </Select>
          </div>
        </div>

        <SectionLabel>Instructions for Saarthi</SectionLabel>
        <p className={sectionSub}>
          Followed on every call and every task. Put anything Saarthi should always know here, like your UPI ID for
          people paying you.
        </p>
        <Textarea
          aria-label="Instructions for Saarthi"
          rows={6}
          maxLength={4000}
          value={form.custom_instructions}
          onChange={set("custom_instructions")}
          placeholder={"My UPI ID is ramesh@okaxis.\nAlways give prices for Azadpur mandi.\nKeep answers very short."}
        />

      </form>
      <MemorySection />
    </>
  );
}
