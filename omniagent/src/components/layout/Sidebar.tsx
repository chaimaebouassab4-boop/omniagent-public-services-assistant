import { Link, useLocation } from "wouter";
import { ChevronLeft, ChevronRight, Landmark } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { useI18n, type Language } from "@/lib/i18n";
import {
  isNavigationItemActive,
  type LayoutNavigationItem,
} from "@/components/layout/navigation";

type SidebarProps = {
  navigation: LayoutNavigationItem[];
  collapsed: boolean;
  onCollapsedChange: (collapsed: boolean) => void;
  mobileOpen: boolean;
  onMobileOpenChange: (open: boolean) => void;
};

function NavigationLinks({
  navigation,
  collapsed,
  onNavigate,
}: {
  navigation: LayoutNavigationItem[];
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const [location] = useLocation();

  return (
    <nav className="flex flex-col gap-1 p-2" aria-label="Navigation latérale">
      {navigation.map((item) => {
        const active = isNavigationItemActive(item, location);
        return (
          <Link
            key={item.href}
            href={item.href}
            title={collapsed ? item.name : undefined}
            onClick={onNavigate}
            aria-current={active ? "page" : undefined}
            className={`relative flex h-11 items-center rounded-lg transition-colors ${
              collapsed ? "justify-center px-2" : "gap-3 px-3"
            } ${
              active
                ? "bg-primary/10 font-semibold text-primary"
                : "text-muted-foreground hover:bg-muted hover:text-foreground"
            }`}
          >
            <item.icon className="h-[18px] w-[18px] shrink-0" />
            {!collapsed && <span className="min-w-0 flex-1 truncate text-sm">{item.name}</span>}
            {item.badge !== undefined && item.badge > 0 && (
              collapsed ? (
                <span className="absolute end-1 top-1 h-2 w-2 rounded-full bg-destructive" />
              ) : (
                <Badge variant="destructive" className="h-5 min-w-5 justify-center rounded-full px-1.5 text-[10px]">
                  {item.badge > 99 ? "99+" : item.badge}
                </Badge>
              )
            )}
          </Link>
        );
      })}
    </nav>
  );
}

export function Sidebar({
  navigation,
  collapsed,
  onCollapsedChange,
  mobileOpen,
  onMobileOpenChange,
}: SidebarProps) {
  const { language, setLanguage, isRtl, t } = useI18n();
  const CollapseIcon = isRtl ? ChevronRight : ChevronLeft;
  const ExpandIcon = isRtl ? ChevronLeft : ChevronRight;

  return (
    <>
      <aside
        className={`sticky top-16 hidden h-[calc(100dvh-4rem)] shrink-0 flex-col border-e border-border/80 bg-card transition-[width] duration-300 ease-in-out md:flex ${
          collapsed ? "w-[68px]" : "w-[268px]"
        }`}
        dir={isRtl ? "rtl" : "ltr"}
      >
        <div className="min-h-0 flex-1 overflow-y-auto py-2">
          <NavigationLinks navigation={navigation} collapsed={collapsed} />
        </div>
        <div className="border-t p-2">
          <Button
            type="button"
            variant="ghost"
            className={`h-10 w-full text-muted-foreground ${collapsed ? "justify-center px-0" : "justify-start gap-3 px-3"}`}
            onClick={() => onCollapsedChange(!collapsed)}
            title={collapsed ? (language === "fr" ? "Déployer" : "توسيع") : (language === "fr" ? "Réduire" : "طي")}
          >
            {collapsed ? <ExpandIcon className="h-4 w-4" /> : <CollapseIcon className="h-4 w-4" />}
            {!collapsed && <span>{language === "fr" ? "Réduire le menu" : "طي القائمة"}</span>}
          </Button>
        </div>
      </aside>

      <Sheet open={mobileOpen} onOpenChange={onMobileOpenChange}>
        <SheetContent side={isRtl ? "right" : "left"} className="flex flex-col w-[min(86vw,320px)] p-0 md:hidden" dir={isRtl ? "rtl" : "ltr"}>
          <SheetHeader className="border-b px-4 py-4 text-start shrink-0">
            <SheetTitle className="flex items-center gap-2.5">
              <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary"><Landmark className="h-5 w-5" /></span>
              <span>{t("app.title")}</span>
            </SheetTitle>
          </SheetHeader>
          <div className="flex-1 overflow-y-auto">
            <NavigationLinks navigation={navigation} collapsed={false} onNavigate={() => onMobileOpenChange(false)} />
          </div>
          <div className="border-t p-3 bg-muted/20 shrink-0">
            <div className="flex items-center justify-between gap-1 rounded-lg border bg-card p-1">
              {[
                { value: "fr", label: "Français" },
                { value: "ar", label: "العربية" },
                { value: "darija", label: "الدارجة" },
              ].map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setLanguage(opt.value as Language)}
                  className={`flex-1 rounded py-1 text-xs font-semibold transition-colors ${
                    language === opt.value
                      ? "bg-primary text-primary-foreground shadow-xs"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
