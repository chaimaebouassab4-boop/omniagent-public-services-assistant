import { ReactNode } from "react";
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
} from "@/components/ui/sidebar";
import { 
  Home, 
  FileText, 
  Briefcase, 
  MessageSquare, 
  Settings, 
  ShieldAlert 
} from "lucide-react";

export function AppLayout({ children }: { children: ReactNode }) {
  const [location] = useLocation();
  const { t, isRtl } = useI18n();

  const navigation = [
    { name: t("nav.home"), href: "/", icon: Home },
    { name: t("nav.dashboard"), href: "/dashboard", icon: FileText },
    { name: t("nav.services"), href: "/services", icon: Briefcase },
    { name: t("nav.chat"), href: "/chat", icon: MessageSquare },
    { name: t("nav.admin"), href: "/admin", icon: ShieldAlert },
    { name: t("nav.profile"), href: "/profile", icon: Settings },
  ];

  return (
    <SidebarProvider defaultOpen={true}>
      <div className={`min-h-screen flex w-full ${isRtl ? 'flex-row-reverse' : ''}`}>
        <Sidebar className="border-r border-sidebar-border bg-sidebar">
          <SidebarContent>
            <div className="p-4 py-6 border-b border-sidebar-border">
              <h2 className="text-xl font-bold text-primary">
                {t("app.title")}
              </h2>
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
                        <Link href={item.href} className="flex items-center gap-3 w-full">
                          <item.icon className="h-5 w-5" />
                          <span>{item.name}</span>
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
          <div className="p-6 md:p-10 flex-1 overflow-auto">
            {children}
          </div>
        </main>
      </div>
    </SidebarProvider>
  );
}
