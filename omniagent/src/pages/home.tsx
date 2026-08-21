import { useI18n } from "@/lib/i18n";
import { MainLayout } from "@/components/layout/MainLayout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Link } from "wouter";
import { motion } from "framer-motion";
import {
  ArrowRight, ArrowLeft, Bot, Clock, ShieldCheck, Star,
  CreditCard, BookOpen, FileText, Home as HomeIcon, Heart, Activity,
  CheckCircle, ChevronRight, MapPin, Globe, Scale, Shield, Users
} from "lucide-react";

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.55, delay: i * 0.1 } }),
};

const SERVICES_PREVIEW = [
  { icon: HomeIcon, nameAr: "شهادة السكنى", nameFr: "Certificat de Résidence", nameDarija: "شهادة السكنى", days: 3, color: "bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400" },
  { icon: FileText, nameAr: "عقد الازدياد", nameFr: "Acte de Naissance", nameDarija: "عقد الازدياد", days: 2, color: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400" },
  { icon: Heart, nameAr: "عقد الزواج", nameFr: "Acte de Mariage", nameDarija: "عقد الزواج", days: 5, color: "bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400" },
  { icon: Activity, nameAr: "شهادة الحياة", nameFr: "Certificat de Vie", nameDarija: "شهادة الحياة", days: 1, color: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" },
  { icon: ShieldCheck, nameAr: "شهادة حسن السيرة", nameFr: "Fiche anthropométrique", nameDarija: "شهادة حسن السيرة", days: 5, color: "bg-cyan-100 text-cyan-700 dark:bg-cyan-900/30 dark:text-cyan-400" },
  { icon: Scale, nameAr: "السجل العدلي", nameFr: "Extrait du Casier Judiciaire", nameDarija: "السجل العدلي", days: 7, color: "bg-primary/10 text-primary" },
];

const TESTIMONIALS = [
  {
    nameAr: "فاطمة الزهراء الموساوي",
    nameFr: "Fatima Zahra Moussaoui",
    city: "Casablanca",
    avatar: "https://images.unsplash.com/photo-1531123897727-8f129e1688ce?w=80&h=80&fit=crop&crop=face",
    stars: 5,
    textFr: "J'ai obtenu mon attestation de résidence en 3 jours. OmniAgent m'a guidée étape par étape, je n'avais jamais utilisé un service en ligne aussi simple.",
    textAr: "حصلت على شهادة الإقامة في 3 أيام. أرشدني OmniAgent خطوة بخطوة، ولم أستخدم قط خدمة إلكترونية بهذه السهولة.",
    textDarija: "جبت شهادة السكنى ف 3 أيام. OmniAgent عاونني خطوة بخطوة، ما شفتش خدمة سهلة بحالها.",
  },
  {
    nameAr: "يوسف العلمي",
    nameFr: "Youssef Alami",
    city: "Rabat",
    avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=80&h=80&fit=crop&crop=face",
    stars: 5,
    textFr: "Renouveler mon passeport semblait compliqué. Grâce à cet assistant, j'ai su exactement quels documents préparer. Zéro allers-retours inutiles.",
    textAr: "بدا لي تجديد جواز سفري معقداً. بفضل هذا المساعد عرفت بالضبط أي وثائق أحتاج. لا ذهاب وإياب غير ضروري.",
    textDarija: "كان عندي مشكل في تجديد جواز السفر. هاد المساعد عاونني نعرف بالضبط أشنو خصني نجيب. ما رجعتش مرتين.",
  },
  {
    nameAr: "نادية الشرايبي",
    nameFr: "Nadia Chraibi",
    city: "Fès",
    avatar: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=80&h=80&fit=crop&crop=face",
    stars: 5,
    textFr: "En tant que chef d'entreprise, je devais ouvrir un registre de commerce. OmniAgent m'a mâché tout le travail. Parfait.",
    textAr: "بصفتي صاحبة شركة، كنت بحاجة لتسجيل سجل تجاري. OmniAgent أنجز كل العمل عني. مثالي.",
    textDarija: "أنا صاحبة شركة وكنت محتاجة نفتح سجل تجاري. OmniAgent دار ليا كل شي. كامل.",
  },
];

const STATS = [
  { value: "47,000+", labelFr: "Demandes traitées", labelAr: "طلب تمت معالجته" },
  { value: "98%", labelFr: "Taux de satisfaction", labelAr: "نسبة الرضا" },
  { value: "3 langues", labelFr: "Prise en charge", labelAr: "لغة مدعومة" },
  { value: "24/7", labelFr: "Disponibilité", labelAr: "متاح دائماً" },
];

export default function Home() {
  const { t, language, isRtl } = useI18n();
  const Arrow = isRtl ? ArrowLeft : ArrowRight;

  const getServiceName = (s: typeof SERVICES_PREVIEW[0]) => {
    if (language === "darija") return s.nameDarija;
    if (language === "ar") return s.nameAr;
    return s.nameFr;
  };

  const getTestimonialText = (t: typeof TESTIMONIALS[0]) => {
    if (language === "ar") return t.textAr;
    if (language === "darija") return t.textDarija;
    return t.textFr;
  };

  return (
    <MainLayout>
      {/* ── HERO ──────────────────────────────────────────────── */}
      <section className="relative min-h-[92vh] flex items-center overflow-hidden">
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

        <div className={`container relative z-10 mx-auto px-4 py-24 ${isRtl ? "text-right" : "text-left"}`}>
          <motion.div custom={0} variants={fadeUp} initial="hidden" animate="show">
            <Badge className="mb-6 px-4 py-1.5 text-sm font-medium bg-primary/10 text-primary border-primary/20">
              {language === "fr" ? "Intelligence Artificielle • خدمات إدارية" : language === "ar" ? "الذكاء الاصطناعي • خدمات إدارية" : "الذكاء الاصطناعي • خدمات إدارية"}
            </Badge>
          </motion.div>

          {/* Arabic/Darija title always shown large */}
          <motion.div custom={1} variants={fadeUp} initial="hidden" animate="show">
            <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-tight text-foreground max-w-3xl">
              {language === "fr" ? (
                <>
                  Vos démarches<br />
                  <span className="text-primary">administratives</span><br />
                  <span className="text-3xl sm:text-4xl text-muted-foreground font-normal mt-2 block" dir="rtl">
                    إجراءاتك الإدارية بسهولة — خدمات ديالك بسرعة
                  </span>
                </>
              ) : (
                <>
                  <span className="text-primary">إجراءاتك الإدارية</span><br />
                  بسهولة وذكاء<br />
                  <span className="text-3xl sm:text-4xl text-muted-foreground font-normal mt-2 block">
                    Vos démarches simplifiées
                  </span>
                </>
              )}
            </h1>
          </motion.div>

          <motion.p
            custom={2} variants={fadeUp} initial="hidden" animate="show"
            className="mt-6 max-w-xl text-lg text-muted-foreground leading-relaxed"
          >
            {language === "fr"
              ? "OmniAgent vous guide à travers toutes les procédures administratives marocaines — CIN, passeport, actes d'état civil — en arabe, darija ou français."
              : language === "ar"
              ? "أومني إيجنت يرشدك خلال جميع الإجراءات الإدارية المغربية — بطاقة التعريف الوطنية، جواز السفر، وثائق الحالة المدنية — بالعربية أو الدارجة أو الفرنسية."
              : "OmniAgent كيعاونك في جميع الإجراءات الإدارية المغربية — البطاقة الوطنية، جواز السفر، وثائق الحالة المدنية — بالعربية أو الدارجة أو الفرنساوية."}
          </motion.p>

          <motion.div
            custom={3} variants={fadeUp} initial="hidden" animate="show"
            className={`mt-10 flex flex-wrap gap-4 ${isRtl ? "justify-end" : "justify-start"}`}
          >
            <Button size="lg" asChild className="gap-2 text-base px-8 h-12 shadow-lg">
              <Link href="/signup">
                {language === "fr" ? "Commencer gratuitement" : language === "ar" ? "ابدأ مجاناً" : "بدا دابا مجاناً"}
                <Arrow className="w-4 h-4" />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild className="gap-2 text-base px-8 h-12">
              <Link href="/chat">
                <Bot className="w-4 h-4" />
                {language === "fr" ? "Parler à l'IA" : language === "ar" ? "تحدث مع الذكاء الاصطناعي" : "هضر مع الذكاء الاصطناعي"}
              </Link>
            </Button>
          </motion.div>

          {/* Trust micro-badges */}
          <motion.div
            custom={4} variants={fadeUp} initial="hidden" animate="show"
            className={`mt-10 flex flex-wrap gap-3 ${isRtl ? "justify-end" : "justify-start"}`}
          >
            {[
              { icon: MapPin, label: "Service 100% Marocain" },
              { icon: ShieldCheck, label: "Données sécurisées" },
              { icon: Globe, label: "AR · دارجة · FR" },
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

      {/* ── STATS BAR ─────────────────────────────────────────── */}
      <section className="bg-primary py-10">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
            {STATS.map((s, i) => (
              <motion.div
                key={s.value}
                custom={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
              >
                <div className="text-3xl font-bold text-white">{s.value}</div>
                <div className="text-sm mt-1 text-white/70">
                  {language === "ar" || language === "darija" ? s.labelAr : s.labelFr}
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── SERVICES PREVIEW ──────────────────────────────────── */}
      <section className="py-24 bg-muted/40">
        <div className="container mx-auto px-4">
          <motion.div
            variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
            className={`mb-12 ${isRtl ? "text-right" : "text-left"}`}
          >
            <p className="text-sm font-semibold text-primary uppercase tracking-widest mb-2">
              {language === "fr" ? "Nos services" : "خدماتنا"}
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
              {language === "fr" ? "Toutes vos démarches, un seul endroit" : language === "ar" ? "جميع إجراءاتك في مكان واحد" : "جميع خدماتك ف بلاصة واحدة"}
            </h2>
            <p className="mt-3 text-muted-foreground max-w-xl">
              {language === "fr"
                ? "De la carte d'identité au registre de commerce — nous couvrons l'ensemble des services administratifs marocains."
                : language === "ar"
                ? "من بطاقة التعريف الوطنية إلى السجل التجاري — نغطي جميع الخدمات الإدارية المغربية."
                : "من البطاقة الوطنية حتى السجل التجاري — كنغطيو جميع الخدمات الإدارية المغربية."}
            </p>
          </motion.div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {SERVICES_PREVIEW.map((svc, i) => (
              <motion.div
                key={svc.nameFr}
                custom={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
                className="bg-card border border-border rounded-2xl p-6 flex items-start gap-4 hover:shadow-md transition-all hover:-translate-y-0.5 cursor-pointer group"
              >
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${svc.color}`}>
                  <svc.icon className="w-6 h-6" />
                </div>
                <div className="flex-1 min-w-0">
                  <h3 className="font-semibold text-foreground leading-snug">{getServiceName(svc)}</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">{svc.nameFr !== getServiceName(svc) ? svc.nameFr : svc.nameAr}</p>
                  <div className="flex items-center gap-1.5 mt-2">
                    <Clock className="w-3 h-3 text-muted-foreground" />
                    <span className="text-xs text-muted-foreground">
                      {svc.days} {language === "fr" ? "jours" : "أيام"}
                    </span>
                  </div>
                </div>
                <ChevronRight className={`w-4 h-4 text-muted-foreground shrink-0 group-hover:text-primary transition-colors ${isRtl ? "rotate-180" : ""}`} />
              </motion.div>
            ))}
          </div>

          <motion.div
            variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
            className="mt-10 text-center"
          >
            <Button variant="outline" size="lg" asChild className="gap-2">
              <Link href="/services">
                {language === "fr" ? "Voir tous les services" : language === "ar" ? "عرض جميع الخدمات" : "شوف جميع الخدمات"}
                <Arrow className="w-4 h-4" />
              </Link>
            </Button>
          </motion.div>
        </div>
      </section>

      {/* ── HOW IT WORKS ──────────────────────────────────────── */}
      <section className="py-24 bg-background">
        <div className="container mx-auto px-4">
          <motion.div
            variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
            className={`mb-12 text-center`}
          >
            <p className="text-sm font-semibold text-primary uppercase tracking-widest mb-2">
              {language === "fr" ? "Comment ça marche" : language === "ar" ? "كيف يعمل" : "كيفاش خدام"}
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
              {language === "fr" ? "3 étapes simples" : language === "ar" ? "٣ خطوات بسيطة" : "3 خطوات بسيطة"}
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8 relative">
            {/* Connecting line */}
            <div className="hidden md:block absolute top-8 left-1/3 right-1/3 h-0.5 bg-border" />

            {[
              {
                num: "01",
                icon: FileText,
                fr: "Choisissez votre service",
                ar: "اختر خدمتك",
                darija: "اختار الخدمة ديالك",
                descFr: "Sélectionnez parmi nos 8 services administratifs officiels.",
                descAr: "اختر من بين 8 خدمات إدارية رسمية.",
                descDarija: "اختار من بين 8 خدمات إدارية رسمية.",
              },
              {
                num: "02",
                icon: Bot,
                fr: "Parlez à l'IA",
                ar: "تحدث مع الذكاء الاصطناعي",
                darija: "هضر مع الذكاء الاصطناعي",
                descFr: "Notre assistant répond en arabe, darija ou français et liste exactement ce qu'il vous faut.",
                descAr: "يجيب مساعدنا بالعربية أو الدارجة أو الفرنسية ويحدد بالضبط ما تحتاجه.",
                descDarija: "المساعد ديالنا كيجاوبك بالعربية أو الدارجة أو الفرنساوية وكيقولك بالضبط أشنو خصك.",
              },
              {
                num: "03",
                icon: CheckCircle,
                fr: "Suivez votre dossier",
                ar: "تابع ملفك",
                darija: "تبع ملفك",
                descFr: "Recevez des mises à jour en temps réel sur l'avancement de votre demande.",
                descAr: "احصل على تحديثات في الوقت الفعلي حول تقدم طلبك.",
                descDarija: "واخد updates بالوقت الحقيقي على حالة الطلب ديالك.",
              },
            ].map((step, i) => (
              <motion.div
                key={step.num}
                custom={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
                className={`text-center flex flex-col items-center gap-4 ${isRtl ? "text-right items-end" : ""}`}
              >
                <div className="relative">
                  <div className="w-16 h-16 bg-primary rounded-2xl flex items-center justify-center shadow-lg">
                    <step.icon className="w-7 h-7 text-white" />
                  </div>
                  <span className="absolute -top-2 -right-2 w-6 h-6 bg-accent rounded-full text-xs font-bold flex items-center justify-center text-accent-foreground">
                    {step.num}
                  </span>
                </div>
                <h3 className="text-xl font-bold text-foreground">
                  {language === "fr" ? step.fr : language === "ar" ? step.ar : step.darija}
                </h3>
                <p className="text-muted-foreground text-sm leading-relaxed max-w-xs">
                  {language === "fr" ? step.descFr : language === "ar" ? step.descAr : step.descDarija}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── MOROCCAN ADMIN VISUAL ─────────────────────────────── */}
      <section className="py-0 relative overflow-hidden">
        <div className="grid lg:grid-cols-2 min-h-[460px]">
          <div className="relative">
            <img
              src="https://images.unsplash.com/photo-1489749798305-4fea3ae63d43?q=80&w=1200&auto=format&fit=crop"
              alt="Médina de Marrakech"
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-r from-transparent to-background hidden lg:block" />
          </div>
          <div className={`flex flex-col justify-center px-10 py-16 bg-background ${isRtl ? "text-right" : "text-left"}`}>
            <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}>
              <p className="text-sm font-semibold text-primary uppercase tracking-widest mb-3">
                {language === "fr" ? "Contexte administratif" : "السياق الإداري"}
              </p>
              <h2 className="text-3xl font-bold text-foreground mb-4">
                {language === "fr"
                  ? "Conçu pour les citoyens marocains"
                  : language === "ar"
                  ? "مصمم للمواطنين المغاربة"
                  : "مصمم للمواطنين المغاربة"}
              </h2>
              <p className="text-muted-foreground leading-relaxed mb-6">
                {language === "fr"
                  ? "OmniAgent est entraîné sur les procédures officielles du Ministère de l'Intérieur, du Consulat, et des services de l'État Civil marocain. Chaque réponse est basée sur les textes réglementaires en vigueur."
                  : language === "ar"
                  ? "تم تدريب OmniAgent على الإجراءات الرسمية لوزارة الداخلية والقنصليات وخدمات الحالة المدنية المغربية. كل إجابة مبنية على النصوص التنظيمية المعمول بها."
                  : "OmniAgent تدرب على الإجراءات الرسمية ديال وزارة الداخلية والقنصليات وخدمات الحالة المدنية المغربية. كل جواب مبني على النصوص التنظيمية المعمول بها."}
              </p>
              <div className="flex flex-col gap-3">
                {[
                  { fr: "Procédures officielles du Maroc", ar: "إجراءات رسمية مغربية" },
                  { fr: "Mis à jour régulièrement", ar: "محدّث باستمرار" },
                  { fr: "Disponible en 3 langues (AR · دارجة · FR)", ar: "متاح بـ 3 لغات (AR · دارجة · FR)" },
                ].map((item) => (
                  <div key={item.fr} className={`flex items-center gap-3 ${isRtl ? "flex-row-reverse" : ""}`}>
                    <CheckCircle className="w-5 h-5 text-primary shrink-0" />
                    <span className="text-sm text-foreground font-medium">
                      {language === "fr" ? item.fr : item.ar}
                    </span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ──────────────────────────────────────── */}
      <section className="py-24 bg-muted/40">
        <div className="container mx-auto px-4">
          <motion.div
            variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
            className="text-center mb-14"
          >
            <p className="text-sm font-semibold text-primary uppercase tracking-widest mb-2">
              {language === "fr" ? "Témoignages" : language === "ar" ? "شهادات المستخدمين" : "شهادات المستخدمين"}
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground">
              {language === "fr"
                ? "Ce que disent nos utilisateurs"
                : language === "ar"
                ? "ما يقوله مستخدمونا"
                : "أشنو كيقولو المستخدمين"}
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {TESTIMONIALS.map((tmpl, i) => (
              <motion.div
                key={tmpl.nameFr}
                custom={i} variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}
                className="bg-card border border-border rounded-2xl p-7 flex flex-col gap-5 shadow-sm hover:shadow-md transition-shadow"
              >
                {/* Stars */}
                <div className="flex gap-1">
                  {Array.from({ length: tmpl.stars }).map((_, j) => (
                    <Star key={j} className="w-4 h-4 fill-amber-400 text-amber-400" />
                  ))}
                </div>
                {/* Quote */}
                <blockquote
                  className={`text-foreground leading-relaxed text-sm flex-1 ${(language === "ar" || language === "darija") ? "text-right" : ""}`}
                  dir={language === "ar" || language === "darija" ? "rtl" : "ltr"}
                >
                  "{getTestimonialText(tmpl)}"
                </blockquote>
                {/* Author */}
                <div className={`flex items-center gap-3 ${isRtl ? "flex-row-reverse" : ""}`}>
                  <img
                    src={tmpl.avatar}
                    alt={tmpl.nameFr}
                    className="w-10 h-10 rounded-full object-cover border-2 border-border"
                  />
                  <div className={isRtl ? "text-right" : "text-left"}>
                    <p className="text-sm font-semibold text-foreground">
                      {language === "fr" ? tmpl.nameFr : tmpl.nameAr}
                    </p>
                    <p className="text-xs text-muted-foreground">{tmpl.city}, Maroc</p>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA FINAL ─────────────────────────────────────────── */}
      <section className="py-24 bg-primary">
        <div className="container mx-auto px-4 text-center">
          <motion.div variants={fadeUp} initial="hidden" whileInView="show" viewport={{ once: true }}>
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">
              {language === "fr"
                ? "Prêt à simplifier vos démarches ?"
                : language === "ar"
                ? "هل أنت مستعد لتبسيط إجراءاتك؟"
                : "واش مستعد تبسط إجراءاتك؟"}
            </h2>
            <p className="text-white/80 text-lg mb-8 max-w-xl mx-auto">
              {language === "fr"
                ? "Rejoignez des milliers de Marocains qui gèrent leurs papiers intelligemment."
                : language === "ar"
                ? "انضم لآلاف المغاربة الذين يديرون وثائقهم بذكاء."
                : "انضم لآلاف المغاربة اللي كيديرو وثائقهم بذكاء."}
            </p>
            <div className="flex flex-wrap gap-4 justify-center">
              <Button size="lg" variant="secondary" asChild className="px-10 h-12 text-base font-semibold">
                <Link href="/signup">
                  {language === "fr" ? "Créer un compte gratuit" : language === "ar" ? "إنشاء حساب مجاني" : "ابدأ مجاناً"}
                </Link>
              </Button>
              <Button size="lg" variant="outline" asChild className="px-10 h-12 text-base border-white/30 text-white hover:bg-white/10">
                <Link href="/services">
                  {language === "fr" ? "Voir les services" : language === "ar" ? "عرض الخدمات" : "شوف الخدمات"}
                </Link>
              </Button>
            </div>
          </motion.div>
        </div>
      </section>
    </MainLayout>
  );
}
