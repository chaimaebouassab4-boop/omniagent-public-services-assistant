import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { HomeSections } from "@/components/home/HomeSections";
import { Link } from "wouter";
import { motion } from "framer-motion";
import { ArrowRight, ArrowLeft, Bot, MapPin, ShieldCheck, Globe } from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.55, delay: i * 0.1 } }),
};

export default function Home() {
  const { language, isRtl } = useI18n();
  const Arrow = isRtl ? ArrowLeft : ArrowRight;

  return (
    <AppLayout fullBleed>
      {/* ── HERO ──────────────────────────────────────────────── */}
      <section className="relative flex min-h-[calc(100svh-4rem)] items-center overflow-hidden">
        {/* Background image — Hassan II Mosque Casablanca */}
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1548013146-72479768bada?q=85&w=2070&auto=format&fit=crop"
            alt="Mosquée Hassan II, Casablanca"
            className="w-full h-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-r from-background via-background/80 to-background/20 dark:from-background dark:via-background/90 dark:to-background/40" />
          <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
        </div>

        <div className={`relative z-10 mx-auto w-full max-w-[1600px] px-4 py-14 sm:px-6 sm:py-20 lg:px-10 lg:py-24 xl:px-14 ${isRtl ? "text-right" : "text-left"}`}>
          <motion.div custom={0} variants={fadeUp} initial="hidden" animate="show">
            <Badge className="mb-4 max-w-full whitespace-normal border-primary/20 bg-primary/10 px-3 py-1.5 text-xs font-medium text-primary sm:mb-6 sm:px-4 sm:text-sm">
              {language === "fr" ? "Services publics • Assistance intelligente" : language === "ar" ? "خدمات عمومية • مساعدة ذكية" : "الخدمات العمومية • مواكبة ذكية"}
            </Badge>
          </motion.div>

          <motion.div custom={1} variants={fadeUp} initial="hidden" animate="show">
            <h1 className={`font-bold leading-[1.08] text-foreground ${language === "fr" ? "max-w-5xl text-4xl sm:text-5xl lg:text-6xl" : "max-w-4xl text-4xl sm:text-5xl md:text-6xl lg:text-7xl"}`}>
              {language === "fr" ? (
                <>
                  Vos services administratifs,<br />
                  <span className="text-primary">plus simples et plus accessibles</span>
                  <span className="mt-5 block max-w-3xl text-lg font-normal leading-relaxed text-muted-foreground sm:text-xl md:text-2xl">
                    Un accompagnement clair à chaque étape de votre démarche
                  </span>
                </>
              ) : (
                <>
                  <span className="text-primary">{language === "ar" ? "خدماتك الإدارية" : "الخدمات الإدارية ديالك"}</span><br />
                  {language === "ar" ? "أبسط وأسهل وصولاً" : "أبسط وأسهل ليك"}<br />
                  <span className="mt-3 block text-xl font-normal leading-relaxed text-muted-foreground sm:text-2xl md:text-3xl lg:text-4xl">
                    {language === "ar" ? "مواكبة واضحة في كل مرحلة من إجراءاتك" : "مواكبة واضحة فكل مرحلة من الإجراءات ديالك"}
                  </span>
                </>
              )}
            </h1>
          </motion.div>

          <motion.p
            custom={2} variants={fadeUp} initial="hidden" animate="show"
            className="mt-5 max-w-2xl text-base leading-relaxed text-muted-foreground sm:mt-6 sm:text-lg"
          >
            {language === "fr"
              ? "OmniAgent simplifie votre parcours administratif en vous guidant de la recherche d’information jusqu’à la préparation de votre dossier. Comprenez les démarches, organisez vos documents, vérifiez les éléments importants et accédez plus facilement au service adapté à votre situation."
              : language === "ar"
              ? "يسهّل OmniAgent مسارك الإداري، من البحث عن المعلومات إلى إعداد ملفك. تعرّف على الإجراءات، ونظّم وثائقك، وتحقّق من العناصر المهمة، واعثر بسهولة أكبر على الخدمة المناسبة لوضعك."
              : "OmniAgent كيسهّل عليك المسار الإداري ديالك، من البحث على المعلومات حتى لوجد الملف ديالك. فهم الإجراءات، نظم الوثائق ديالك، تأكد من المعلومات المهمة، ووصل بسهولة أكثر للخدمة اللي مناسبة للحالة ديالك."}
          </motion.p>

          <motion.div
            custom={3} variants={fadeUp} initial="hidden" animate="show"
            className={`mt-8 flex flex-col gap-3 sm:mt-10 sm:flex-row sm:flex-wrap sm:gap-4 ${isRtl ? "sm:justify-end" : "sm:justify-start"}`}
          >
            <Button size="lg" asChild className="h-12 w-full gap-2 px-6 text-base shadow-md sm:w-auto sm:px-8">
              <Link href="/signup">
                {language === "fr" ? "Créer mon compte citoyen" : language === "ar" ? "إنشاء حسابي كمواطن" : "نصايب الحساب ديالي كمواطن"}
                <Arrow className="w-4 h-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="h-12 w-full gap-2 px-6 text-base sm:w-auto sm:px-8">
              <Link href="/chat">
                <Bot className="w-4 h-4" />
                {language === "fr" ? "Parler à l'IA" : language === "ar" ? "تحدث إلى المساعد الذكي" : "هضر مع المساعد الذكي"}
              </Link>
            </Button>
          </motion.div>

          {/* Trust micro-badges */}
          <motion.div
            custom={4} variants={fadeUp} initial="hidden" animate="show"
            className={`mt-8 flex flex-wrap gap-2 sm:mt-10 sm:gap-3 ${isRtl ? "justify-end" : "justify-start"}`}
          >
            {[
              { icon: MapPin, label: language === "fr" ? "Service 100% Marocain" : language === "ar" ? "خدمة مغربية 100٪" : "خدمة مغربية 100٪" },
              { icon: ShieldCheck, label: language === "fr" ? "Données sécurisées" : language === "ar" ? "بيانات آمنة" : "المعطيات ديالك محمية" },
              { icon: Globe, label: language === "fr" ? "AR · دارجة · FR" : language === "ar" ? "العربية · الدارجة · الفرنسية" : "العربية · الدارجة · الفرنسية" },
            ].map((badge) => (
              <span
                key={badge.label}
                className={`inline-flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-full bg-card border border-border text-muted-foreground ${isRtl ? "flex-row-reverse" : ""}`}
              >
                <badge.icon className="w-3.5 h-3.5 text-primary" />
                {badge.label}
              </span>
            ))}
          </motion.div>
        </div>
      </section>

      <HomeSections />
    </AppLayout>
  );
}
