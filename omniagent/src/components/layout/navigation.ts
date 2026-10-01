import type { LucideIcon } from "lucide-react";
import {
  Briefcase,
  CircleHelp,
  FileText,
  History,
  Home,
  MessageSquare,
  Settings,
  ShieldAlert,
} from "lucide-react";

export type LayoutNavigationItem = {
  name: string;
  href: string;
  icon: LucideIcon;
  badge?: number;
  showInHeader?: boolean;
};

type NavigationOptions = {
  language: "fr" | "ar" | "darija";
  t: (key: string) => string;
  isAdmin: boolean;
  pendingCount: number;
};

export function getLayoutNavigation({
  language,
  t,
  isAdmin,
  pendingCount,
}: NavigationOptions): LayoutNavigationItem[] {
  const helpLabel = language === "fr" ? "Aide" : language === "darija" ? "المساعدة" : "المساعدة";

  return [
    { name: t("nav.home"), href: "/", icon: Home },
    { name: t("nav.services"), href: "/services", icon: Briefcase, showInHeader: true },
    { name: t("nav.chat"), href: "/chat", icon: MessageSquare, showInHeader: true },
    { name: t("nav.dashboard"), href: "/dashboard", icon: FileText, showInHeader: true },
    { name: t("nav.history"), href: "/history", icon: History, showInHeader: true },
    { name: helpLabel, href: "/help", icon: CircleHelp, showInHeader: true },
    {
      name: t("nav.admin"),
      href: "/admin",
      icon: ShieldAlert,
      badge: isAdmin && pendingCount > 0 ? pendingCount : undefined,
      showInHeader: isAdmin,
    },
    { name: t("nav.profile"), href: "/profile", icon: Settings },
  ];
}

export function isNavigationItemActive(
  item: LayoutNavigationItem,
  location: string,
): boolean {
  if (item.href === "/") return location === "/";
  if (item.href === "/dashboard" && location.startsWith("/cases/")) return true;
  return location === item.href || location.startsWith(`${item.href}/`);
}
