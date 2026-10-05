import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { HomeSections } from "@/components/home/HomeSections";
import { Link } from "wouter";
import { motion } from "framer-motion";
import { ArrowRight, ArrowLeft, Bot, MapPin, ShieldCheck, Globe } from "lucide-react";
import "@/components/home/HomeTheme.css";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.55, delay: i * 0.1 } }),
};

export default function Home() {
  const { language, isRtl } = useI18n();
  const Arrow = isRtl ? ArrowLeft : ArrowRight;

  return (
    <AppLayout fullBleed className="omni-home-theme">
      {/* ── HERO ──────────────────────────────────────────────── */}
      <section className="home-hero relative flex min-h-[calc(100svh-4rem)] items-center overflow-hidden">
        {/* Background image — Hassan II Mosque Casablanca */}
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1548013146-72479768bada?q=85&w=2070&auto=format&fit=crop"
            alt="Mosquée Hassan II, Casablanca"
            className="w-full h-full object-cover"
          />
          <div className="home-hero-wash absolute inset-0" />
          <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
        </div>

        <div className={`relative z-10 mx-auto w-full max-w-[1600px] px-4 py-8 sm:px-6 sm:py-16 lg:px-10 lg:py-20 xl:px-14`}>
          <div className="grid gap-8 sm:gap-10 lg:grid-cols-12 lg:items-center lg:gap-12 xl:gap-16">
            {/* Left Column: Headline, Description & CTAs */}
            <div className={`lg:col-span-7 ${isRtl ? "text-right" : "text-left"}`}>
              <motion.div custom={0} variants={fadeUp} initial="hidden" animate="show">
                <Badge className="mb-3 max-w-full whitespace-normal border-primary/20 bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary sm:mb-5 sm:px-4 sm:text-sm">
                  {language === "fr" ? "Services publics • Assistance intelligente" : language === "ar" ? "خدمات عمومية • مساعدة ذكية" : "الخدمات العمومية • مواكبة ذكية"}
                </Badge>
              </motion.div>

              <motion.div custom={1} variants={fadeUp} initial="hidden" animate="show">
                <h1 className={`font-bold leading-[1.12] sm:leading-[1.08] text-foreground ${language === "fr" ? "text-3xl sm:text-5xl lg:text-5xl xl:text-6xl" : "text-3xl sm:text-5xl md:text-5xl lg:text-6xl"}`}>
                  {language === "fr" ? (
                    <>
                      Vos services administratifs,<br />
                      <span className="text-primary">plus simples et plus accessibles</span>
                      <span className="mt-2.5 sm:mt-4 block text-base sm:text-xl md:text-2xl font-normal leading-relaxed text-muted-foreground">
                        Un accompagnement clair à chaque étape de votre démarche
                      </span>
                    </>
                  ) : (
                    <>
                      <span className="text-primary">{language === "ar" ? "خدماتك الإدارية" : "الخدمات الإدارية ديالك"}</span><br />
                      {language === "ar" ? "أبسط وأسهل وصولاً" : "أبسط وأسهل ليك"}<br />
                      <span className="mt-2 sm:mt-3 block text-lg sm:text-2xl md:text-3xl font-normal leading-relaxed text-muted-foreground">
                        {language === "ar" ? "مواكبة واضحة في كل مرحلة من إجراءاتك" : "مواكبة واضحة فكل مرحلة من الإجراءات ديالك"}
                      </span>
                    </>
                  )}
                </h1>
              </motion.div>

              <motion.p
                custom={2} variants={fadeUp} initial="hidden" animate="show"
                className="mt-3.5 sm:mt-5 max-w-2xl text-sm sm:text-base lg:text-lg leading-relaxed text-muted-foreground"
              >
                {language === "fr"
                  ? "OmniAgent simplifie votre parcours administratif en vous guidant de la recherche d’information jusqu’à la préparation de votre dossier. Comprenez les démarches, organisez vos documents, vérifiez les éléments importants et accédez plus facilement au service adapté à votre situation."
                  : language === "ar"
                  ? "يسهّل OmniAgent مسارك الإداري، من البحث عن المعلومات إلى إعداد ملفك. تعرّف على الإجراءات، ونظّم وثائقك، وتحقّق من العناصر المهمة، واعثر بسهولة أكبر على الخدمة المناسبة لوضعك."
                  : "OmniAgent كيسهّل عليك المسار الإداري ديالك، من البحث على المعلومات حتى لوجد الملف ديالك. فهم الإجراءات، نظم الوثائق ديالك، تأكد من المعلومات المهمة، ووصل بسهولة أكثر للخدمة اللي مناسبة للحالة ديالك."}
              </motion.p>

              <motion.div
                custom={3} variants={fadeUp} initial="hidden" animate="show"
                className={`mt-6 sm:mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:gap-4 ${isRtl ? "sm:justify-start" : "sm:justify-start"}`}
              >
                <Button size="lg" asChild className="h-11 sm:h-12 w-full gap-2 px-5 sm:px-8 text-sm sm:text-base shadow-md sm:w-auto">
                  <Link href="/signup">
                    {language === "fr" ? "Créer mon compte citoyen" : language === "ar" ? "إنشاء حسابي كمواطن" : "نصايب الحساب ديالي كمواطن"}
                    <Arrow className="w-4 h-4" />
                  </Link>
                </Button>
                <Button size="lg" variant="secondary" asChild className="h-11 sm:h-12 w-full gap-2 px-5 sm:px-8 text-sm sm:text-base shadow-md sm:w-auto">
                  <Link href="/chat">
                    <Bot className="w-4 h-4 text-primary" />
                    {language === "fr" ? "Parler à l'IA" : language === "ar" ? "تحدث إلى المساعد الذكي" : "هضر مع المساعد الذكي"}
                  </Link>
                </Button>
              </motion.div>

              {/* Trust micro-badges */}
              <motion.div
                custom={4} variants={fadeUp} initial="hidden" animate="show"
                className={`mt-6 sm:mt-8 flex flex-wrap gap-2 sm:gap-3 ${isRtl ? "justify-start" : "justify-start"}`}
              >
                {[
                  { icon: MapPin, label: language === "fr" ? "Service 100% Marocain" : language === "ar" ? "خدمة مغربية 100٪" : "خدمة مغربية 100٪" },
                  { icon: ShieldCheck, label: language === "fr" ? "Données sécurisées" : language === "ar" ? "بيانات آمنة" : "المعطيات ديالك محمية" },
                  { icon: Globe, label: language === "fr" ? "AR · دارجة · FR" : language === "ar" ? "العربية · الدارجة · الفرنسية" : "العربية · الدارجة · الفرنسية" },
                ].map((badge) => (
                  <span
                    key={badge.label}
                    className={`inline-flex items-center gap-1.5 text-xs font-medium px-2.5 py-1 sm:px-3 sm:py-1.5 rounded-full bg-card/85 backdrop-blur-sm border border-border text-muted-foreground ${isRtl ? "flex-row-reverse" : ""}`}
                  >
                    <badge.icon className="w-3.5 h-3.5 text-primary shrink-0" />
                    {badge.label}
                  </span>
                ))}
              </motion.div>
            </div>

            {/* Right Column: Interactive Moroccan Administrative Showcase Card */}
            <motion.div
              custom={2}
              variants={fadeUp}
              initial="hidden"
              animate="show"
              className="lg:col-span-5"
            >
              <div className="relative rounded-2xl border border-primary/25 bg-card/95 p-4 sm:p-6 shadow-2xl backdrop-blur-md transition-all">
                {/* Card Top Glow */}
                <div className="pointer-events-none absolute -inset-px rounded-2xl bg-gradient-to-b from-primary/15 via-transparent to-transparent opacity-60" />

                {/* Assistant Status Header */}
                <div className="relative flex items-center justify-between border-b border-border/80 pb-3.5">
                  <div className="flex items-center gap-3">
                    <div className="relative grid size-10 place-items-center rounded-xl bg-primary/10 text-primary border border-primary/20 shadow-inner">
                      <Bot className="size-5" />
                      <span className="absolute -top-0.5 -end-0.5 size-2.5 rounded-full bg-emerald-500 ring-2 ring-card animate-pulse" />
                    </div>
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-sm font-bold text-foreground">OmniAgent Maroc</span>
                        <span className="rounded bg-primary/15 px-1.5 py-0.2 text-[10px] font-semibold text-primary">IA 2.0</span>
                      </div>
                      <p className="text-[11px] text-muted-foreground">
                        {language === "fr" ? "Assistant administratif en direct" : language === "ar" ? "مساعد إداري فوري" : "مساعد إداري مباشر"}
                      </p>
                    </div>
                  </div>

                  <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-500/10 px-2.5 py-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                    <span className="size-1.5 rounded-full bg-emerald-500" />
                    {language === "fr" ? "En ligne" : language === "ar" ? "متصل" : "واجد"}
                  </span>
                </div>

                {/* Simulated Conversation & Process Preview */}
                <div className="relative mt-4 space-y-3 text-xs sm:text-sm">
                  {/* Citizen Question */}
                  <div className={`flex items-start gap-2.5 ${isRtl ? "flex-row-reverse text-right" : "text-left"}`}>
                    <div className="grid size-7 shrink-0 place-items-center rounded-full bg-secondary/15 text-secondary text-xs font-bold">
                      🇲🇦
                    </div>
                    <div className="max-w-[85%] rounded-2xl rounded-tl-sm bg-muted/90 p-2.5 sm:p-3 text-foreground border border-border">
                      <p className="font-medium text-xs sm:text-sm">
                        {language === "fr"
                          ? "Comment renouveler ma Carte Nationale (CNIE) ?"
                          : language === "ar"
                          ? "كيف أجدد بطاقة التعريف الوطنية (CNIE)؟"
                          : "كيفاش نجدد لاكارط ناسيونال ديالي (CNIE)؟"}
                      </p>
                    </div>
                  </div>

                  {/* AI Response with 3-Step Verification Checklist */}
                  <div className={`flex items-start gap-2.5 ${isRtl ? "flex-row-reverse text-right" : "text-left"}`}>
                    <div className="grid size-7 shrink-0 place-items-center rounded-full bg-primary/15 text-primary">
                      <Bot className="size-3.5" />
                    </div>
                    <div className="flex-1 rounded-2xl rounded-tr-sm bg-primary/5 p-3 sm:p-3.5 border border-primary/15 space-y-2.5">
                      <p className="text-xs font-semibold text-primary">
                        {language === "fr"
                          ? "Démarche simplifiée en 3 pièces :"
                          : language === "ar"
                          ? "المسطرة مبسطة في 3 وثائق:"
                          : "الإجراء مبسط فـ 3 ديال الوثائق:"}
                      </p>

                      <div className="space-y-1.5 text-xs text-foreground/90">
                        <div className="flex items-center justify-between rounded-lg bg-card/80 px-2.5 py-1.5 border border-border/60">
                          <span className="flex items-center gap-2">
                            <span className="text-emerald-600 font-bold">✓</span>
                            <span>{language === "fr" ? "Rendez-vous sur cnie.ma" : language === "ar" ? "حجز موعد عبر cnie.ma" : "موعد فـ cnie.ma"}</span>
                          </span>
                          <span className="text-[10px] text-muted-foreground font-mono">100% en ligne</span>
                        </div>
                        <div className="flex items-center justify-between rounded-lg bg-card/80 px-2.5 py-1.5 border border-border/60">
                          <span className="flex items-center gap-2">
                            <span className="text-emerald-600 font-bold">✓</span>
                            <span>{language === "fr" ? "Certificat de résidence / Quittance" : language === "ar" ? "شهادة السكنى أو فاتورة ماء/كهرباء" : "شهادة السكنى أو فاتورة"}</span>
                          </span>
                          <span className="text-[10px] text-muted-foreground font-mono">&lt; 3 mois</span>
                        </div>
                        <div className="flex items-center justify-between rounded-lg bg-card/80 px-2.5 py-1.5 border border-border/60">
                          <span className="flex items-center gap-2">
                            <span className="text-emerald-600 font-bold">✓</span>
                            <span>{language === "fr" ? "2 photos d'identité officielles" : language === "ar" ? "صورتان شمسيتان بيومتريتان" : "2 تصاور رسميين"}</span>
                          </span>
                          <span className="text-[10px] text-muted-foreground font-mono">35×45mm</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Moroccan Administrative Trust Strip */}
                <div className="mt-4 pt-3.5 border-t border-border flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-foreground">
                  <div className="flex items-center gap-1 font-medium text-foreground">
                    <span className="text-amber-500">★★★★★</span>
                    <span>4.9/5</span>
                    <span className="text-muted-foreground">• 47 000+ citoyens</span>
                  </div>
                  <span className="inline-flex items-center gap-1 font-medium text-primary">
                    <ShieldCheck className="size-3.5" />
                    {language === "fr" ? "Loi 09-08 CNDP" : language === "ar" ? "قانون 09-08 CNDP" : "قانون 09-08 CNDP"}
                  </span>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      <HomeSections />
    </AppLayout>
  );
}
