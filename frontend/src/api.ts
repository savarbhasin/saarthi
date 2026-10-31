export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly field?: string,
  ) {
    super(message);
  }
}

export async function api<T>(path: string, method = "GET", body?: unknown): Promise<T> {
  const response = await fetch(`/api/web${path}`, {
    method,
    credentials: "same-origin",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new ApiError(response.status, data.message ?? data.detail ?? "Something went wrong.", data.field);
  }
  return data as T;
}

export type Me = {
  phone: string;
  name: string;
  language: string;
  pack: string;
  occupation: string;
  custom_instructions: string;
  options: { languages: Record<string, string>; packs: Record<string, string> };
};

export type Skill = {
  id: string;
  name: string;
  description: string;
  instructions: string;
  enabled: boolean;
};

export type Connector = {
  id: string;
  name: string;
  transport: "stdio" | "http" | "sse";
  enabled: boolean;
  url: string;
  command: string;
  secret_names: string[];
};

export type Task = {
  id: string;
  goal: string;
  summary: string;
  result: string;
  state: "working" | "done" | "failed";
  created_at: string;
};

export type Routine = { id: string; text: string };

export type Fact = { id: string | null; text: string };

export type Ability = { title: string; detail: string; examples: string[] };

export type Guide = { pack: string; pack_label: string; everyone: Ability[]; profile: Ability[] };

type TaskCard = Pick<Task, "id" | "goal" | "summary" | "state" | "created_at">;

export type Home = {
  name: string;
  pack: string;
  stats: { tasks_done: number; calls_this_week: number; minutes_talked: number; people_called: number };
  working: TaskCard[];
  recent_tasks: TaskCard[];
  upcoming: Routine[];
  calls: { id: string; inbound: boolean; seconds: number; created_at: string }[];
  outreach: { id: string; name: string; status: string; note: string; created_at: string }[];
};
