import { useState } from "react";
import { Link, useLocation } from "wouter";
import { useI18n } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { motion } from "framer-motion";
import { Eye, EyeOff, ArrowRight, ArrowLeft, Bot, KeyRound, Mail, ShieldCheck } from "lucide-react";
import { login } from "@/lib/auth";
import { useToast } from "@/hooks/use-toast";
import { Landmark, BadgeCheck } from "lucide-react";

import { apiUrl } from "@/lib/api-url";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function Login() {
  const { language, setLanguage, isRtl } = useI18n();
  const [_, setLocation] = useLocation();
  const { toast } = useToast();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  // Forgot password state
  const [resetOpen, setResetOpen] = useState(false);
  const [resetStep, setResetStep] = useState<"email" | "code" | "done">("email");
  const [resetEmail, setResetEmail] = useState("");
  const [resetCode, setResetCode] = useState("");
  const [resetCodeFromServer, setResetCodeFromServer] = useState<string | null>(null);
  const [newPassword, setNewPassword] = useState("");
  const [resetLoading, setResetLoading] = useState(false);
  const [resetError, setResetError] = useState("");

  const Arrow = isRtl ? ArrowLeft : ArrowRight;
  const requestedPath = new URLSearchParams(window.location.search).get("returnTo");
  const safeReturnPath =
    requestedPath?.startsWith("/") && !requestedPath.startsWith("//")
      ? requestedPath
      : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      const user = await login(email, password);
      setLocation(safeReturnPath ?? (user.isAdmin ? "/admin" : "/dashboard"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Échec de la connexion");
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = () => {
    setResetEmail(email); // Pre-fill from login form
    setResetStep("email");
    setResetCode("");
    setNewPassword("");
    setResetError("");
    setResetCodeFromServer(null);
    setResetOpen(true);
  };

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    setResetLoading(true);
    setResetError("");
    try {
      const res = await fetch(apiUrl("/api/auth/forgot-password"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: resetEmail }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur");
      // MVP: server returns the code directly
      if (data.code) {
        setResetCodeFromServer(data.code);
        setResetCode(data.code);
      }
      setResetStep("code");
    } catch (err) {
      setResetError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setResetLoading(false);
    }
  };

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setResetLoading(true);
    setResetError("");
    try {
      const res = await fetch(apiUrl("/api/auth/reset-password"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: resetEmail,
          code: resetCode,
          newPassword: newPassword,
        }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erreur");
      setResetStep("done");
      toast({
        title: language === "fr" ? "Mot de passe modifié ✓" : "تم تغيير كلمة المرور ✓",
        description: language === "fr"
          ? "Vous pouvez maintenant vous connecter."
          : "دابا تقدر دخل بكلمة السر الجديدة.",
      });
    } catch (err) {
      setResetError(err instanceof Error ? err.message : "Erreur");
    } finally {
      setResetLoading(false);
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
  };

  const getText = (key: keyof typeof t) => t[key][language] ?? t[key]["fr"];

  const isFr = language === "fr";

  return (
    <div className={`min-h-screen grid overflow-x-hidden overflow-y-auto lg:grid-cols-2 ${isRtl ? "direction-rtl" : ""}`}>
      {/* Left — Image panel */}
      <motion.div
        initial={{ opacity: 0.96, x: "100%" }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.65, ease: [0.25, 1, 0.5, 1] }}
        className="relative hidden overflow-hidden lg:block"
      >
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
  <blockquote
    className="text-white text-xl font-light leading-relaxed mb-6"
    dir="rtl"
  >
    "المساعد الذكي للخدمات الإدارية المغربية — بالعربية والدارجة والفرنسية"
  </blockquote>

  <p className="text-white/70 text-sm">
    Votre assistant IA pour les démarches administratives marocaines
  </p>

  <div className="flex flex-wrap gap-3 mt-6">
    {[
      {
        icon: Landmark,
        label: "Services administratifs",
      },
      {
        icon: ShieldCheck,
        label: "Données sécurisées",
      },
      {
        icon: BadgeCheck,
        label: "Service fiable",
      },
    ].map(({ icon: Icon, label }) => (
      <div
        key={label}
        className="flex items-center gap-2 px-3 py-2 rounded-lg bg-white/10 border border-white/10"
      >
        <Icon
          className="w-4 h-4 text-white"
          strokeWidth={1.8}
        />
        <span className="text-white/90 text-xs font-medium">
          {label}
        </span>
      </div>
    ))}
  </div>
</div>
        </div>
      </motion.div>

      {/* Right — Form */}
      <motion.div
        initial={{ opacity: 0.96, x: "-100%" }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.65, ease: [0.25, 1, 0.5, 1] }}
        className={`relative flex flex-col justify-center items-center px-4 py-12 sm:px-6 sm:py-16 bg-background min-h-screen lg:min-h-0 ${isRtl ? "text-right" : "text-left"}`}
      >
        {/* Top bar with ThemeToggle and Language Switcher */}
        <div className={`absolute top-3 sm:top-4 ${isRtl ? "left-3 sm:left-4" : "right-3 sm:right-4"} flex items-center gap-1.5 sm:gap-2 z-10`}>
          <ThemeToggle />
          <div className="flex items-center gap-0.5 sm:gap-1 border border-border rounded-lg p-0.5 bg-card/80">
            {(["ar", "darija", "fr"] as const).map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => setLanguage(lang)}
                className={`px-1.5 sm:px-2 py-0.5 rounded text-[11px] sm:text-xs font-medium transition-colors ${
                  language === lang
                    ? "bg-primary text-white"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {lang === "ar" ? "عربية" : lang === "darija" ? "دارجة" : "FR"}
              </button>
            ))}
          </div>
        </div>

        {/* Mobile logo */}
        <Link href="/" className="flex items-center gap-2 mb-6 sm:mb-10 lg:hidden">
          <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <span className="text-xl font-bold text-primary">OmniAgent</span>
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
          className="w-full max-w-md"
        >
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground mb-1.5 sm:mb-2">{getText("title")}</h1>
          <p className="text-sm sm:text-base text-muted-foreground mb-6 sm:mb-8">{getText("subtitle")}</p>

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
                <button type="button" onClick={handleForgotPassword} className="text-xs text-primary hover:underline">
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

          {/* Sign up link */}
          <p className={`mt-8 text-sm text-muted-foreground text-center`}>
            {getText("noAccount")}{" "}
            <Link href="/signup" className="text-primary font-medium hover:underline">
              {getText("signup")}
            </Link>
          </p>
        </motion.div>
      </motion.div>

      {/* ── Password Reset Dialog ── */}
      <Dialog open={resetOpen} onOpenChange={(open) => { if (!open) setResetOpen(false); }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <KeyRound className="w-5 h-5 text-primary" />
              {isFr ? "Réinitialiser le mot de passe" : "إعادة تعيين كلمة المرور"}
            </DialogTitle>
            <DialogDescription>
              {resetStep === "email" && (isFr
                ? "Entrez votre adresse email pour recevoir un code de réinitialisation."
                : "دخل الإيميل ديالك باش تاخد كود ديال إعادة تعيين كلمة المرور.")}
              {resetStep === "code" && (isFr
                ? "Entrez le code reçu et votre nouveau mot de passe."
                : "دخل الكود لي وصلك وكلمة المرور الجديدة.")}
              {resetStep === "done" && (isFr
                ? "Votre mot de passe a été modifié avec succès."
                : "تم تغيير كلمة المرور بنجاح.")}
            </DialogDescription>
          </DialogHeader>

          {resetError && (
            <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600" dir="ltr">
              {resetError}
            </div>
          )}

          {/* Step 1: Enter email */}
          {resetStep === "email" && (
            <form onSubmit={handleRequestCode} className="space-y-4 mt-2">
              <div className="space-y-1.5">
                <Label htmlFor="reset-email" className="text-sm font-medium">
                  {isFr ? "Adresse e-mail" : "البريد الإلكتروني"}
                </Label>
                <div className="relative">
                  <Mail className={`absolute top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground ${isRtl ? "right-3" : "left-3"}`} />
                  <Input
                    id="reset-email"
                    type="email"
                    value={resetEmail}
                    onChange={(e) => setResetEmail(e.target.value)}
                    placeholder="ahmed@example.ma"
                    className={`h-11 ${isRtl ? "pr-10" : "pl-10"}`}
                    required
                    dir="ltr"
                  />
                </div>
              </div>
              <Button type="submit" className="w-full h-11" disabled={resetLoading}>
                {resetLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    {isFr ? "Envoi..." : "جاري الإرسال..."}
                  </span>
                ) : (
                  isFr ? "Envoyer le code" : "إرسال الكود"
                )}
              </Button>
            </form>
          )}

          {/* Step 2: Enter code + new password */}
          {resetStep === "code" && (
            <form onSubmit={handleResetPassword} className="space-y-4 mt-2">
              {/* MVP: show the code directly */}
              {resetCodeFromServer && (
                <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
                  <p className="font-medium mb-1">{isFr ? "🔑 Code de réinitialisation (MVP)" : "🔑 كود إعادة التعيين (MVP)"}</p>
                  <p className="text-2xl font-mono font-bold tracking-widest text-center my-2">{resetCodeFromServer}</p>
                  <p className="text-xs text-amber-600">
                    {isFr
                      ? "En production, ce code serait envoyé par email."
                      : "فالإنتاج، هاد الكود غادي يتبعث عبر الإيميل."}
                  </p>
                </div>
              )}

              <div className="space-y-1.5">
                <Label htmlFor="reset-code" className="text-sm font-medium">
                  {isFr ? "Code à 6 chiffres" : "الكود (6 أرقام)"}
                </Label>
                <Input
                  id="reset-code"
                  value={resetCode}
                  onChange={(e) => setResetCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                  placeholder="000000"
                  className="h-11 text-center text-lg font-mono tracking-widest"
                  maxLength={6}
                  required
                  dir="ltr"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="new-password" className="text-sm font-medium">
                  {isFr ? "Nouveau mot de passe" : "كلمة المرور الجديدة"}
                </Label>
                <Input
                  id="new-password"
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  className="h-11"
                  minLength={6}
                  required
                />
              </div>

              <Button type="submit" className="w-full h-11" disabled={resetLoading || resetCode.length < 6}>
                {resetLoading ? (
                  <span className="flex items-center gap-2">
                    <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                    {isFr ? "Modification..." : "جاري التغيير..."}
                  </span>
                ) : (
                  isFr ? "Changer le mot de passe" : "غير كلمة المرور"
                )}
              </Button>
            </form>
          )}

          {/* Step 3: Success */}
          {resetStep === "done" && (
            <div className="flex flex-col items-center gap-4 py-4">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                <ShieldCheck className="w-8 h-8 text-green-600" />
              </div>
              <p className="text-sm text-muted-foreground text-center">
                {isFr
                  ? "Vous pouvez maintenant vous connecter avec votre nouveau mot de passe."
                  : "دابا تقدر دخل بكلمة المرور الجديدة ديالك."}
              </p>
              <Button onClick={() => setResetOpen(false)} className="w-full h-11">
                {isFr ? "Retour à la connexion" : "رجع للدخول"}
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
