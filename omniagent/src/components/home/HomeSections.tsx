import { useEffect, useState, type ReactNode } from "react";
import { Link } from "wouter";
import {
  ArrowRight,
  ArrowUp,
  BookOpen,
  ChevronRight,
  CircleHelp,
  FileCheck2,
  FileText,
  Files,
  FolderCheck,
  FolderOpen,
  Info,
  Landmark,
  LockKeyhole,
  Newspaper,
  Search,
  ShieldCheck,
  UserRound,
  Building2,
  CheckCircle2,
  Sparkles,
  Stamp,
  Clock,
  Scale,
} from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { isAuthenticated } from "@/lib/auth";
import { useI18n, type Language } from "@/lib/i18n";
import { useListServices } from "@/lib/api-client";
import { HOME_LIFE_EVENTS, HOME_QUICK_ACTIONS } from "@/lib/home-config";
import { matchesLifeEvent, matchesServiceSearch, serviceCategoryLabel, serviceDetailsHref } from "@/lib/service-discovery";
import { SERVICES_META } from "@/lib/services-data";
import { OmniAgentJourney } from "./OmniAgentJourney";

export { OmniAgentJourney } from "./OmniAgentJourney";

const container = "mx-auto w-full max-w-7xl px-4 sm:px-6";
const cardLink = "home-card group rounded-xl border border-border bg-card transition-colors hover:border-primary/50 hover:bg-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2";

function privateHref(path: string) {
  return isAuthenticated() ? path : `/login?returnTo=${encodeURIComponent(path)}`;
}

function Section({ id, title, description, muted = false, children }: { id: string; title: string; description?: string; muted?: boolean; children: ReactNode }) {
  const reduceMotion = useReducedMotion();
  return (
    <motion.section
      id={id}
      aria-labelledby={`${id}-title`}
      initial={reduceMotion ? false : { opacity: 0, y: 18 }}
      whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.12 }}
      transition={{ duration: reduceMotion ? 0 : 0.45, ease: "easeOut" }}
      className={`home-section scroll-mt-24 py-10 sm:py-16 lg:py-20 ${muted ? "home-section-tinted border-y border-border/60" : ""}`}
    >
      <div className={container}>
        <div className="home-section-heading mb-6 sm:mb-9">
          <h2 id={`${id}-title`} className="max-w-3xl text-xl font-bold tracking-tight text-foreground sm:text-2xl lg:text-3xl">{title}</h2>
          {description && <p className="mt-2.5 max-w-3xl text-sm leading-relaxed text-muted-foreground sm:mt-3 sm:text-base">{description}</p>}
        </div>
        {children}
      </div>
    </motion.section>
  );
}

type Catalogue = ReturnType<typeof useListServices>;

function CatalogueStatus({ catalogue, children }: { catalogue: Catalogue; children: ReactNode }) {
  const { t } = useI18n();
  if (catalogue.isLoading) return (
    <div role="status" aria-label={t("home.catalogue.loading")} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {[0, 1, 2].map((key) => <div key={key} className="space-y-4 rounded-xl border bg-card p-6"><Skeleton className="h-4 w-24" /><Skeleton className="h-6 w-3/4" /><Skeleton className="h-12 w-full" /></div>)}
      <span className="sr-only">{t("home.catalogue.loading")}</span>
    </div>
  );
  if (catalogue.isError) return (
    <div role="alert" className="flex flex-col items-start gap-4 rounded-xl border bg-card p-6 sm:flex-row sm:items-center sm:justify-between">
      <div><p className="font-semibold">{t("home.catalogue.unavailable")}</p><p className="mt-1 text-sm text-muted-foreground">{t("home.catalogue.retryHint")}</p></div>
      <Button variant="outline" onClick={() => void catalogue.refetch()} disabled={catalogue.isFetching}>{catalogue.isFetching ? t("home.catalogue.loading") : t("home.catalogue.retry")}</Button>
    </div>
  );
  if (!catalogue.data?.some((service) => service.isActive !== false)) return <p role="status" className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">{t("home.catalogue.empty")}</p>;
  return <>{children}</>;
}

