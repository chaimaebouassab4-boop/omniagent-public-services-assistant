import { ReactNode, useState } from "react";
import { Link, useLocation } from "wouter";
import { useI18n } from "@/lib/i18n";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { 
  Home, 
  FileText, 
  Briefcase, 
  MessageSquare, 
  Settings, 
  ShieldAlert,
  Bell,
  CheckCircle2,
  Clock,
  AlertCircle,
  ExternalLink,
  ChevronRight,
  History,
  Loader2,
  PlayCircle,
} from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getStoredUser, getToken } from "@/lib/auth";
import { apiUrl } from "@/lib/api-url";
import { activateDemoPersona } from "@workspace/api-client-react";
import { useToast } from "@/hooks/use-toast";

type NotificationItem = {
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

function formatTimeAgo(isoString: string | null, language: string) {
  if (!isoString) return "";
  const diffMs = Date.now() - new Date(isoString).getTime();
  const diffMin = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMin < 1) return language === "fr" ? "À l'instant" : "الآن";
  if (diffMin < 60) return language === "fr" ? `Il y a ${diffMin} min` : `منذ ${diffMin} دقيقة`;
  if (diffHours < 24) return language === "fr" ? `Il y a ${diffHours} h` : `منذ ${diffHours} ساعة`;
  return language === "fr" ? `Il y a ${diffDays} j` : `منذ ${diffDays} يوم`;
}

