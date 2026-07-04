import { BriefcaseBusiness, FileText, Home, ShieldCheck } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../../contexts/AuthContext";
import { Button } from "../ui/Button";
import { cn } from "../../lib/utils";
import omniLogo from "../../readyomni.png";

const navItems = [
  { to: "/", label: "Khadamat", labelFr: "Services", icon: Home },
  { to: "/cases", label: "Dossierat", labelFr: "Dossiers", icon: BriefcaseBusiness },
  { to: "/upload/7f4b6c9d-7a65-4b18-b551-e94db6c49a01", label: "Watha2iq", labelFr: "Documents", icon: FileText },
  { to: "/admin", label: "Idara", labelFr: "Admin", icon: ShieldCheck }
];

/** Primary responsive application shell with shared navigation. */
export function AppLayout(): JSX.Element {
  const { isAuthenticated, logout, user } = useAuth();
  const [language, setLanguage] = useState<"darija" | "arabic" | "fr">("darija");

  const languageLabels = {
    darija: "Darija",
    arabic: "العربية",
    fr: "Fr"
  };

  return (
    <div className="min-h-screen">
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-50 focus:rounded-lg focus:bg-white focus:px-4 focus:py-2 focus:shadow"
      >
        Skip to content
      </a>
      <header className="sticky top-0 z-40 border-b border-[#EAC79F] bg-[#111A33] text-white backdrop-blur-xl">
        <div className="mx-auto flex max-w-[1500px] items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <NavLink to="/" className="flex items-center gap-3 font-extrabold text-white">
            <span className="grid h-12 w-12 overflow-hidden rounded-xl border border-white/20 bg-white/10 shadow-sm">
              <img src={omniLogo} alt="OmniAgent logo" className="h-full w-full object-cover" />
            </span>
            <span className="leading-tight">
              <span className="block text-base">Khadamat Lmowatin</span>
              <span className="block text-xs font-semibold text-[#CFE8CC]">الخدمات الإدارية</span>
            </span>
          </NavLink>
          <nav aria-label="Primary navigation" className="hidden items-center gap-1 md:flex">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    "inline-flex h-10 items-center gap-2 rounded-lg px-3 text-sm font-semibold text-[#EAC79F] transition-colors hover:bg-white/10 hover:text-white",
                    isActive && "bg-[#D96A50] text-white"
                  )
                }
              >
                <item.icon className="h-4 w-4" aria-hidden="true" />
                <span className="leading-tight">
                  <span className="block">{item.label}</span>
                  <span className="block text-[11px] text-[#CFE8CC]">{item.labelFr}</span>
                </span>
              </NavLink>
            ))}
          </nav>
          <div className="hidden items-center gap-3 md:flex">
            {isAuthenticated ? (
              <>
                <span className="text-sm font-medium text-[#F8EFD8]">{user?.email}</span>
                <Button type="button" variant="outline" onClick={logout}>
                  Sign out
                </Button>
              </>
            ) : (
              <NavLink to="/admin">
                <Button type="button" variant="outline">
                  Admin login
                </Button>
              </NavLink>
            )}
          </div>
        </div>
      </header>
      <main id="main-content" className="mx-auto max-w-[1500px] px-4 py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
      <div className="fixed bottom-24 right-4 z-50 md:bottom-6 md:right-6">
        <div className="rounded-2xl border border-[#d9ccb8] bg-white/95 p-1 shadow-xl backdrop-blur">
          {(["darija", "arabic", "fr"] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setLanguage(option)}
              className={cn(
                "block w-full rounded-xl px-3 py-2 text-left text-sm font-bold transition-colors",
                language === option ? "bg-[#3F7A38] text-white" : "text-[#111A33] hover:bg-[#F8EFD8]"
              )}
              aria-label={`Switch language to ${languageLabels[option]}`}
            >
              {languageLabels[option]}
            </button>
          ))}
        </div>
      </div>
      <nav
        aria-label="Mobile navigation"
        className="fixed inset-x-0 bottom-0 z-40 grid grid-cols-4 border-t border-[#EAC79F] bg-white md:hidden"
      >
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              cn(
                "grid min-h-16 place-items-center gap-1 px-2 py-2 text-xs font-bold text-slate-500",
                isActive && "text-[#174D14]"
              )
            }
          >
            <item.icon className="h-5 w-5" aria-hidden="true" />
            <span>{item.label}</span>
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