const QUICK_ACTION_THEMES: Record<string, { tagFr: string; tagAr: string; tagDarija: string; colorClass: string; bgClass: string; iconBg: string }> = {
  inform: {
    tagFr: "Guides officiels",
    tagAr: "دلائل رسمية",
    tagDarija: "دلائل رسمية",
    colorClass: "text-sky-600 dark:text-sky-400",
    bgClass: "from-sky-500/10 via-transparent to-transparent",
    iconBg: "bg-sky-500/10 text-sky-600 dark:text-sky-400 border-sky-500/20",
  },
  prepare: {
    tagFr: "Scan & Contrôle",
    tagAr: "فحص الوثائق",
    tagDarija: "فحص الوثائق",
    colorClass: "text-amber-600 dark:text-amber-400",
    bgClass: "from-amber-500/10 via-transparent to-transparent",
    iconBg: "bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20",
  },
  track: {
    tagFr: "Suivi en direct",
    tagAr: "تتبع مباشر",
    tagDarija: "تتبع مباشر",
    colorClass: "text-emerald-600 dark:text-emerald-400",
    bgClass: "from-emerald-500/10 via-transparent to-transparent",
    iconBg: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20",
  },
  find: {
    tagFr: "Recherche IA",
    tagAr: "بحث ذكي",
    tagDarija: "بحث ذكي",
    colorClass: "text-purple-600 dark:text-purple-400",
    bgClass: "from-purple-500/10 via-transparent to-transparent",
    iconBg: "bg-purple-500/10 text-purple-600 dark:text-purple-400 border-purple-500/20",
  },
};

