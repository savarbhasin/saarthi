import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { api, type Me } from "../api";
import { useLoad } from "../useLoad";
import { Icon, type IconName } from "./Icon";

const LINKS: [string, string, IconName][] = [
  ["/", "Home", "home"],
  ["/you", "You", "user"],
  ["/skills", "Skills", "skill"],
  ["/connectors", "Connectors", "plug"],
  ["/tasks", "Tasks", "tasks"],
  ["/schedule", "Schedule", "calendar"],
  ["/guide", "Guide", "bolt"],
];

const link = (active: boolean) =>
  [
    "flex items-center gap-3 px-3 py-2 text-[15px] font-semibold whitespace-nowrap no-underline transition-colors",
    active ? "bg-accent-soft text-accent" : "text-muted hover:bg-soft hover:text-fg",
  ].join(" ");

export function Layout() {
  const navigate = useNavigate();
  // Also the sign-in guard: a 401 here sends the user to /login.
  const { data: me } = useLoad<Me>("/me");

  async function signOut() {
    await api("/logout", "POST");
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen md:grid md:grid-cols-[240px_minmax(0,1fr)]">
      {/* On phones this is a fixed-height top bar; sticky page headers sit just below it (top-14). */}
      <aside className="sticky top-0 z-10 flex h-14 items-center border-b border-line bg-surface md:h-screen md:flex-col md:items-stretch md:border-r md:border-b-0">
        <NavLink
          to="/"
          className="block shrink-0 px-4 py-3 text-lg font-bold whitespace-nowrap text-fg no-underline md:px-5 md:pt-6 md:pb-5 md:text-[22px]"
        >
          सारथी <span className="text-accent max-[460px]:hidden">Saarthi</span>
        </NavLink>

        <nav className="flex flex-1 gap-1 overflow-x-auto px-2 py-2 [scrollbar-width:none] md:flex-col md:px-3 md:py-1">
          {LINKS.map(([to, label, icon]) => (
            <NavLink key={to} to={to} end title={label} className={({ isActive }) => link(isActive)}>
              {({ isActive }) => (
                <>
                  <Icon name={icon} />
                  <span className={isActive ? "" : "max-md:hidden"}>{label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <div className="flex items-center gap-2 border-line px-2 md:border-t md:p-4">
          <div className="hidden min-w-0 flex-1 text-[13px] text-muted md:block">
            <b className="block truncate text-sm text-fg">{me?.name || "…"}</b>
            {me?.phone}
          </div>
          <button
            onClick={signOut}
            title="Sign out"
            aria-label="Sign out"
            className="cursor-pointer p-2 text-muted transition-colors hover:bg-soft hover:text-fg"
          >
            <Icon name="logout" />
          </button>
        </div>
      </aside>

      <main className="mx-auto w-full max-w-[1440px] min-w-0 px-4 pt-6 pb-20 md:px-10 md:py-9">
        <Outlet />
      </main>
    </div>
  );
}
