import { useState } from "react";
import { Link, useLocation } from "wouter";
import { Bell, Landmark, LogIn, LogOut, Menu, UserRound } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useI18n, type Language } from "@/lib/i18n";
import { logout, type AuthUser } from "@/lib/auth";
import {
  isNavigationItemActive,
  type LayoutNavigationItem,
} from "@/components/layout/navigation";

export type NotificationItem = {
  id: string;
  caseId: number;
  type: string;
  referenceNumber: string;
  applicantName: string;
  serviceNameFr: string;
  serviceNameAr: string;
  status: "submitted" | "in_review" | "approved" | "rejected" | "closed";
  createdAt: string | null;
  messageFr: string;
  messageAr: string;
};

type HeaderProps = {
  navigation: LayoutNavigationItem[];
  currentUser: AuthUser | null;
  showSidebar: boolean;
  isAdmin: boolean;
  pendingCount: number;
  notifications: NotificationItem[];
  onOpenMobileSidebar: () => void;
};

const LANGUAGE_OPTIONS: { value: Language; label: string }[] = [
  { value: "fr", label: "FR" },
  { value: "ar", label: "AR" },
  { value: "darija", label: "DA" },
];

export function Header({
  navigation,
  currentUser,
  showSidebar,
  isAdmin,
  pendingCount,
  notifications,
  onOpenMobileSidebar,
}: HeaderProps) {
  const [location, setLocation] = useLocation();
  const { language, setLanguage, t, isRtl } = useI18n();
  const [openNotifications, setOpenNotifications] = useState(false);
  const headerNavigation = navigation.filter((item) => item.showInHeader);

  const handleLogout = () => {
    logout();
    setLocation("/login");
  };

  return (
    <header
      className="sticky top-0 z-50 flex h-16 shrink-0 items-center gap-3 border-b border-border/80 bg-card/95 px-3 shadow-sm backdrop-blur sm:px-5 lg:px-7"
      dir={isRtl ? "rtl" : "ltr"}
    >
      {showSidebar && (
        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="md:hidden"
          onClick={onOpenMobileSidebar}
          aria-label={language === "fr" ? "Ouvrir le menu" : "فتح القائمة"}
        >
          <Menu className="h-5 w-5" />
        </Button>
      )}

      <Link href="/" className="flex min-w-0 shrink-0 items-center gap-2.5" aria-label={t("app.title")}>
        <span className="flex h-9 w-9 items-center justify-center rounded-lg border border-primary/20 bg-primary/10 text-primary">
          <Landmark className="h-5 w-5" />
        </span>
        <span className="hidden min-w-0 flex-col leading-tight sm:flex">
          <span className="truncate text-base font-bold text-[#17365d] dark:text-foreground">{t("app.title")}</span>
          <span className="text-[10px] text-muted-foreground">
            {language === "fr" ? "Services administratifs numériques" : "الخدمات الإدارية الرقمية"}
          </span>
        </span>
      </Link>

      <nav className="mx-auto hidden min-w-0 items-center gap-0.5 xl:flex" aria-label="Navigation principale">
        {headerNavigation.map((item) => {
          const active = isNavigationItemActive(item, location);
          return (
            <Link
              key={item.href}
              href={item.href}
              aria-current={active ? "page" : undefined}
              className={`whitespace-nowrap rounded-md px-2.5 py-2 text-sm transition-colors ${
                active
                  ? "bg-primary/10 font-semibold text-primary"
                  : "text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {item.name}
            </Link>
          );
        })}
      </nav>

      <div className="ms-auto flex shrink-0 items-center gap-1 sm:gap-1.5 xl:ms-0">
        <div className="flex items-center rounded-md border bg-muted/35 p-0.5" aria-label="Langue">
          {LANGUAGE_OPTIONS.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => setLanguage(option.value)}
              className={`rounded px-1.5 py-0.5 text-[10px] font-semibold transition-colors sm:px-2 sm:py-1 sm:text-[11px] ${
                language === option.value ? "bg-card text-primary shadow-sm" : "text-muted-foreground hover:text-foreground"
              }`}
              aria-pressed={language === option.value}
            >
              {option.label}
            </button>
          ))}
        </div>

        <ThemeToggle className="h-9 w-9" />

        {isAdmin && (
          <Popover open={openNotifications} onOpenChange={setOpenNotifications}>
            <PopoverTrigger asChild>
              <Button variant="ghost" size="icon" className="relative h-9 w-9" aria-label="Notifications">
                <Bell className="h-4 w-4" />
                {pendingCount > 0 && (
                  <span className="absolute end-0 top-0 flex h-4 min-w-4 items-center justify-center rounded-full bg-destructive px-1 text-[10px] font-bold text-destructive-foreground">
                    {pendingCount > 99 ? "99+" : pendingCount}
                  </span>
                )}
              </Button>
            </PopoverTrigger>
            <PopoverContent align={isRtl ? "start" : "end"} className="w-[calc(100vw-2rem)] max-w-xs sm:w-80 p-0" dir={isRtl ? "rtl" : "ltr"}>
              <div className="flex items-center justify-between border-b px-3 py-2.5">
                <span className="text-sm font-semibold">{language === "fr" ? "Notifications" : "الإشعارات"}</span>
                {pendingCount > 0 && <Badge variant="destructive">{pendingCount}</Badge>}
              </div>
              <div className="max-h-72 overflow-y-auto">
                {notifications.length > 0 ? notifications.map((notification) => (
                  <button
                    key={notification.id}
                    type="button"
                    className="block w-full border-b px-3 py-2.5 text-start text-xs transition-colors hover:bg-muted"
                    onClick={() => {
                      setOpenNotifications(false);
                      setLocation(`/cases/${notification.caseId}`);
                    }}
                  >
                    <span className="block font-semibold">{notification.applicantName} · {notification.referenceNumber}</span>
                    <span className="mt-0.5 block text-muted-foreground">
                      {language === "fr" ? notification.serviceNameFr : notification.serviceNameAr}
                    </span>
                  </button>
                )) : (
                  <p className="px-3 py-6 text-center text-xs text-muted-foreground">
                    {language === "fr" ? "Aucune notification récente." : "لا توجد إشعارات جديدة."}
                  </p>
                )}
              </div>
            </PopoverContent>
          </Popover>
        )}

        {currentUser ? (
          <>
            <Link
              href="/profile"
              className="flex h-9 items-center gap-2 rounded-md border px-2.5 text-sm text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label={t("nav.profile")}
            >
              <UserRound className="h-4 w-4" />
              <span className="hidden max-w-28 truncate 2xl:block">{currentUser.fullName}</span>
            </Link>
            <Button variant="ghost" size="icon" className="h-9 w-9" onClick={handleLogout} aria-label={language === "fr" ? "Se déconnecter" : "تسجيل الخروج"}>
              <LogOut className="h-4 w-4" />
            </Button>
          </>
        ) : (
          <Button variant="outline" size="sm" asChild className="h-9 gap-2">
            <Link href="/login"><LogIn className="h-4 w-4" /><span className="hidden sm:inline">{language === "fr" ? "Connexion" : "دخول"}</span></Link>
          </Button>
        )}
      </div>
    </header>
  );
}
