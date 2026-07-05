import { useState } from "react";
import { Link, useLocation } from "wouter";
import { useI18n } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { motion } from "framer-motion";
import { Eye, EyeOff, ArrowRight, ArrowLeft, Bot } from "lucide-react";
import { login } from "@/lib/auth";

export default function Login() {
  const { language, isRtl } = useI18n();
  const [_, setLocation] = useLocation();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const Arrow = isRtl ? ArrowLeft : ArrowRight;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      const user = await login(email, password);
      setLocation(user.isAdmin ? "/admin" : "/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Échec de la connexion");
    } finally {
      setIsLoading(false);
    }
  };

  const t = {
    title: { fr: "Bon retour", ar: "مرحباً بعودتك", darija: "مرحبا بيك" },
    subtitle: {
      fr: "Connectez-vous pour accéder à vos dossiers",
      ar: "سجّل الدخول للوصول إلى ملفاتك",
      darija: "دخل للحساب ديالك باش تشوف ملفاتك",
    },
    email: { fr: "Adresse e-mail", ar: "البريد الإلكتروني", darija: "الإيميل" },
    password: { fr: "Mot de passe", ar: "كلمة المرور", darija: "كلمة السر" },
    forgot: { fr: "Mot de passe oublié ?", ar: "نسيت كلمة المرور؟", darija: "نسيتي كلمة السر؟" },
    submit: { fr: "Se connecter", ar: "تسجيل الدخول", darija: "دخل" },
    noAccount: { fr: "Pas encore de compte ?", ar: "ليس لديك حساب؟", darija: "ما عندكش حساب؟" },
    signup: { fr: "S'inscrire", ar: "إنشاء حساب", darija: "سجل دابا" },
    or: { fr: "ou continuer avec", ar: "أو المتابعة عبر", darija: "أو كمل بـ" },
  };

  const getText = (key: keyof typeof t) => t[key][language] ?? t[key]["fr"];

  return (
    <div className={`min-h-screen grid lg:grid-cols-2 ${isRtl ? "direction-rtl" : ""}`}>
      {/* Left — Image panel */}
      <div className="hidden lg:block relative overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1539020140153-e479b8c22e70?q=85&w=1400&auto=format&fit=crop"
          alt="Rabat, Maroc"
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-primary/80 via-primary/60 to-secondary/80" />
        <div className="absolute inset-0 flex flex-col justify-between p-12">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-9 h-9 bg-white rounded-xl flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary" />
            </div>
            <span className="text-2xl font-bold text-white">OmniAgent</span>
          </Link>
          {/* Quote */}
          <div>
            <blockquote className="text-white text-xl font-light leading-relaxed mb-6" dir="rtl">
              "المساعد الذكي للخدمات الإدارية المغربية — بالعربية والدارجة والفرنسية"
            </blockquote>
            <p className="text-white/70 text-sm">Votre assistant IA pour les démarches administratives marocaines</p>
            <div className="flex gap-3 mt-6">
              {["🇲🇦", "🔒", "⚡"].map((icon) => (
                <span key={icon} className="w-10 h-10 bg-white/10 rounded-full flex items-center justify-center text-lg">
                  {icon}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Right — Form */}
      <div className={`flex flex-col justify-center items-center px-6 py-16 bg-background ${isRtl ? "text-right" : "text-left"}`}>
        {/* Mobile logo */}
        <Link href="/" className="flex items-center gap-2 mb-10 lg:hidden">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <span className="text-xl font-bold text-primary">OmniAgent</span>
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <h1 className="text-3xl font-bold text-foreground mb-2">{getText("title")}</h1>
          <p className="text-muted-foreground mb-8">{getText("subtitle")}</p>

          <form onSubmit={handleSubmit} className="space-y-5">
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600" dir="ltr">
                {error}
              </div>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-sm font-medium">{getText("email")}</Label>
              <Input
                id="email"
                type="email"
                data-testid="input-email"
                placeholder="ahmed@example.ma"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="h-11"
                required
                dir="ltr"
              />
            </div>

            <div className="space-y-1.5">
              <div className={`flex items-center justify-between ${isRtl ? "flex-row-reverse" : ""}`}>
                <Label htmlFor="password" className="text-sm font-medium">{getText("password")}</Label>
                <button type="button" className="text-xs text-primary hover:underline">
                  {getText("forgot")}
                </button>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  data-testid="input-password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`h-11 ${isRtl ? "pl-10" : "pr-10"}`}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={`absolute top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground ${isRtl ? "left-3" : "right-3"}`}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              data-testid="button-login"
              className="w-full h-11 text-base gap-2"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  {language === "fr" ? "Connexion..." : language === "ar" ? "جاري الدخول..." : "دير الدخول..."}
                </span>
              ) : (
                <>
                  {getText("submit")}
                  <Arrow className="w-4 h-4" />
                </>
              )}
            </Button>
          </form>

          {/* Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-border" />
            </div>
            <div className="relative flex justify-center text-xs text-muted-foreground">
              <span className="px-3 bg-background">{getText("or")}</span>
            </div>
          </div>

          {/* Social login placeholders */}
          <div className="grid grid-cols-2 gap-3">
            <Button variant="outline" className="h-11 gap-2 font-normal" type="button">
              <img src="https://www.google.com/favicon.ico" alt="Google" className="w-4 h-4" />
              Google
            </Button>
            <Button variant="outline" className="h-11 gap-2 font-normal" type="button">
              <span className="text-blue-600 font-bold text-sm">f</span>
              Facebook
            </Button>
          </div>

          {/* Sign up link */}
          <p className={`mt-8 text-sm text-muted-foreground text-center`}>
            {getText("noAccount")}{" "}
            <Link href="/signup" className="text-primary font-medium hover:underline">
              {getText("signup")}
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
