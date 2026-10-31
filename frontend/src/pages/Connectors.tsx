import { useState, type FormEvent } from "react";
import { ApiError, api, type Connector } from "../api";
import { Badge, Button, Card, Empty, Hero, Input, Label, Loading, Modal, Notice, Select, Textarea } from "../components/ui";
import { useLoad } from "../useLoad";

const BLANK = { name: "", transport: "http", url: "", headers: "", command: "", args: "", env: "" };
type Form = typeof BLANK;

const TRANSPORTS = [
  ["http", "Remote (HTTP)"],
  ["sse", "Remote (SSE)"],
  ["stdio", "Local command"],
];

function ConnectorForm({ onDone }: { onDone: (saved: boolean) => void }) {
  const [form, setForm] = useState(BLANK);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const local = form.transport === "stdio";

  const set = (field: keyof Form) => (event: { target: { value: string } }) =>
    setForm({ ...form, [field]: event.target.value });

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await api("/connectors", "POST", form);
      onDone(true);
    } catch (exc) {
      setError(exc instanceof ApiError ? exc.message : "Couldn't connect.");
      setBusy(false);
    }
  }

  return (
    <form onSubmit={save}>
      {error && <Notice kind="error">{error}</Notice>}
      <div className="grid gap-x-5 sm:grid-cols-2">
        <div>
          <Label htmlFor="name" first>
            Name
          </Label>
          <Input id="name" mono value={form.name} onChange={set("name")} placeholder="github" required autoFocus />
        </div>
        <div>
          <Label htmlFor="transport" first>
            Type
          </Label>
          <Select id="transport" value={form.transport} onChange={set("transport")}>
            {TRANSPORTS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </Select>
        </div>
      </div>

      {local ? (
        <>
          <div className="grid gap-x-5 sm:grid-cols-2">
            <div>
              <Label htmlFor="command">Command</Label>
              <Input id="command" mono value={form.command} onChange={set("command")} placeholder="npx" />
            </div>
            <div>
              <Label htmlFor="args">Arguments</Label>
              <Input
                id="args"
                mono
                value={form.args}
                onChange={set("args")}
                placeholder="-y @modelcontextprotocol/server-memory"
              />
            </div>
          </div>
          <Label htmlFor="env" hint="one per line, KEY=value">
            Environment
          </Label>
          <Textarea id="env" mono rows={3} value={form.env} onChange={set("env")} placeholder="API_KEY=..." />
        </>
      ) : (
        <>
          <Label htmlFor="url">URL</Label>
          <Input id="url" mono value={form.url} onChange={set("url")} placeholder="https://example.com/mcp" />
          <Label htmlFor="headers" hint="one per line, Name: value">
            Headers
          </Label>
          <Textarea
            id="headers"
            mono
            rows={3}
            value={form.headers}
            onChange={set("headers")}
            placeholder="Authorization: Bearer ..."
          />
        </>
      )}

      <p className="mt-4 text-[13px] text-muted">Using an existing name replaces that connector.</p>
      <div className="mt-5 flex justify-end gap-2.5">
        <Button type="button" variant="quiet" onClick={() => onDone(false)}>
          Cancel
        </Button>
        <Button icon="plus" disabled={busy}>
          Connect
        </Button>
      </div>
    </form>
  );
}

export function Connectors() {
  const { data: servers, error: loadError, reload } = useLoad<Connector[]>("/connectors");
  const [adding, setAdding] = useState(false);

  if (loadError) return <Notice kind="error">{loadError}</Notice>;
  if (!servers) return <Loading />;

  async function toggle(server: Connector) {
    await api(`/connectors/${server.id}`, "PATCH", { enabled: !server.enabled });
    await reload();
  }

  async function remove(server: Connector) {
    if (!confirm(`Remove ${server.name}?`)) return;
    await api(`/connectors/${server.id}`, "DELETE");
    await reload();
  }

  async function closeModal(saved: boolean) {
    setAdding(false);
    if (saved) await reload();
  }

  const addButton = (
    <Button icon="plus" onClick={() => setAdding(true)}>
      Add connector
    </Button>
  );

  return (
    <>
      <Hero
        icon="plug"
        title="Connectors"
        lede="Give your worker more tools by connecting MCP servers. Local ones run inside your own computer."
        action={addButton}
      />

      {servers.map((server) => (
        <Card key={server.id}>
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <strong className="font-mono">{server.name}</strong>
                <Badge>{server.transport === "stdio" ? "Local" : server.transport.toUpperCase()}</Badge>
                <Badge kind={server.enabled ? "ok" : undefined}>{server.enabled ? "On" : "Off"}</Badge>
              </div>
              <div className="mt-1 font-mono text-sm break-words text-muted">
                {server.transport === "stdio" ? server.command : server.url}
              </div>
              {server.secret_names.length > 0 && (
                <div className="mt-1 text-[13px] text-muted">Secrets set: {server.secret_names.join(", ")}</div>
              )}
            </div>
            <div className="flex shrink-0 flex-wrap gap-2">
              <Button small variant="quiet" onClick={() => toggle(server)}>
                {server.enabled ? "Turn off" : "Turn on"}
              </Button>
              <Button small variant="danger" onClick={() => remove(server)}>
                Remove
              </Button>
            </div>
          </div>
        </Card>
      ))}

      {servers.length === 0 && (
        <Empty icon="plug" title="No connectors yet">
          <span>Your worker already has a browser, files and code. Add a connector to give it more.</span>
          <span className="mt-4">{addButton}</span>
        </Empty>
      )}

      {adding && (
        <Modal title="Add a connector" onClose={() => void closeModal(false)}>
          <ConnectorForm onDone={(saved) => void closeModal(saved)} />
        </Modal>
      )}
    </>
  );
}
