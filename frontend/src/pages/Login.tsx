import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api";
import { Icon, type IconName } from "../components/Icon";
import { Button, Card, Input, Label, Notice } from "../components/ui";

type Sent = { phone: string; dev_code?: string };

const FEATURES: [IconName, string][] = [
  ["skill", "Write skills your worker follows"],
  ["plug", "Plug in any MCP server"],
  ["tasks", "See every task and its full result"],
];

export function Login() {
  const navigate = useNavigate();
  const [phone, setPhone] = useState("");
  const [code, setCode] = useState("");
  const [sent, setSent] = useState<Sent | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await action();
    } catch (exc) {
      setError(exc instanceof ApiError ? exc.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const sendCode = (event: FormEvent) => {
    event.preventDefault();
    void run(async () => setSent(await api<Sent>("/login", "POST", { phone })));
  };

  const verify = (event: FormEvent) => {
    event.preventDefault();
    void run(async () => {
      await api("/login/verify", "POST", { phone: sent!.phone, code });
      navigate("/", { replace: true });
    });
  };

  return (
    <div className="grid min-h-screen place-items-center bg-canvas px-4 py-6">
      <div className="w-full max-w-[440px]">
        <div className="mb-5 text-[26px] font-bold">
          सारथी <span className="text-accent">Saarthi</span>
        </div>

        {sent === null ? (
          <>
            <h1 className="text-[28px] leading-tight font-bold tracking-tight">Make Saarthi yours</h1>
            <p className="mt-2 mb-6 text-muted">Teach it skills, connect your apps, and see everything it's done for you.</p>
            {error && <Notice kind="error">{error}</Notice>}
            <form onSubmit={sendCode}>
              <Card className="p-6">
                <Label htmlFor="phone" hint="the one you call Saarthi from" first>
                  Your phone number
                </Label>
                <Input
                  id="phone"
                  type="tel"
                  inputMode="tel"
                  placeholder="98765 43210"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  required
                  autoFocus
                />
                <Button icon="phone" disabled={busy} className="mt-5 w-full">
                  {busy ? "Calling…" : "Call me with a code"}
                </Button>
              </Card>
            </form>
            <div className="mt-6 grid gap-2.5">
              {FEATURES.map(([icon, text]) => (
                <div key={icon} className="flex items-center gap-2.5 text-muted">
                  <span className="text-accent">
                    <Icon name={icon} />
                  </span>
                  {text}
                </div>
              ))}
            </div>
          </>
        ) : (
          <>
            <h1 className="text-[28px] leading-tight font-bold tracking-tight">Pick up the phone</h1>
            {sent.dev_code ? (
              <>
                <p className="mt-2 mb-6 text-muted">Local dev mode: no call was made.</p>
                <Notice kind="info">
                  Your code is <strong className="font-mono">{sent.dev_code}</strong>
                </Notice>
              </>
            ) : (
              <p className="mt-2 mb-6 text-muted">Saarthi is calling {sent.phone} and will read out a 6-digit code.</p>
            )}
            {error && <Notice kind="error">{error}</Notice>}
            <form onSubmit={verify}>
              <Card className="p-6">
                <Label htmlFor="code" first>
                  Code
                </Label>
                <Input
                  id="code"
                  className="text-center text-2xl font-bold tracking-[0.4em]"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={6}
                  pattern="[0-9]{6}"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
                  required
                  autoFocus
                />
                <Button disabled={busy} className="mt-5 w-full">
                  Sign in
                </Button>
              </Card>
            </form>
            <button
              className="cursor-pointer font-semibold text-accent hover:underline"
              onClick={() => (setSent(null), setCode(""), setError(""))}
            >
              Use a different number
            </button>
          </>
        )}
      </div>
    </div>
  );
}