export function AppLayout({ children }: { children: ReactNode }) {
  const [location, setLocation] = useLocation();
  const { t, language, setLanguage, isRtl } = useI18n();
  const [openNotifs, setOpenNotifs] = useState(false);
  const [demoPersona, setDemoPersona] = useState("");
  const [demoLoading, setDemoLoading] = useState(false);
  const queryClient = useQueryClient();
  const { toast } = useToast();
  const currentUser = getStoredUser();
  const isAdmin = !!currentUser?.isAdmin;

  // Real-time admin notifications query with 10s polling
  const { data: notifData } = useQuery({
    queryKey: ["admin", "notifications"],
    queryFn: async () => {
      const token = getToken();
      if (!token) return { pendingCount: 0, notifications: [] as NotificationItem[] };
      const res = await fetch(apiUrl("/api/admin/notifications"), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return { pendingCount: 0, notifications: [] as NotificationItem[] };
      return res.json() as Promise<{ pendingCount: number; notifications: NotificationItem[] }>;
    },
    enabled: isAdmin,
    refetchInterval: 10_000,
  });

  const pendingCount = notifData?.pendingCount ?? 0;
  const notifications = notifData?.notifications ?? [];

  const launchDemo = async (value: string) => {
    if (!value) return;
    const persona = value as "amine" | "fatima" | "youssef";
    setDemoPersona(value);
    setDemoLoading(true);
    try {
      const result = await activateDemoPersona(persona);
      setLanguage(result.persona.language);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["admin"] }),
        queryClient.invalidateQueries({ queryKey: ["cases"] }),
        queryClient.invalidateQueries({ queryKey: ["dashboard"] }),
      ]);
      setLocation(`/cases/${result.case.id}`);
    } catch (error) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Mode démo indisponible" : "تعذر تشغيل العرض",
        description: error instanceof Error ? error.message : undefined,
      });
    } finally {
      setDemoLoading(false);
      setDemoPersona("");
    }
  };

  const navigation = [
    { name: t("nav.home"), href: "/", icon: Home },
    { name: t("nav.dashboard"), href: "/dashboard", icon: FileText },
    { name: t("nav.history"), href: "/history", icon: History },
    { name: t("nav.services"), href: "/services", icon: Briefcase },
    ...(!isAdmin ? [{ name: t("nav.chat"), href: "/chat", icon: MessageSquare }] : []),
    { 
      name: t("nav.admin"), 
      href: "/admin", 
      icon: ShieldAlert,
      badge: isAdmin && pendingCount > 0 ? pendingCount : undefined 
    },
    { name: t("nav.profile"), href: "/profile", icon: Settings },
  ];

  return (
    <SidebarProvider defaultOpen={true}>
      <div className={`min-h-screen flex w-full ${isRtl ? 'flex-row-reverse' : ''}`}>
        <Sidebar className="border-r border-sidebar-border bg-sidebar">
          <SidebarContent>
            {/* Header with Title, ThemeToggle and Notification Bell */}
            <div className="p-4 py-5 border-b border-sidebar-border flex items-center justify-between gap-2">
              <h2 className="text-xl font-bold text-primary truncate">
                {t("app.title")}
              </h2>

              <div className="flex items-center gap-1 shrink-0">
                <ThemeToggle className="h-9 w-9 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground" />

                {/* Notification Popover for Admin */}
                {isAdmin && (
                  <Popover open={openNotifs} onOpenChange={setOpenNotifs}>
                    <PopoverTrigger asChild>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="relative h-9 w-9 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground"
                        aria-label="Notifications"
                      >
                        <Bell className="h-5 w-5" />
                      {pendingCount > 0 && (
                        <span className="absolute top-1 right-1 flex h-4 min-w-[16px] items-center justify-center rounded-full bg-red-600 px-1 text-[10px] font-bold text-white shadow-xs animate-pulse">
                          {pendingCount > 99 ? "99+" : pendingCount}
                        </span>
                      )}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent 
                    className="w-80 sm:w-96 p-0 shadow-xl border-border bg-popover z-50" 
                    align={isRtl ? "start" : "end"}
                    dir={isRtl ? "rtl" : "ltr"}
                  >
                    <div className="p-3.5 border-b border-border flex items-center justify-between bg-muted/40">
                      <div className="flex items-center gap-2">
                        <Bell className="w-4 h-4 text-primary" />
                        <span className="font-semibold text-sm text-foreground">
                          {language === "fr" ? "Notifications d'activité" : "إشعارات النشاط والطلبات"}
                        </span>
                      </div>
                      {pendingCount > 0 && (
                        <Badge variant="destructive" className="text-[11px] px-2 py-0.5">
                          {pendingCount} {language === "fr" ? "en attente" : "قيد الانتظار"}
                        </Badge>
                      )}
                    </div>

                    <div className="max-h-80 overflow-y-auto divide-y divide-border/60">
                      {notifications.length > 0 ? (
                        notifications.map((n) => (
                          <div 
                            key={n.id}
                            onClick={() => {
                              setOpenNotifs(false);
                              setLocation(`/cases/${n.caseId}`);
                            }}
                            className="p-3 hover:bg-muted/60 transition-colors cursor-pointer flex items-start gap-3 text-start"
                          >
                            <div className="mt-0.5 shrink-0">
                              {n.status === "approved" ? (
                                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                              ) : n.status === "rejected" ? (
                                <AlertCircle className="w-4 h-4 text-red-600" />
                              ) : (
                                <Clock className="w-4 h-4 text-amber-500 animate-pulse" />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs font-semibold text-foreground truncate">
                                {n.applicantName} • <span className="font-mono text-primary">{n.referenceNumber}</span>
                              </p>
                              <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">
                                {language === "fr" ? n.serviceNameFr : n.serviceNameAr}
                              </p>
                              <div className="flex items-center justify-between mt-1">
                                <span className="text-[10px] text-muted-foreground/80">
                                  {formatTimeAgo(n.createdAt, language)}
                                </span>
                                <Badge 
                                  variant="outline" 
                                  className={`text-[9px] px-1.5 py-0 h-4 border-0 ${
                                    n.status === "approved" 
                                      ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400" 
                                      : n.status === "rejected"
                                      ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400"
                                      : "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                                  }`}
                                >
                                  {n.status === "approved" 
                                    ? (language === "fr" ? "Accepté" : "مقبول") 
                                    : n.status === "rejected" 
                                    ? (language === "fr" ? "Rejeté" : "مرفوض") 
                                    : (language === "fr" ? "Nouveau" : "جديد")}
                                </Badge>
                              </div>
                            </div>
                          </div>
                        ))
                      ) : (
                        <div className="py-8 text-center text-xs text-muted-foreground">
                          {language === "fr" ? "Aucune notification récente." : "لا توجد إشعارات جديدة."}
                        </div>
                      )}
                    </div>

                    <div className="p-2.5 border-t border-border bg-muted/20">
                      <Button 
                        variant="ghost" 
                        size="sm" 
                        className="w-full text-xs text-primary hover:text-primary font-medium gap-1 justify-center"
                        onClick={() => {
                          setOpenNotifs(false);
                          setLocation("/admin");
                        }}
                      >
                        <span>{language === "fr" ? "Ouvrir l'administration" : "لوحة إدارة الطلبات"}</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </Button>
                    </div>
                  </PopoverContent>
                </Popover>
              )}
              </div>
            </div>

            <SidebarGroup>
              <SidebarGroupContent>
                <SidebarMenu>
                  {navigation.map((item) => (
                    <SidebarMenuItem key={item.href}>
                      <SidebarMenuButton 
                        asChild 
                        isActive={location === item.href}
                        tooltip={item.name}
                      >
                        <Link href={item.href} className="flex items-center justify-between w-full">
                          <div className="flex items-center gap-3">
                            <item.icon className="h-5 w-5" />
                            <span>{item.name}</span>
                          </div>
                          {item.badge !== undefined && item.badge > 0 && (
                            <Badge 
                              variant="destructive" 
                              className="h-5 min-w-[20px] px-1.5 text-[10px] font-bold flex items-center justify-center rounded-full bg-red-600 text-white"
                            >
                              {item.badge}
                            </Badge>
                          )}
                        </Link>
                      </SidebarMenuButton>
                    </SidebarMenuItem>
                  ))}
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>
        </Sidebar>
        <main className="flex-1 flex flex-col bg-background relative z-0 min-w-0">
          {/* Mobile Top Bar */}
          <div className="md:hidden flex items-center justify-between px-4 py-2.5 border-b border-border bg-card/70 backdrop-blur sticky top-0 z-40">
            <SidebarTrigger />
            <div className="flex items-center gap-1">
              <ThemeToggle />
            </div>
          </div>
          {isAdmin && (
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-primary/15 bg-primary/5 px-4 py-2.5 md:px-10">
              <div className="flex items-center gap-2 text-sm font-semibold text-foreground">
                <PlayCircle className="h-4 w-4 text-primary" />
                <span>{language === "fr" ? "Mode présentation" : "وضع العرض"}</span>
                <Badge variant="outline" className="hidden border-primary/30 bg-background text-[10px] sm:inline-flex">DEMO</Badge>
              </div>
              <div className="flex items-center gap-2">
                {demoLoading && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
                <select
                  aria-label={language === "fr" ? "Choisir un scénario de démonstration" : "اختيار سيناريو العرض"}
                  value={demoPersona}
                  disabled={demoLoading}
                  onChange={(event) => void launchDemo(event.target.value)}
                  className="h-9 max-w-[340px] rounded-md border border-input bg-background px-3 text-sm shadow-sm outline-none focus:ring-2 focus:ring-ring"
                >
                  <option value="">{language === "fr" ? "Choisir une persona…" : "اختار شخصية…"}</option>
                  <option value="amine">Demo 1: Amine — Darija · Certificat de résidence</option>
                  <option value="fatima">Demo 2: Fatima — Français · Acte de naissance</option>
                  <option value="youssef">Demo 3: Youssef — Rejet · Document illisible</option>
                </select>
              </div>
            </div>
          )}
          <div className="p-6 md:p-10 flex-1 overflow-auto">
            {children}
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
