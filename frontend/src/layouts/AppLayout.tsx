import type { ReactNode } from "react";
import { Activity, Film, History, Home, Settings, Tv, VolumeX } from "lucide-react";
import { NavLink } from "react-router-dom";

import { useI18n } from "../i18n/I18nProvider";
import { cn } from "../utils/cn";

const navigationItems = [
  { to: "/", icon: Home, label: "nav.dashboard" },
  { to: "/missing", icon: VolumeX, label: "nav.missing" },
  { to: "/movies", icon: Film, label: "nav.movies" },
  { to: "/series", icon: Tv, label: "nav.series" },
  { to: "/history", icon: History, label: "nav.history" },
  { to: "/settings", icon: Settings, label: "nav.settings" },
] as const;

export function AppLayout({ children }: { children: ReactNode }) {
  const { t } = useI18n();

  return (
    <div className="min-h-screen bg-muted text-foreground">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r border-border bg-background md:flex md:flex-col">
        <div className="flex h-16 items-center gap-3 border-b border-border px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity aria-hidden="true" size={20} />
          </div>
          <div>
            <p className="text-sm font-semibold">{t("app.name")}</p>
            <p className="text-xs text-muted-foreground">Audio audit</p>
          </div>
        </div>
        <nav className="flex-1 space-y-1 p-3" aria-label="Primary">
          {navigationItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === "/"}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground",
                )
              }
            >
              <item.icon aria-hidden="true" size={18} />
              {t(item.label)}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="md:pl-64">
        <header className="sticky top-0 z-10 border-b border-border bg-background/95 px-4 py-3 backdrop-blur md:hidden">
          <div className="flex items-center justify-between">
            <span className="font-semibold">{t("app.name")}</span>
            <nav className="flex gap-1" aria-label="Mobile">
              {navigationItems.slice(0, 4).map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  end={item.to === "/"}
                  className={({ isActive }) =>
                    cn(
                      "rounded-md p-2 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary",
                      isActive ? "bg-primary text-primary-foreground" : "text-muted-foreground",
                    )
                  }
                  title={t(item.label)}
                >
                  <item.icon aria-hidden="true" size={18} />
                  <span className="sr-only">{t(item.label)}</span>
                </NavLink>
              ))}
            </nav>
          </div>
        </header>
        <main className="mx-auto min-h-screen max-w-7xl px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
