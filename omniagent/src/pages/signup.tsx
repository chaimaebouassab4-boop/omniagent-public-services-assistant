import { useState } from "react";
import { Link, useLocation } from "wouter";
import { useI18n } from "@/lib/i18n";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { motion } from "framer-motion";
import { Eye, EyeOff, ArrowRight, ArrowLeft, Bot, CheckCircle } from "lucide-react";
import { signup } from "@/lib/auth";

const BENEFITS = [
  { fr: "Suivez vos dossiers en temps réel", ar: "تابع ملفاتك في الوقت الفعلي", darija: "تبع ملفاتك بالوقت الحقيقي" },
  { fr: "Recevez des alertes sur vos demandes", ar: "احصل على تنبيهات بشأن طلباتك", darija: "واخد تنبيهات على الطلبات ديالك" },
  { fr: "Historique complet de vos démarches", ar: "سجل كامل لإجراءاتك", darija: "تاريخ كامل ديال الإجراءات ديالك" },
  { fr: "Assistance IA 24h/7j en 3 langues", ar: "مساعدة ذكية 24/7 بـ3 لغات", darija: "مساعدة ذكية 24/7 بـ3 لغات" },
];

export default function Signup() {
  const { language, isRtl } = useI18n();
  const [_, setLocation] = useLocation();
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [form, setForm] = useState({ fullName: "", email: "", phone: "", password: "" });
  const [error, setError] = useState("");

  const Arrow = isRtl ? ArrowLeft : ArrowRight;

  const update = (k: keyof typeof form) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm((prev) => ({ ...prev, [k]: e.target.value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      await signup({
        fullName: form.fullName,
        email: form.email,
        phone: form.phone || undefined,
        password: form.password,
      });
      setLocation("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Échec de l'inscription");
    } finally {
      setIsLoading(false);
    }
  };

  const t = {
    title: { fr: "Créer votre compte", ar: "إنشاء حسابك", darija: "ابدأ دابا مجاناً" },
    subtitle: {
      fr: "Rejoignez des milliers de citoyens marocains",
      ar: "انضم لآلاف المواطنين المغاربة",
      darija: "انضم لآلاف المواطنين المغاربة",
    },
    fullName: { fr: "Nom complet", ar: "الاسم الكامل", darija: "الاسم الكامل" },
    email: { fr: "Adresse e-mail", ar: "البريد الإلكتروني", darija: "الإيميل" },
    phone: { fr: "Téléphone (optionnel)", ar: "رقم الهاتف (اختياري)", darija: "رقم الهاتف (اختياري)" },
    password: { fr: "Mot de passe", ar: "كلمة المرور", darija: "كلمة السر" },
    submit: { fr: "Créer mon compte", ar: "إنشاء الحساب", darija: "ابدأ دابا" },
    hasAccount: { fr: "Déjà un compte ?", ar: "لديك حساب بالفعل؟", darija: "عندك حساب؟" },
    login: { fr: "Se connecter", ar: "تسجيل الدخول", darija: "دخل" },
    terms: {
      fr: "En vous inscrivant, vous acceptez nos Conditions d'utilisation et notre Politique de confidentialité.",
      ar: "بالتسجيل، أنت توافق على شروط الاستخدام وسياسة الخصوصية.",
      darija: "بالتسجيل كتقبل الشروط وسياسة الخصوصية.",
    },
  };

  const getText = (key: keyof typeof t) => t[key][language] ?? t[key]["fr"];

  return (
    <div className={`min-h-screen grid lg:grid-cols-2 ${isRtl ? "direction-rtl" : ""}`}>
      {/* Left — Benefits panel */}
      <div className="hidden lg:flex flex-col justify-between relative overflow-hidden">
        <img
          src="https://images.unsplash.com/photo-1499856871958-5b9357976b82?q=80&w=1400&auto=format&fit=crop"
          alt="Médina marocaine"
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-br from-secondary/90 via-secondary/75 to-primary/80" />

        <div className="relative z-10 flex flex-col h-full p-12 justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2">
            <div className="w-9 h-9 bg-white rounded-xl flex items-center justify-center">
              <Bot className="w-5 h-5 text-secondary" />
            </div>
            <span className="text-2xl font-bold text-white">OmniAgent</span>
          </Link>

          {/* Benefits */}
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">
              {language === "fr" ? "Tout ce que vous obtenez" : language === "ar" ? "كل ما ستحصل عليه" : "كل أشنو غادي تولي عندك"}
            </h2>
            <p className="text-white/70 mb-8 text-sm">
              {language === "fr" ? "Un compte gratuit, un accès complet." : "حساب مجاني، وصول كامل."}
            </p>
            <div className="flex flex-col gap-5">
              {BENEFITS.map((b, i) => (
                <motion.div
                  key={b.fr}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.2 + i * 0.1 }}
                  className="flex items-start gap-3"
                >
                  <CheckCircle className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                  <span className="text-white text-sm leading-snug">
                    {language === "fr" ? b.fr : language === "ar" ? b.ar : b.darija}
                  </span>
                </motion.div>
              ))}
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-5 mt-10 pt-8 border-t border-white/20">
              <div>
                <div className="text-2xl font-bold text-white">47,000+</div>
                <div className="text-xs text-white/60 mt-0.5">
                  {language === "fr" ? "Dossiers traités" : "طلب تمت معالجته"}
                </div>
              </div>
              <div>
                <div className="text-2xl font-bold text-white">98%</div>
                <div className="text-xs text-white/60 mt-0.5">
                  {language === "fr" ? "Satisfaction" : "نسبة الرضا"}
                </div>
              </div>
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

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <div className="rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-600" dir="ltr">
                {error}
              </div>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="fullName" className="text-sm font-medium">{getText("fullName")}</Label>
              <Input
                id="fullName"
                data-testid="input-fullname"
                placeholder={language === "fr" ? "Ahmed Benali" : "أحمد بنعلي"}
                value={form.fullName}
                onChange={update("fullName")}
                className="h-11"
                required
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-sm font-medium">{getText("email")}</Label>
              <Input
                id="email"
                type="email"
                data-testid="input-email"
                placeholder="ahmed@example.ma"
                value={form.email}
                onChange={update("email")}
                className="h-11"
                required
                dir="ltr"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="phone" className="text-sm font-medium">{getText("phone")}</Label>
              <Input
                id="phone"
                type="tel"
                data-testid="input-phone"
                placeholder="+212 6 XX XX XX XX"
                value={form.phone}
                onChange={update("phone")}
                className="h-11"
                dir="ltr"
              />
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="password" className="text-sm font-medium">{getText("password")}</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  data-testid="input-password"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={update("password")}
                  className={`h-11 ${isRtl ? "pl-10" : "pr-10"}`}
                  required
                  minLength={8}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className={`absolute top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground ${isRtl ? "left-3" : "right-3"}`}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {/* Password strength indicator */}
              {form.password.length > 0 && (
                <div className="flex gap-1 mt-2">
                  {[1, 2, 3].map((level) => (
                    <div
                      key={level}
                      className={`h-1 flex-1 rounded-full transition-colors ${
                        form.password.length >= level * 4
                          ? level === 1 ? "bg-red-400" : level === 2 ? "bg-amber-400" : "bg-green-400"
                          : "bg-border"
                      }`}
                    />
                  ))}
                </div>
              )}
            </div>

            <Button
              type="submit"
              data-testid="button-signup"
              className="w-full h-11 text-base gap-2 mt-2"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  {language === "fr" ? "Création..." : language === "ar" ? "جاري الإنشاء..." : "كيتصنع..."}
                </span>
              ) : (
                <>
                  {getText("submit")}
                  <Arrow className="w-4 h-4" />
                </>
              )}
            </Button>
          </form>




          <p className="mt-5 text-xs text-muted-foreground text-center leading-relaxed">
            {getText("terms")}
          </p>

          <p className="mt-5 text-sm text-muted-foreground text-center">
            {getText("hasAccount")}{" "}
            <Link href="/login" className="text-primary font-medium hover:underline">
              {getText("login")}
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
