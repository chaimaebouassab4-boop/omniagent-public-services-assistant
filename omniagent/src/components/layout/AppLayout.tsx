import { type ReactNode, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useLocation } from "wouter";
import { Header, type NotificationItem } from "@/components/layout/Header";
import { Sidebar } from "@/components/layout/Sidebar";
import { getLayoutNavigation } from "@/components/layout/navigation";
import { apiUrl } from "@/lib/api-url";
import { getStoredUser, getToken } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";

const SIDEBAR_STORAGE_KEY = "omniagent_sidebar_collapsed";

type AppLayoutProps = {
  children: ReactNode;
  fullHeight?: boolean;
  fullBleed?: boolean;
  className?: string;
};

function getInitialSidebarState(): boolean {
  if (typeof window === "undefined") return false;
  const stored = window.localStorage.getItem(SIDEBAR_STORAGE_KEY);
  if (stored === "true") return true;
  if (stored === "false") return false;
  return window.matchMedia("(max-width: 1023px)").matches;
}

export function AppLayout({ children, fullHeight = false, fullBleed = false, className = "" }: AppLayoutProps) {
  const { t, language, isRtl } = useI18n();
  const [location] = useLocation();
  const [collapsed, setCollapsed] = useState(getInitialSidebarState);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const currentUser = getStoredUser();
  const showSidebar = Boolean(currentUser) && location !== "/";
  const isAdmin = Boolean(currentUser?.isAdmin);

  const { data: notificationData } = useQuery({
    queryKey: ["admin", "notifications"],
    queryFn: async () => {
      const token = getToken();
      if (!token) return { pendingCount: 0, notifications: [] as NotificationItem[] };
      const response = await fetch(apiUrl("/api/admin/notifications"), {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!response.ok) return { pendingCount: 0, notifications: [] as NotificationItem[] };
      return response.json() as Promise<{
        pendingCount: number;
        notifications: NotificationItem[];
      }>;
    },
    enabled: isAdmin,
    refetchInterval: 10_000,
  });

  const pendingCount = notificationData?.pendingCount ?? 0;
  const notifications = notificationData?.notifications ?? [];
  const navigation = useMemo(
    () => getLayoutNavigation({ language, t, isAdmin, pendingCount }),
    [language, t, isAdmin, pendingCount],
  );

  const handleCollapsedChange = (nextCollapsed: boolean) => {
    setCollapsed(nextCollapsed);
    window.localStorage.setItem(SIDEBAR_STORAGE_KEY, String(nextCollapsed));
  };

  return (
    <div className={`w-full bg-background ${fullHeight ? "h-dvh overflow-hidden" : "min-h-dvh"} ${className}`} dir={isRtl ? "rtl" : "ltr"}>
      <Header
        navigation={navigation}
        currentUser={currentUser}
        showSidebar={showSidebar}
        isAdmin={isAdmin}
        pendingCount={pendingCount}
        notifications={notifications}
        onOpenMobileSidebar={() => setMobileSidebarOpen(true)}
      />

      <div className={`flex w-full ${fullHeight ? "h-[calc(100dvh-4rem)] min-h-0 overflow-hidden" : "min-h-[calc(100dvh-4rem)]"}`}>
        {showSidebar && (
          <Sidebar
            navigation={navigation}
            collapsed={collapsed}
            onCollapsedChange={handleCollapsedChange}
            mobileOpen={mobileSidebarOpen}
            onMobileOpenChange={setMobileSidebarOpen}
          />
        )}
        <main className={`min-w-0 flex-1 ${fullHeight ? "h-full min-h-0 overflow-hidden" : "overflow-auto"}`}>
          <div className={
            fullHeight
              ? "flex h-full min-h-0 flex-col overflow-hidden p-2 sm:p-3 lg:p-4"
              : fullBleed
              ? "w-full"
              : "mx-auto w-full max-w-[1600px] p-4 sm:p-6 lg:p-8"
          }>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