export function HomeQuickActions() {
  const { t, language } = useI18n();
  return (
    <Section id="acces-rapide" title={t("home.quick.title")} description={t("home.quick.description")}>
      <div className="grid gap-3.5 sm:gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {HOME_QUICK_ACTIONS.map((action) => {
          const href = "requiresAuth" in action && action.requiresAuth ? privateHref(action.href) : action.href;
          const Component = action.href.includes("#") ? "a" : Link;
          const theme = QUICK_ACTION_THEMES[action.id] || QUICK_ACTION_THEMES.inform;
          const tag = language === "fr" ? theme.tagFr : language === "ar" ? theme.tagAr : theme.tagDarija;

          return (
            <Component
              key={action.id}
              href={href}
              className={`${cardLink} relative flex flex-col overflow-hidden p-4 sm:p-6 transition-all hover:-translate-y-1`}
            >
              <div className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${theme.bgClass} opacity-60`} />

              <div className="relative mb-3.5 sm:mb-4 flex items-center justify-between">
                <span className={`grid size-11 sm:size-12 place-items-center rounded-xl border ${theme.iconBg} shadow-xs`}>
                  <action.icon aria-hidden="true" className="h-5 w-5 sm:h-6 sm:w-6" strokeWidth={1.8} />
                </span>
                <span className="rounded-full bg-card/90 px-2.5 py-0.5 text-[11px] font-semibold text-muted-foreground border border-border shadow-xs">
                  {tag}
                </span>
              </div>

              <h3 className="relative font-semibold text-sm sm:text-base leading-snug text-foreground">
                {t(`home.quick.${action.id}.title`)}
              </h3>
              <p className="relative mt-2 flex-1 text-xs sm:text-sm leading-relaxed text-muted-foreground">
                {t(`home.quick.${action.id}.description`)}
              </p>

              <div className="relative mt-4 sm:mt-5 flex items-center justify-between border-t border-border/70 pt-3 text-xs font-semibold text-primary">
                <span className="text-[11px] text-muted-foreground font-normal">
                  {language === "fr" ? "Accéder" : language === "ar" ? "دخول" : "دخول"}
                </span>
                <ArrowRight
                  aria-hidden="true"
                  className="h-4 w-4 text-primary transition-transform group-hover:translate-x-1 rtl:group-hover:-translate-x-1 rtl:rotate-180"
                />
              </div>
            </Component>
          );
        })}
      </div>
    </Section>
  );
}

const LIFE_EVENT_THEMES: Record<string, { tagFr: string; tagAr: string; tagDarija: string; color: string; bg: string; border: string }> = {
  moving: {
    tagFr: "Certificat de résidence, Eau/Élec",
    tagAr: "شهادة السكنى، فواتير الماء والكهرباء",
    tagDarija: "شهادة السكنى وفواتير الماء والضو",
    color: "text-teal-600 dark:text-teal-400",
    bg: "bg-teal-500/10",
    border: "border-teal-500/25",
  },
  marriage: {
    tagFr: "Acte de mariage, Livret de famille",
    tagAr: "عقد الزواج، الدفتر العائلي",
    tagDarija: "عقد الزواج والدفتر العائلي",
    color: "text-rose-600 dark:text-rose-400",
    bg: "bg-rose-500/10",
    border: "border-rose-500/25",
  },
  "lost-document": {
    tagFr: "Déclaration de perte, Duplicata CIN",
    tagAr: "شهادة الضياع، نظير بطاقة التعريف",
    tagDarija: "شهادة الضياع ونظير لاكارط",
    color: "text-amber-600 dark:text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/25",
  },
  business: {
    tagFr: "Registre de commerce, Patente",
    tagAr: "السجل التجاري، الضريبة المهنية",
    tagDarija: "السجل التجاري ولاپاطونت",
    color: "text-indigo-600 dark:text-indigo-400",
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/25",
  },
  travel: {
    tagFr: "Passeport biométrique, Visa",
    tagAr: "جواز السفر البيومتري، التأشيرة",
    tagDarija: "الباسبور والفيزا",
    color: "text-sky-600 dark:text-sky-400",
    bg: "bg-sky-500/10",
    border: "border-sky-500/25",
  },
  work: {
    tagFr: "Fiche anthropométrique, Concours",
    tagAr: "حسن السيرة، مباريات التوظيف",
    tagDarija: "حسن السيرة ومباريات الخدمة",
    color: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/25",
  },
};

export function LifeEventSection({ catalogue }: { catalogue: Catalogue }) {
  const { t, language } = useI18n();
  const available = (catalogue.data ?? []).filter((service) => service.isActive !== false);
  return (
    <Section id="situations" title={t("home.life.title")} description={t("home.life.description")} muted>
      <CatalogueStatus catalogue={catalogue}>
        <div className="grid gap-3 sm:gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {HOME_LIFE_EVENTS.map((event) => {
            const supported = available.some((service) => matchesLifeEvent(service, event.id));
            const theme = LIFE_EVENT_THEMES[event.id] || LIFE_EVENT_THEMES.moving;
            const subTag = language === "fr" ? theme.tagFr : language === "ar" ? theme.tagAr : theme.tagDarija;

            const content = (
              <>
                <div className={`grid size-11 sm:size-12 shrink-0 place-items-center rounded-xl border ${theme.bg} ${theme.border} ${theme.color} shadow-xs`}>
                  <event.icon aria-hidden="true" className="h-5 w-5 sm:h-6 sm:w-6" strokeWidth={1.8} />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold sm:text-base text-foreground leading-snug">{t(`home.life.${event.id}`)}</h3>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground truncate">{subTag}</p>
                  {!supported && <p className="mt-0.5 text-[11px] text-amber-600 dark:text-amber-400 font-medium">{t("home.life.soon")}</p>}
                </div>
                {supported ? (
                  <ChevronRight aria-hidden="true" className="h-4 w-4 shrink-0 text-muted-foreground group-hover:text-primary transition-colors rtl:rotate-180" />
                ) : (
                  <span className="text-[10px] rounded bg-muted px-1.5 py-0.5 text-muted-foreground">⏳</span>
                )}
              </>
            );

            return supported ? (
              <Link
                key={event.id}
                href={`/services?lifeEvent=${event.id}`}
                className={`${cardLink} flex min-h-20 sm:min-h-24 items-center gap-3.5 sm:gap-4 p-4 sm:p-5`}
              >
                {content}
              </Link>
            ) : (
              <div
                key={event.id}
                className="flex min-h-20 sm:min-h-24 items-center gap-3.5 sm:gap-4 rounded-xl border border-border bg-background/50 p-4 sm:p-5 opacity-80"
              >
                {content}
              </div>
            );
          })}
        </div>
      </CatalogueStatus>
    </Section>
  );
}

function getCategoryIcon(category?: string) {
  switch (category) {
    case "civil_status":
    case "civil":
      return FileText;
    case "justice":
      return Scale;
    case "family":
      return UserRound;
    case "property":
      return Building2;
    default:
      return Landmark;
  }
}

export function PopularServices({ catalogue }: { catalogue: Catalogue }) {
  const { t, language } = useI18n();
  // The API has no popularity metric: preserve its order, without invented counts.
  const services = (catalogue.data ?? []).filter((service) => service.isActive !== false).slice(0, 6);

  return (
    <Section id="demarches" title={t("home.popular.title")} description={t("home.popular.description")}>
      <CatalogueStatus catalogue={catalogue}>
        <div className="grid gap-4 sm:gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {services.map((service) => {
            const meta = SERVICES_META[service.id];
            const officeLabel = meta?.office ? (language === "ar" || language === "darija" ? meta.office.ar : meta.office.fr) : null;
            const CategoryIcon = getCategoryIcon(service.category);

            return (
              <Link
                key={service.id}
                href={serviceDetailsHref(service)}
                className="home-card group flex flex-col justify-between rounded-xl border border-border bg-card p-5 sm:p-6 transition-all duration-200 hover:border-primary/60 hover:shadow-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <div>
                  {/* Category & Fee Header */}
                  <div className="flex items-center justify-between gap-2">
                    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-secondary">
                      <CategoryIcon className="h-4 w-4 shrink-0 text-secondary" />
                      <span>{serviceCategoryLabel(service, language) ?? t("home.category.fallback")}</span>
                    </span>
                    {meta?.fee && (
                      <span className="rounded-md border border-border bg-muted/60 px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
                        {meta.fee}
                      </span>
                    )}
                  </div>

                  {/* Office / Administration */}
                  {officeLabel && (
                    <p className="mt-2.5 flex items-center gap-1.5 text-xs text-muted-foreground line-clamp-1">
                      <Landmark className="h-3.5 w-3.5 shrink-0 text-primary/70" />
                      <span className="truncate">{officeLabel}</span>
                    </p>
                  )}

                  {/* Title */}
                  <h3 className="mt-2 text-base sm:text-lg font-semibold tracking-tight text-foreground group-hover:text-primary transition-colors leading-snug">
                    {language === "fr" ? service.nameFr : service.nameAr || service.nameFr}
                  </h3>

                  {/* Description */}
                  <p className="mt-2 text-xs sm:text-sm leading-relaxed text-muted-foreground line-clamp-2">
                    {language === "fr" ? service.descriptionFr : service.descriptionAr || service.descriptionFr}
                  </p>
                </div>

                {/* Footer with Administrative Metadata & Action */}
                <div className="mt-5 border-t border-border pt-3.5 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-3 text-muted-foreground text-[11px]">
                    <span className="inline-flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {service.processingDays
                        ? `${service.processingDays} ${language === "fr" ? "jours" : "أيام"}`
                        : language === "fr"
                        ? "2 à 3 jours"
                        : "2 إلى 3 أيام"}
                    </span>
                    <span className="inline-flex items-center gap-1">
                      <FileCheck2 className="h-3 w-3" />
                      {service.requiredDocuments?.length ?? 3} {language === "fr" ? "pièces" : "وثائق"}
                    </span>
                  </div>

                  <span className="inline-flex items-center gap-1 font-semibold text-primary group-hover:underline">
                    <span>{t("home.popular.view")}</span>
                    <ArrowRight aria-hidden="true" className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5 rtl:group-hover:-translate-x-0.5 rtl:rotate-180" />
                  </span>
                </div>
              </Link>
            );
          })}
        </div>
      </CatalogueStatus>

      <div className="mt-7 flex justify-center sm:justify-start">
        <Button variant="outline" size="lg" asChild className="gap-2">
          <Link href="/services">
            {t("home.popular.all")}
            <ArrowRight aria-hidden="true" className="h-4 w-4 rtl:rotate-180" />
          </Link>
        </Button>
      </div>
    </Section>
  );
}

const preparationSteps = [
  { titleKey: "home.prepare.profile", icon: UserRound, href: "/profile", badgeFr: "CIN validée", badgeAr: "البطاقة مؤكدة", stepNum: "1" },
  { titleKey: "home.prepare.documents", icon: Files, href: "/profile", badgeFr: "Justificatifs", badgeAr: "الوثائق المطلوبة", stepNum: "2" },
  { titleKey: "home.prepare.precheck", icon: FileCheck2, href: "/services", badgeFr: "IA de contrôle", badgeAr: "فحص ذكي", stepNum: "3" },
  { titleKey: "home.prepare.ready", icon: FolderCheck, href: "/dashboard", badgeFr: "Prêt au dépôt", badgeAr: "جاهز للإيداع", stepNum: "4" },
];

const preparationBenefits = [
  { id: "reuse", icon: UserRound, colorClass: "text-sky-300", bgClass: "bg-sky-500/20 border-sky-500/35" },
  { id: "analyze", icon: FileCheck2, colorClass: "text-amber-300", bgClass: "bg-amber-500/20 border-amber-500/35" },
  { id: "organize", icon: FolderOpen, colorClass: "text-emerald-300", bgClass: "bg-emerald-500/20 border-emerald-500/35" },
];

export function PreparationFlow() {
  const { t, language } = useI18n();
  const reduceMotion = useReducedMotion();

  return (
    <motion.section
      id="preparer"
      aria-labelledby="preparer-title"
      initial={reduceMotion ? false : { opacity: 0, y: 18 }}
      whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.12 }}
      transition={{ duration: reduceMotion ? 0 : 0.45, ease: "easeOut" }}
      className="home-preparation border-y border-border/60 py-10 sm:py-16 lg:py-20"
    >
      <div className={`${container} grid gap-8 lg:grid-cols-[1fr_1.15fr] lg:items-center lg:gap-14`}>
        <div>
          <p className="mb-2.5 sm:mb-3 text-xs font-semibold uppercase tracking-widest text-sky-300">{t("home.prepare.eyebrow")}</p>
          <h2 id="preparer-title" className="text-xl sm:text-3xl font-bold tracking-tight text-white">{t("home.prepare.title")}</h2>
          <p className="mt-3 sm:mt-4 text-xs sm:text-base leading-relaxed text-slate-200">{t("home.prepare.description")}</p>

          {/* Value Checklist */}
          <div className="mt-5 sm:mt-6 space-y-2 text-xs sm:text-sm text-slate-100">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              <span>{language === "fr" ? "Zéro déplacement inutile avant d'avoir toutes les pièces" : language === "ar" ? "بدون تنقلات زائدة قبل استكمال الوثائق" : "بلا تنقلات خاوية قبل ما تكمل الوراق"}</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              <span>{language === "fr" ? "Vérification de lisibilité et conformité des scans" : language === "ar" ? "فحص وضوح ومطابقة النسخ الرقمية" : "فحص وضوح ومطابقة الوثائق"}</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400 shrink-0" />
              <span>{language === "fr" ? "Format standardisé reconnu par les administrations" : language === "ar" ? "تنسيق موحد معتمد لدى الإدارات" : "شكل موحد كيقبلوه فالمقاطعة"}</span>
            </div>
          </div>

          <Button asChild className="mt-6 sm:mt-8 h-auto min-h-11 w-full sm:w-auto whitespace-normal text-center shadow-md bg-primary hover:bg-primary/90 text-white font-semibold">
            <Link href="/services">
              {t("home.prepare.action")}
              <ArrowRight aria-hidden="true" className="rtl:rotate-180" />
            </Link>
          </Button>
        </div>

        {/* Moroccan Digital Citizen Dossier Card */}
        <div className="home-preparation-card rounded-2xl border border-border bg-card p-4 sm:p-7 shadow-xl">
          {/* Dossier Header */}
          <div className="flex items-center justify-between border-b border-white/10 pb-3.5 mb-4">
            <div className="flex items-center gap-2.5">
              <div className="grid size-9 place-items-center rounded-lg bg-sky-500/20 text-sky-300 border border-sky-500/35">
                <FolderCheck className="size-5" />
              </div>
              <div>
                <h4 className="text-xs sm:text-sm font-bold text-white">
                  {language === "fr" ? "Dossier Citoyen Numérique" : language === "ar" ? "الملف الرقمي للمواطن" : "الملف الرقمي للمواطن"}
                </h4>
                <p className="text-[11px] text-slate-300">
                  {language === "fr" ? "Préparation guidée pas-à-pas" : language === "ar" ? "إعداد موجه خطوة بخطوة" : "إعداد موجه خطوة بخطوة"}
                </p>
              </div>
            </div>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-2.5 py-0.5 text-[11px] font-semibold text-emerald-300 border border-emerald-500/35">
              <Sparkles className="size-3 text-emerald-300" />
              {language === "fr" ? "Pré-contrôle IA" : language === "ar" ? "فحص ذكي" : "فحص ذكي"}
            </span>
          </div>

          {/* Stepper Grid */}
          <ol aria-label={t("home.prepare.flowLabel")} className="grid gap-2.5 sm:grid-cols-4">
            {preparationSteps.map((step, index) => (
              <li key={step.titleKey} className="relative flex items-center gap-3 sm:block sm:text-center">
                <Link
                  href={step.href === "/services" ? step.href : privateHref(step.href)}
                  className="group flex w-full min-h-11 items-center gap-2.5 rounded-xl border border-white/10 bg-white/[0.05] p-2.5 text-xs font-medium transition-all hover:border-primary/60 hover:bg-white/[0.09] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:flex-col sm:p-3"
                >
                  <div className="relative grid size-8 place-items-center rounded-lg bg-white/10 text-white border border-white/15 group-hover:bg-primary/20 group-hover:text-primary transition-colors">
                    <step.icon aria-hidden="true" className="h-4 w-4" />
                    <span className="absolute -top-1 -end-1 flex size-4 items-center justify-center rounded-full bg-primary text-[9px] font-bold text-white shadow-xs">
                      {step.stepNum}
                    </span>
                  </div>
                  <span className="text-white font-semibold leading-tight">{t(step.titleKey)}</span>
                  <span className="hidden sm:inline-block text-[10px] text-slate-300 font-normal">
                    {language === "fr" ? step.badgeFr : step.badgeAr}
                  </span>
                </Link>
                {index < preparationSteps.length - 1 && (
                  <ChevronRight
                    aria-hidden="true"
                    className="ms-auto h-4 w-4 rotate-90 text-slate-400 sm:absolute sm:-end-3 sm:top-5 sm:rotate-0 rtl:sm:rotate-180"
                  />
                )}
              </li>
            ))}
          </ol>

          {/* 3 Benefits with Styled Icons */}
          <div className="mt-5 space-y-3.5 sm:space-y-4 border-t border-white/10 pt-5">
            {preparationBenefits.map((benefit) => (
              <div key={benefit.id} className="flex items-start gap-3">
                <div className={`grid size-8 shrink-0 place-items-center rounded-lg border ${benefit.bgClass} ${benefit.colorClass}`}>
                  <benefit.icon aria-hidden="true" className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-xs sm:text-sm font-semibold text-white">{t(`home.prepare.${benefit.id}.title`)}</h3>
                  <p className="mt-0.5 text-xs sm:text-sm leading-relaxed text-slate-300">{t(`home.prepare.${benefit.id}.description`)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </motion.section>
  );
}

const POPULAR_FINDER_KEYWORDS = [
  { labelFr: "Carte Nationale (CIN)", labelAr: "البطاقة الوطنية" },
  { labelFr: "Certificat de résidence", labelAr: "شهادة السكنى" },
  { labelFr: "Acte de naissance", labelAr: "عقد الازدياد" },
  { labelFr: "Acte de mariage", labelAr: "عقد الزواج" },
  { labelFr: "Casier judiciaire", labelAr: "السجل العدلي" },
  { labelFr: "Fiche anthropométrique", labelAr: "حسن السيرة" },
];

export function ServiceFinder({ catalogue }: { catalogue: Catalogue }) {
  const { t, language } = useI18n();
  const [query, setQuery] = useState("");
  const services = (catalogue.data ?? []).filter((service) => service.isActive !== false && matchesServiceSearch(service, query));
  const displayed = services.slice(0, query.trim() ? 6 : 3);

  return (
    <Section id="trouver-un-service" title={t("home.finder.title")} description={t("home.finder.description")} muted>
      <div className="grid gap-6 lg:grid-cols-[1fr_1.1fr] lg:gap-12">
        <div>
          <form action="/services" method="get" className="space-y-3">
            <label htmlFor="home-service-search" className="block text-sm font-semibold">{t("home.finder.label")}</label>
            <div className="relative">
              <Search aria-hidden="true" className="pointer-events-none absolute start-3 top-3.5 h-4 w-4 text-muted-foreground" />
              <Input
                id="home-service-search"
                type="search"
                name="q"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder={t("home.finder.placeholder")}
                className="h-11 bg-card ps-10"
              />
            </div>
            <Button type="submit" variant="secondary" className="w-full sm:w-auto min-h-11">
              {t("home.finder.action")}
              <ArrowRight aria-hidden="true" className="rtl:rotate-180" />
            </Button>
          </form>

          {/* Quick Search Keyword Chips */}
          <div className="mt-4">
            <p className="text-xs font-semibold text-muted-foreground mb-2">
              {language === "fr" ? "Recherches fréquentes :" : language === "ar" ? "عمليات البحث الشائعة:" : "البحث الشائع:"}
            </p>
            <div className="flex flex-wrap gap-1.5 sm:gap-2">
              {POPULAR_FINDER_KEYWORDS.map((item) => {
                const text = language === "ar" || language === "darija" ? item.labelAr : item.labelFr;
                return (
                  <button
                    key={item.labelFr}
                    type="button"
                    onClick={() => setQuery(text)}
                    className="inline-flex items-center gap-1.5 rounded-full border border-border bg-card px-2.5 py-1 text-xs font-medium text-foreground transition-colors hover:border-primary/50 hover:bg-primary/5"
                  >
                    <Search className="size-3 text-muted-foreground" />
                    <span>{text}</span>
                  </button>
                );
              })}
            </div>
          </div>

          <p className="mt-3 sm:mt-4 flex items-start gap-2 text-xs leading-relaxed text-muted-foreground">
            <Info aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0" />
            {t("home.finder.scope")}
          </p>
        </div>

        <CatalogueStatus catalogue={catalogue}>
          <div>
            <p role="status" aria-live="polite" className="mb-2.5 sm:mb-3 text-xs font-medium text-muted-foreground">
              {query.trim() ? t("home.finder.results", { count: services.length }) : t("home.finder.suggestions")}
            </p>
            <div className="divide-y divide-border rounded-xl border border-border bg-card">
              {displayed.map((service) => {
                const meta = SERVICES_META[service.id];
                return (
                  <Link
                    key={service.id}
                    href={serviceDetailsHref(service)}
                    className="flex min-h-14 sm:min-h-16 items-center justify-between gap-3 sm:gap-4 rounded-lg p-3.5 sm:p-4 transition-colors hover:bg-secondary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="grid size-9 shrink-0 place-items-center rounded-lg bg-secondary/10 text-secondary border border-secondary/20">
                        <FileText className="size-4" />
                      </div>
                      <div className="min-w-0">
                        <h3 className="text-xs sm:text-sm font-semibold truncate">
                          {language === "fr" ? service.nameFr : service.nameAr || service.nameFr}
                        </h3>
                        {serviceCategoryLabel(service, language) && (
                          <p className="mt-0.5 text-[11px] sm:text-xs text-muted-foreground">
                            {serviceCategoryLabel(service, language)}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      {meta?.fee && (
                        <span className="rounded-full bg-secondary/10 px-2 py-0.5 text-[10px] font-semibold text-secondary">
                          {meta.fee}
                        </span>
                      )}
                      <ChevronRight aria-hidden="true" className="h-4 w-4 text-secondary rtl:rotate-180" />
                    </div>
                  </Link>
                );
              })}
              {!displayed.length && (
                <div className="p-4 sm:p-5">
                  <p className="text-sm font-semibold">{t("home.finder.noMatch")}</p>
                  <p className="mt-2 text-sm text-muted-foreground">{t("home.finder.otherTerm")}</p>
                  <Button className="mt-3" variant="outline" onClick={() => setQuery("")}>
                    {t("home.finder.clear")}
                  </Button>
                </div>
              )}
            </div>
            {services.length > displayed.length && query.trim() && (
              <Link
                href={`/services?q=${encodeURIComponent(query)}`}
                className="mt-3.5 sm:mt-4 inline-flex min-h-11 items-center gap-2 text-xs sm:text-sm font-semibold underline underline-offset-4"
              >
                {t("home.finder.allResults")}
                <ArrowRight aria-hidden="true" className="h-4 w-4" />
              </Link>
            )}
          </div>
        </CatalogueStatus>
      </div>
    </Section>
  );
}

const trustItems = [
  { id: "protection", icon: ShieldCheck, color: "text-emerald-400", bg: "bg-emerald-500/10 border-emerald-500/20" },
  { id: "access", icon: LockKeyhole, color: "text-sky-400", bg: "bg-sky-500/10 border-sky-500/20" },
  { id: "transparency", icon: BookOpen, color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
];

export function TrustSection() {
  const { t, language } = useI18n();
  return (
    <Section id="vos-donnees" title={t("home.trust.title")}>
      {/* Sovereign Moroccan CNDP Seal Banner */}
      <div className="mb-6 sm:mb-8 rounded-xl border border-primary/30 bg-primary/10 p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3.5">
          <div className="grid size-11 shrink-0 place-items-center rounded-xl bg-primary/20 text-primary border border-primary/30">
            <Stamp className="size-6" />
          </div>
          <div>
            <h3 className="font-bold text-sm sm:text-base text-white">
              {language === "fr"
                ? "Conformité CNDP • Loi n° 09-08"
                : language === "ar"
                ? "مطابقة CNDP • القانون رقم 09-08"
                : "مطابقة CNDP • القانون 09-08"}
            </h3>
            <p className="text-xs sm:text-sm text-slate-200 mt-0.5">
              {language === "fr"
                ? "Protection des données à caractère personnel et souveraineté numérique marocaine."
                : language === "ar"
                ? "حماية المعطيات ذات الطابع الشخصي والسيادة الرقمية الوطنية بالمغرب."
                : "حماية المعطيات الشخصية والسيادة الرقمية بالمغرب."}
            </p>
          </div>
        </div>
        <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-semibold text-white border border-white/20 shrink-0">
          ✓ 100% Souverain
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:gap-6 md:grid-cols-3">
        {trustItems.map((item) => (
          <div key={item.id} className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/[0.04] p-4 sm:p-5">
            <div className={`grid size-9 shrink-0 place-items-center rounded-lg border ${item.bg} ${item.color}`}>
              <item.icon aria-hidden="true" className="h-4 w-4" />
            </div>
            <div>
              <h3 className="text-sm font-semibold text-white">{t(`home.trust.${item.id}.title`)}</h3>
              <p className="mt-1.5 sm:mt-2 text-xs sm:text-sm leading-relaxed text-slate-300">
                {t(`home.trust.${item.id}.description`)}
              </p>
            </div>
          </div>
        ))}
      </div>
      <a
        href="/help#confidentialite-securite"
        className="mt-6 sm:mt-8 inline-flex min-h-11 items-center gap-2 text-sm font-semibold underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        {t("home.trust.action")}
        <ArrowRight aria-hidden="true" className="h-4 w-4 shrink-0 rtl:rotate-180" />
      </a>
    </Section>
  );
}

export interface PublicUpdate {
  id: string;
  title: string;
  summary: string;
  category: "Mise à jour d’une procédure" | "Nouveau service numérique" | "Information pratique";
  href: string;
  translations?: Partial<Record<Language, { title: string; summary: string }>>;
}

export function PublicUpdates({ updates = [] }: { updates?: PublicUpdate[] }) {
  const { t, language } = useI18n();
  return (
    <Section id="actualites" title={t("home.updates.title")} muted>
      {/* Official Portals Strip */}
      <div className="mb-5 sm:mb-6 flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span className="font-semibold text-foreground">
          {language === "fr" ? "Sources administratives interconnectées :" : language === "ar" ? "المصادر الإدارية المعتمدة:" : "المصادر المعتمدة:"}
        </span>
        {["Watiqa.ma", "Idarati.ma", "cnie.ma", "Portail Justice"].map((portal) => (
          <span key={portal} className="inline-flex items-center gap-1 rounded-full bg-card px-2.5 py-1 font-medium border border-border">
            <Landmark className="size-3 text-primary" />
            {portal}
          </span>
        ))}
      </div>

      {updates.length ? (
        <div className="divide-y divide-border rounded-xl border border-border bg-card p-4 sm:p-6">
          {updates.map((update) => (
            <a key={update.id} href={update.href} className="block rounded-lg py-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">
              <p className="text-xs font-medium text-secondary">
                {t(update.category === "Mise à jour d’une procédure" ? "home.updates.procedure" : update.category === "Nouveau service numérique" ? "home.updates.digital" : "home.updates.practical")}
              </p>
              <h3 className="mt-2 font-semibold text-sm sm:text-base">{update.translations?.[language]?.title ?? update.title}</h3>
              <p className="mt-1.5 sm:mt-2 text-xs sm:text-sm text-muted-foreground">{update.translations?.[language]?.summary ?? update.summary}</p>
              <span className="mt-2.5 sm:mt-3 inline-flex items-center gap-2 text-xs sm:text-sm underline underline-offset-4">
                {t("home.updates.read")}
                <ArrowRight aria-hidden="true" className="h-4 w-4" />
              </span>
            </a>
          ))}
        </div>
      ) : (
        <div className="flex items-start gap-3.5 sm:gap-4 rounded-xl border border-border bg-card p-4 sm:p-6">
          <div className="grid size-12 shrink-0 place-items-center rounded-xl bg-secondary/10 text-secondary border border-secondary/20">
            <Newspaper aria-hidden="true" className="h-6 w-6" />
          </div>
          <div>
            <h3 className="text-sm font-semibold">{t("home.updates.empty")}</h3>
            <p className="mt-1.5 sm:mt-2 max-w-2xl text-xs sm:text-sm leading-relaxed text-muted-foreground">{t("home.updates.description")}</p>
            <Link href="/services" className="mt-2.5 sm:mt-3 inline-flex min-h-11 items-center gap-2 text-xs sm:text-sm font-semibold underline underline-offset-4">
              {t("home.updates.action")}
              <ArrowRight aria-hidden="true" className="h-4 w-4" />
            </Link>
          </div>
        </div>
      )}
    </Section>
  );
}

export function HomeFooter() {
  const { t } = useI18n();
  return <footer className="border-t border-border bg-background py-6 sm:py-7"><div className={`${container} flex flex-col gap-4 sm:gap-5 sm:flex-row sm:items-center sm:justify-between`}><div><Link href="/" className="inline-flex items-center gap-2 font-bold"><Landmark aria-hidden="true" className="h-5 w-5 text-primary" />{t("app.title")}</Link><p className="mt-1.5 sm:mt-2 text-xs text-muted-foreground">{t("home.footer.description")}</p></div><nav aria-label={t("home.footer.label")} className="flex flex-wrap gap-x-4 sm:gap-x-6 gap-y-2 text-xs sm:text-sm"><Link href="/services" className="inline-flex min-h-11 items-center hover:underline">{t("nav.services")}</Link><Link href="/help" className="inline-flex min-h-11 items-center gap-1.5 hover:underline"><CircleHelp aria-hidden="true" className="h-4 w-4" />{t("nav.help")}</Link><a href="/help#confidentialite-securite" className="inline-flex min-h-11 items-center hover:underline">{t("home.footer.privacy")}</a></nav></div></footer>;
}

function ScrollToTopButton() {
  const { t } = useI18n();
  const [visible, setVisible] = useState(false);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    const updateVisibility = () => setVisible(window.scrollY > 400);
    updateVisibility();
    window.addEventListener("scroll", updateVisibility, { passive: true });
    return () => window.removeEventListener("scroll", updateVisibility);
  }, []);

  return (
    <AnimatePresence>
      {visible && (
        <motion.button
          key="scroll-to-top"
          type="button"
          aria-label={t("home.scrollTop")}
          title={t("home.scrollTop")}
          initial={reduceMotion ? false : { opacity: 0, y: 8, scale: 0.92 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={reduceMotion ? undefined : { opacity: 0, y: 8, scale: 0.92 }}
          transition={{ duration: reduceMotion ? 0 : 0.18 }}
          onClick={() => window.scrollTo({ top: 0, behavior: reduceMotion ? "auto" : "smooth" })}
          className="fixed bottom-5 end-5 z-40 grid size-12 place-items-center rounded-full border border-primary/20 bg-primary text-primary-foreground shadow-lg transition-colors hover:bg-primary/90 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
        >
          <ArrowUp aria-hidden="true" className="h-5 w-5" />
        </motion.button>
      )}
    </AnimatePresence>
  );
}

export function HomeSections() {
  const { language, isRtl } = useI18n();
  // Share the catalogue query and React Query cache with the existing Services page.
  const catalogue = useListServices();
  return <div lang={language === "darija" ? "ar-MA" : language} dir={isRtl ? "rtl" : "ltr"} className="text-start"><HomeQuickActions /><LifeEventSection catalogue={catalogue} /><PopularServices catalogue={catalogue} /><PreparationFlow /><OmniAgentJourney /><ServiceFinder catalogue={catalogue} /><TrustSection /><PublicUpdates /><HomeFooter /><ScrollToTopButton /></div>;
}
