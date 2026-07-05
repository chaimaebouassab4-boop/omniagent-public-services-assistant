import { ReactNode, useEffect, useState } from "react";
import { Link, useLocation } from "wouter";
import { useI18n } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Bot, LogOut } from "lucide-react";
import { getStoredUser, logout, type AuthUser } from "@/lib/auth";

function initials(user: AuthUser): string {
  const source = user.fullName?.trim() || user.email;
  return source
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part.charAt(0).toUpperCase())
    .join("");
}

export function MainLayout({ children }: { children: ReactNode }) {
  const { language, setLanguage, isRtl } = useI18n();
  const [_, setLocation] = useLocation();
  const [user, setUser] = useState<AuthUser | null>(null);

  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  const handleLogout = () => {
    logout();
    setUser(null);
    setLocation("/login");
  };

  return (
    <div className="min-h-screen flex flex-col bg-background">
      <header className="sticky top-0 z-50 w-full border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
        <div className={`container mx-auto h-16 flex items-center justify-between px-4 ${isRtl ? "flex-row-reverse" : ""}`}>
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 shrink-0">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <span className="text-xl font-bold text-primary">OmniAgent</span>
          </Link>

          {/* Nav center */}
          <nav className={`hidden md:flex items-center gap-6 ${isRtl ? "flex-row-reverse" : ""}`}>
            <Link href="/services" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
              {language === "fr" ? "Services" : "الخدمات"}
            </Link>
            <Link href="/chat" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
              {language === "fr" ? "Assistant IA" : "المساعد الذكي"}
            </Link>
            <Link href="/dashboard" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">
              {language === "fr" ? "Mes dossiers" : "قضاياي"}
            </Link>
          </nav>

          {/* Right — lang + auth */}
          <div className={`flex items-center gap-3 ${isRtl ? "flex-row-reverse" : ""}`}>
            {/* Language switcher */}
            <div className="flex items-center gap-1 border border-border rounded-lg p-0.5">
              {(["ar", "darija", "fr"] as const).map((lang) => (
                <button
                  key={lang}
                  onClick={() => setLanguage(lang)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                    language === lang
                      ? "bg-primary text-white"
                      : "text-muted-foreground hover:text-foreground"
                  }`}
                >
                  {lang === "ar" ? "عربية" : lang === "darija" ? "دارجة" : "FR"}
                </button>
              ))}
            </div>

            {/* Auth: profile when logged in, otherwise login/signup */}
            {user ? (
              <>
                <Link
                  href="/profile"
                  className={`flex items-center gap-2 rounded-lg border border-border px-2 py-1 hover:bg-muted transition-colors ${isRtl ? "flex-row-reverse" : ""}`}
                >
                  <span className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center text-xs font-bold shrink-0">
                    {initials(user)}
                  </span>
                  <span className="hidden sm:block text-sm font-medium text-foreground max-w-[140px] truncate">
                    {user.fullName || user.email}
                  </span>
                </Link>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleLogout}
                  title={language === "fr" ? "Déconnexion" : "تسجيل الخروج"}
                  aria-label={language === "fr" ? "Déconnexion" : "تسجيل الخروج"}
                >
                  <LogOut className="w-4 h-4" />
                </Button>
              </>
            ) : (
              <>
                <Button variant="ghost" size="sm" asChild className="hidden sm:inline-flex">
                  <Link href="/login">
                    {language === "fr" ? "Connexion" : language === "ar" ? "دخول" : "دخل"}
                  </Link>
                </Button>
                <Button size="sm" asChild>
                  <Link href="/signup">
                    {language === "fr" ? "S'inscrire" : language === "ar" ? "تسجيل" : "سجل"}
                  </Link>
                </Button>
              </>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1">{children}</main>

      <footer className="border-t bg-card">
        <div className="container mx-auto px-4 py-10">
          <div className={`grid grid-cols-1 md:grid-cols-4 gap-8 ${isRtl ? "text-right" : "text-left"}`}>
            <div className="md:col-span-2">
              <Link href="/" className="flex items-center gap-2 mb-3">
                <div className="w-7 h-7 bg-primary rounded-lg flex items-center justify-center">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <span className="text-lg font-bold text-primary">OmniAgent</span>
              </Link>
              <p className="text-sm text-muted-foreground leading-relaxed max-w-xs">
                {language === "fr"
                  ? "Votre assistant IA pour toutes les démarches administratives marocaines."
                  : language === "ar"
                  ? "مساعدك الذكي لجميع الإجراءات الإدارية المغربية."
                  : "المساعد ديالك للإجراءات الإدارية المغربية."}
              </p>
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground mb-3">
                {language === "fr" ? "Services" : "الخدمات"}
              </p>
              <div className="flex flex-col gap-2">
                {[
                  { fr: "Carte d'Identité", ar: "بطاقة التعريف" },
                  { fr: "Passeport", ar: "جواز السفر" },
                  { fr: "Acte de Naissance", ar: "شهادة الميلاد" },
                  { fr: "Attestation de Résidence", ar: "شهادة الإقامة" },
                ].map((item) => (
                  <Link
                    key={item.fr}
                    href="/services"
                    className="text-xs text-muted-foreground hover:text-primary transition-colors"
                  >
                    {language === "fr" ? item.fr : item.ar}
                  </Link>
                ))}
              </div>
            </div>
            <div>
              <p className="text-sm font-semibold text-foreground mb-3">
                {language === "fr" ? "Liens utiles" : "روابط مفيدة"}
              </p>
              <div className="flex flex-col gap-2">
                {[
                  { fr: "Se connecter", ar: "تسجيل الدخول", href: "/login" },
                  { fr: "Créer un compte", ar: "إنشاء حساب", href: "/signup" },
                  { fr: "Assistant IA", ar: "المساعد الذكي", href: "/chat" },
                  { fr: "Tableau de bord", ar: "لوحة التحكم", href: "/dashboard" },
                ].map((item) => (
                  <Link
                    key={item.fr}
                    href={item.href}
                    className="text-xs text-muted-foreground hover:text-primary transition-colors"
                  >
                    {language === "fr" ? item.fr : item.ar}
                  </Link>
                ))}
              </div>
            </div>
          </div>
          <div className="border-t border-border mt-8 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p className="text-xs text-muted-foreground">
              © 2026 OmniAgent. {language === "fr" ? "Tous droits réservés." : "جميع الحقوق محفوظة."}
            </p>
            <p className="text-xs text-muted-foreground">🇲🇦 Made for Morocco</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
