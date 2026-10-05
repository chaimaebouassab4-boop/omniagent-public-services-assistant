import { useState } from "react";
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import {
  ArrowUpRight,
  Compass,
  Copy,
  FolderOpen,
  Route,
  ScanLine,
  Send,
  CheckCircle2,
  Clock,
  Landmark,
  Lock,
  ShieldCheck,
  Sparkles,
  MapPin,
  Bell,
} from "lucide-react";
import { Link } from "wouter";
import { Accordion, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { isAuthenticated } from "@/lib/auth";
import { useI18n } from "@/lib/i18n";
import "./OmniAgentJourney.css";

// Stable IDs preserve the selected step when the language changes.
const steps = [
  { id: "comprendre", icon: Compass, href: "/services", requiresAuth: false },
  { id: "preparer", icon: FolderOpen, href: "/services", requiresAuth: false },
  { id: "reutiliser", icon: Copy, href: "/profile", requiresAuth: true },
  { id: "verifier", icon: ScanLine, href: "/profile", requiresAuth: true },
  { id: "agir", icon: Send, href: "/#trouver-un-service", requiresAuth: false },
  { id: "suivre", icon: Route, href: "/history", requiresAuth: true },
];

const STEP_VISUALS: Record<
  string,
  {
    badge: { fr: string; ar: string; darija: string };
    pills: Array<{ icon: any; fr: string; ar: string; darija: string }>;
  }
> = {
  comprendre: {
    badge: { fr: "Synthèse Administrative", ar: "الدليل الإداري الموحد", darija: "الدليل الإداري" },
    pills: [
      { icon: Clock, fr: "Délais moyens vérifiés", ar: "الآجال القانونية محددة", darija: "الآجال محددة" },
      { icon: Landmark, fr: "Compétence territoriale", ar: "الإدارة المختصة موضحة", darija: "المقاطعة المحددة" },
      { icon: CheckCircle2, fr: "Frais officiels sans surprise", ar: "الرسوم الرسمية واضحة", darija: "المصاريف الرسمية باينة" },
    ],
  },
  preparer: {
    badge: { fr: "Checklist Personnalisée", ar: "لائحة الوثائق المخصصة", darija: "لائحة الوثائق" },
    pills: [
      { icon: CheckCircle2, fr: "Pièce d'identité (CIN)", ar: "بطاقة التعريف الوطنية", darija: "لاكارط ناسيونال" },
      { icon: CheckCircle2, fr: "Justificatif de domicile", ar: "إثبات السكنى", darija: "شهادة السكنى" },
      { icon: CheckCircle2, fr: "Photos réglementaires", ar: "صور مطابقة للمواصفات", darija: "تصاور رسميين" },
    ],
  },
  reutiliser: {
    badge: { fr: "Coffre-fort Sécurisé", ar: "خزانة رقمية آمنة", darija: "فضاء آمن للوثائق" },
    pills: [
      { icon: Lock, fr: "Chiffrement AES-256", ar: "تشفير عالي الأمان", darija: "حماية مشددة" },
      { icon: Copy, fr: "0 saisie répétée", ar: "بدون تكرار إدخال البيانات", darija: "بلا ما تعاود تكتب" },
      { icon: ShieldCheck, fr: "Confidentialité totale", ar: "سرية تامة للمعطيات", darija: "سرية تامة" },
    ],
  },
  verifier: {
    badge: { fr: "Contrôle Qualité IA", ar: "فحص الجودة بالذكاء الاصطناعي", darija: "مراقبة ذكية" },
    pills: [
      { icon: Sparkles, fr: "Lisibilité des scans", ar: "فحص وضوح النسخ", darija: "وضوح الوثائق" },
      { icon: CheckCircle2, fr: "Vérification des dates", ar: "التأكد من تواريخ الصلاحية", darija: "تأكيد الصلاحية" },
      { icon: ShieldCheck, fr: "0 dossier rejeté", ar: "تقليص مخاطر الرفض", darija: "تفادي الرفض" },
    ],
  },
  agir: {
    badge: { fr: "Orientation & Dépôt", ar: "التوجيه ونقط الإيداع", darija: "التوجيه والمقاطعة" },
    pills: [
      { icon: MapPin, fr: "Annexe / Guichet identifié", ar: "تحديد الملحقة الإدارية", darija: "المقاطعة المحددة" },
      { icon: Clock, fr: "Créneaux recommandés", ar: "مواقيت الاستقبال الموصى بها", darija: "أوقات الخدمة" },
      { icon: Send, fr: "Bordereau prêt à déposer", ar: "ملف منظم وجاهز للإيداع", darija: "ملف واجد" },
    ],
  },
  suivre: {
    badge: { fr: "Tableau de Bord & Alertes", ar: "تتبع الإجراء والإشعارات", darija: "التتبع والإشعارات" },
    pills: [
      { icon: Route, fr: "Progression en direct", ar: "متابعة تقدم المعالجة", darija: "تتبع مباشر" },
      { icon: Bell, fr: "Rappels et notifications", ar: "تنبيهات عند كل مستجد", darija: "تنبيهات فورية" },
      { icon: CheckCircle2, fr: "Historique archivé", ar: "أرشيف كامل لطلباتك", darija: "أرشيف كامل" },
    ],
  },
};

export function OmniAgentJourney() {
  const { t, language, isRtl } = useI18n();
  const [activeStep, setActiveStep] = useState(steps[0].id);
  const activeIndex = steps.findIndex((step) => step.id === activeStep);

  return (
    <section id="accompagnement" aria-labelledby="accompagnement-title" dir={isRtl ? "rtl" : "ltr"} className="omni-journey relative isolate scroll-mt-24 py-10 text-start sm:py-16 lg:py-20">
      <div className="relative z-10 mx-auto grid w-full max-w-7xl gap-6 px-4 sm:gap-8 sm:px-6 lg:grid-cols-[0.85fr_1.15fr] lg:items-start lg:gap-16">
        <div className="lg:sticky lg:top-28">
          <p className="omni-journey-accent mb-3 sm:mb-4 flex items-center gap-2.5 sm:gap-3 text-xs font-semibold uppercase tracking-[0.16em] rtl:tracking-normal">
            <span aria-hidden="true" className="h-px w-6 sm:w-8 bg-primary" />{t("home.journey.eyebrow")}
          </p>
          <h2 id="accompagnement-title" className="max-w-xl text-2xl font-bold leading-[1.2] tracking-tight text-foreground sm:text-3xl lg:text-[2.65rem]">
            {t("home.journey.title")} <span className="omni-journey-accent">{t("home.journey.titleAccent")}</span>
          </h2>
          <p className="mt-3.5 sm:mt-5 max-w-lg text-xs sm:text-base leading-relaxed sm:leading-7 text-muted-foreground">
            {t("home.journey.description")}
          </p>

          <div className="mt-4 sm:mt-6 flex items-center gap-2.5 sm:gap-3 text-xs sm:text-sm text-muted-foreground lg:mt-9">
            <Compass aria-hidden="true" className="h-4 w-4 shrink-0 text-primary" />
            <p>{t("home.journey.hint")}</p>
          </div>
          <div className="mt-5 hidden max-w-xs border-t border-border pt-5 lg:block" aria-hidden="true">
            <div className="flex items-baseline justify-between gap-3">
              <span className="text-sm font-semibold text-foreground">{activeIndex >= 0 ? t(`home.journey.${steps[activeIndex].id}.title`) : t("home.journey.idle")}</span>
              <bdi dir="ltr" className="omni-journey-accent font-mono text-xs tabular-nums">{activeIndex >= 0 ? String(activeIndex + 1).padStart(2, "0") : "—"} <span className="mx-1 text-border">/</span> {String(steps.length).padStart(2, "0")}</bdi>
            </div>
            <div className="mt-3 flex gap-1.5">
              {steps.map((step) => <span key={step.id} className={`h-1 flex-1 rounded-full transition-colors duration-300 motion-reduce:transition-none ${step.id === activeStep ? "bg-primary" : "bg-primary/15"}`} />)}
            </div>
          </div>
        </div>

        <Accordion type="single" collapsible value={activeStep} onValueChange={setActiveStep} dir={isRtl ? "rtl" : "ltr"} aria-label={t("home.journey.label")} className="relative min-w-0 space-y-3">
          {steps.map((step, index) => {
            const href = step.requiresAuth && !isAuthenticated() ? `/login?returnTo=${encodeURIComponent(step.href)}` : step.href;
            const Action = step.href.includes("#") ? "a" : Link;
            const visual = STEP_VISUALS[step.id];

            return (
              <AccordionItem key={step.id} value={step.id} className="omni-journey-item group/step relative overflow-hidden rounded-xl border border-border shadow-sm">
                <span aria-hidden="true" className="pointer-events-none absolute inset-y-0 start-0 w-[3px] bg-primary opacity-0 transition-opacity duration-300 group-data-[state=open]/step:opacity-100 motion-reduce:transition-none" />
                <AccordionTrigger className="gap-2.5 rounded-xl px-3.5 py-3.5 text-start hover:no-underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring sm:gap-4 sm:px-5 sm:py-4 [&>svg]:text-muted-foreground [&>svg]:duration-300 motion-reduce:[&>svg]:transition-none">
                  <span aria-hidden="true" className="omni-journey-icon omni-journey-accent flex h-10 w-10 sm:h-11 sm:w-11 shrink-0 items-center justify-center rounded-xl border border-primary/15 bg-primary/5 group-data-[state=open]/step:border-primary/25 group-data-[state=open]/step:bg-primary/10">
                    <step.icon className="h-5 w-5 sm:h-[22px] sm:w-[22px]" strokeWidth={1.65} />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-baseline gap-2 sm:gap-3">
                      <span className="text-sm font-semibold tracking-tight text-foreground sm:text-base lg:text-lg">{t(`home.journey.${step.id}.title`)}</span>
                      <span aria-hidden="true" dir="ltr" className="omni-journey-accent ms-auto rounded-md bg-primary/5 px-1.5 py-0.5 sm:px-2 sm:py-1 font-mono text-[10px] sm:text-[11px] font-medium tabular-nums group-data-[state=open]/step:bg-primary/10">{String(index + 1).padStart(2, "0")}</span>
                    </span>
                    <span className="mt-0.5 block text-xs font-normal leading-relaxed text-muted-foreground sm:text-sm">{t(`home.journey.${step.id}.caption`)}</span>
                  </span>
                </AccordionTrigger>
                <AccordionPrimitive.Content className="omni-journey-content overflow-hidden">
                  <div className="px-3.5 pb-4 sm:ps-[5.25rem] sm:pe-5 sm:pb-5">
                    <div className="border-t border-border/70 pt-3 sm:pt-4">
                      <p className="max-w-lg text-xs sm:text-sm leading-relaxed text-muted-foreground">{t(`home.journey.${step.id}.description`)}</p>

                      {/* Visual Step Preview Card */}
                      {visual && (
                        <div className="mt-3.5 rounded-xl border border-primary/20 bg-card/90 p-3 sm:p-3.5 shadow-xs">
                          <div className="mb-2.5 flex items-center justify-between">
                            <span className="flex items-center gap-1.5 text-[11px] font-semibold text-primary">
                              <Sparkles className="size-3.5" />
                              {visual.badge[language === "ar" ? "ar" : language === "darija" ? "darija" : "fr"]}
                            </span>
                            <span className="text-[10px] text-muted-foreground font-mono">OmniAgent Maroc</span>
                          </div>

                          <div className="grid gap-2 sm:grid-cols-3">
                            {visual.pills.map((pill, pIndex) => (
                              <div
                                key={pIndex}
                                className="flex items-center gap-2 rounded-lg border border-border/70 bg-muted/40 px-2.5 py-1.5 text-xs text-foreground"
                              >
                                <pill.icon className="size-3.5 shrink-0 text-secondary" />
                                <span className="truncate text-[11px] font-medium">
                                  {pill[language === "ar" ? "ar" : language === "darija" ? "darija" : "fr"]}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <Action href={href} className="mt-3 inline-flex min-h-11 max-w-full items-center gap-2 rounded-md text-xs sm:text-sm font-semibold omni-journey-accent underline decoration-primary/35 underline-offset-4 transition-colors hover:decoration-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
                        {t(`home.journey.${step.id}.action`)}<ArrowUpRight aria-hidden="true" className="h-4 w-4 shrink-0 text-primary rtl:-rotate-90" />
                      </Action>
                    </div>
                  </div>
                </AccordionPrimitive.Content>
              </AccordionItem>
            );
          })}
        </Accordion>
      </div>
    </section>
  );
}
