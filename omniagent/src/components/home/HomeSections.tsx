import { useEffect, useState, type ReactNode } from "react";
import { Link } from "wouter";
import { ArrowRight, ArrowUp, BookOpen, ChevronRight, CircleHelp, FileCheck2, Files, FolderCheck, FolderOpen, Info, Landmark, LockKeyhole, Newspaper, Search, ShieldCheck, UserRound } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { isAuthenticated } from "@/lib/auth";
import { useI18n, type Language } from "@/lib/i18n";
import { useListServices } from "@/lib/api-client";
import { HOME_LIFE_EVENTS, HOME_QUICK_ACTIONS } from "@/lib/home-config";
import { matchesLifeEvent, matchesServiceSearch, serviceCategoryLabel, serviceDetailsHref } from "@/lib/service-discovery";
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
      className={`home-section scroll-mt-24 py-12 sm:py-16 lg:py-20 ${muted ? "home-section-tinted border-y border-border/60" : ""}`}
    >
      <div className={container}>
        <div className="home-section-heading mb-7 sm:mb-9">
          <h2 id={`${id}-title`} className="max-w-3xl text-2xl font-bold tracking-tight text-foreground sm:text-3xl">{title}</h2>
          {description && <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground sm:text-base">{description}</p>}
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

export function HomeQuickActions() {
  const { t } = useI18n();
  return (
    <Section id="acces-rapide" title={t("home.quick.title")} description={t("home.quick.description")}>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {HOME_QUICK_ACTIONS.map((action) => {
          const href = "requiresAuth" in action && action.requiresAuth ? privateHref(action.href) : action.href;
          const Component = action.href.includes("#") ? "a" : Link;
          return <Component key={action.id} href={href} className={`${cardLink} flex flex-col p-5 sm:p-6`}>
            <span className="home-icon mb-5 grid size-12 place-items-center rounded-xl"><action.icon aria-hidden="true" className="h-6 w-6 text-secondary" strokeWidth={1.7} /></span>
            <h3 className="font-semibold leading-snug">{t(`home.quick.${action.id}.title`)}</h3>
            <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground">{t(`home.quick.${action.id}.description`)}</p>
            <ArrowRight aria-hidden="true" className="mt-5 h-4 w-4 self-end text-muted-foreground group-hover:text-secondary rtl:rotate-180" />
          </Component>;
        })}
      </div>
    </Section>
  );
}

export function LifeEventSection({ catalogue }: { catalogue: Catalogue }) {
  const { t } = useI18n();
  const available = (catalogue.data ?? []).filter((service) => service.isActive !== false);
  return (
    <Section id="situations" title={t("home.life.title")} description={t("home.life.description")} muted>
      <CatalogueStatus catalogue={catalogue}>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {HOME_LIFE_EVENTS.map((event) => {
            const supported = available.some((service) => matchesLifeEvent(service, event.id));
            const content = <><event.icon aria-hidden="true" className={`h-5 w-5 shrink-0 ${supported ? "text-secondary" : "text-muted-foreground"}`} /><div className="min-w-0 flex-1"><h3 className="text-sm font-semibold sm:text-base">{t(`home.life.${event.id}`)}</h3>{!supported && <p className="mt-1 text-xs text-muted-foreground">{t("home.life.soon")}</p>}</div>{supported && <ChevronRight aria-hidden="true" className="h-4 w-4 shrink-0 text-muted-foreground rtl:rotate-180" />}</>;
            return supported
              ? <Link key={event.id} href={`/services?lifeEvent=${event.id}`} className={`${cardLink} flex min-h-24 items-center gap-4 p-5`}>{content}</Link>
              : <div key={event.id} className="flex min-h-24 items-center gap-4 rounded-xl border border-border bg-background/60 p-5">{content}</div>;
          })}
        </div>
      </CatalogueStatus>
    </Section>
  );
}

export function PopularServices({ catalogue }: { catalogue: Catalogue }) {
  const { t, language } = useI18n();
  // The API has no popularity metric: preserve its order, without invented counts.
  const services = (catalogue.data ?? []).filter((service) => service.isActive !== false).slice(0, 6);
  return (
    <Section id="demarches" title={t("home.popular.title")} description={t("home.popular.description")}>
      <CatalogueStatus catalogue={catalogue}>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {services.map((service) => <Link key={service.id} href={serviceDetailsHref(service)} className={`${cardLink} flex flex-col p-5 sm:p-6`}>
            <div className="mb-4 flex items-center gap-2 text-xs font-medium text-secondary"><FileCheck2 aria-hidden="true" className="h-4 w-4" />{serviceCategoryLabel(service, language) ?? t("home.category.fallback")}</div>
            <h3 className="font-semibold leading-snug">{language === "fr" ? service.nameFr : service.nameAr || service.nameFr}</h3>
            <p className="mt-3 line-clamp-3 flex-1 text-sm leading-relaxed text-muted-foreground">{language === "fr" ? service.descriptionFr : service.descriptionAr || service.descriptionFr}</p>
            <span className="mt-5 flex items-center justify-between gap-3 border-t border-border pt-4 text-sm font-semibold text-primary">{t("home.popular.view")}<ArrowRight aria-hidden="true" className="h-4 w-4 rtl:rotate-180" /></span>
          </Link>)}
        </div>
      </CatalogueStatus>
      <div className="mt-6"><Button variant="outline" asChild><Link href="/services">{t("home.popular.all")}<ArrowRight aria-hidden="true" className="rtl:rotate-180" /></Link></Button></div>
    </Section>
  );
}

const preparationSteps = [
  { titleKey: "home.prepare.profile", icon: UserRound, href: "/profile" },
  { titleKey: "home.prepare.documents", icon: Files, href: "/profile" },
  { titleKey: "home.prepare.precheck", icon: FileCheck2, href: "/services" },
  { titleKey: "home.prepare.ready", icon: FolderCheck, href: "/dashboard" },
];
const preparationBenefits = [
  { id: "reuse", icon: UserRound },
  { id: "analyze", icon: FileCheck2 },
  { id: "organize", icon: FolderOpen },
];

export function PreparationFlow() {
  const { t } = useI18n();
  const reduceMotion = useReducedMotion();
  return (
    <motion.section
      id="preparer"
      aria-labelledby="preparer-title"
      initial={reduceMotion ? false : { opacity: 0, y: 18 }}
      whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.12 }}
      transition={{ duration: reduceMotion ? 0 : 0.45, ease: "easeOut" }}
      className="home-preparation border-y border-border/60 py-12 sm:py-16 lg:py-20"
    >
      <div className={`${container} grid gap-9 lg:grid-cols-[1fr_1.1fr] lg:items-center lg:gap-14`}>
        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-secondary">{t("home.prepare.eyebrow")}</p>
          <h2 id="preparer-title" className="text-2xl font-bold tracking-tight sm:text-3xl">{t("home.prepare.title")}</h2>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">{t("home.prepare.description")}</p>
          <Button asChild className="mt-6 h-auto min-h-11 whitespace-normal text-center"><Link href="/services">{t("home.prepare.action")}<ArrowRight aria-hidden="true" className="rtl:rotate-180" /></Link></Button>
        </div>
        <div className="home-preparation-card rounded-xl border border-border bg-card p-5 sm:p-7">
          <ol aria-label={t("home.prepare.flowLabel")} className="grid gap-2 sm:grid-cols-4">
            {preparationSteps.map((step, index) => <li key={step.titleKey} className="relative flex items-center gap-3 sm:block sm:text-center">
              <Link href={step.href === "/services" ? step.href : privateHref(step.href)} className="inline-flex min-h-11 items-center gap-3 rounded-lg px-2 py-3 text-sm font-medium transition-colors hover:bg-secondary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:flex-col sm:px-1">
                <step.icon aria-hidden="true" className="h-5 w-5 shrink-0 text-secondary" />{t(step.titleKey)}
              </Link>
              {index < preparationSteps.length - 1 && <ChevronRight aria-hidden="true" className="ms-auto h-4 w-4 rotate-90 text-muted-foreground sm:absolute sm:-end-3 sm:top-4 sm:rotate-0 rtl:sm:rotate-180" />}
            </li>)}
          </ol>
          <div className="mt-5 space-y-5 border-t border-border pt-6">
            {preparationBenefits.map((benefit) => <div key={benefit.id} className="flex items-start gap-3"><benefit.icon aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-secondary" /><div><h3 className="text-sm font-semibold">{t(`home.prepare.${benefit.id}.title`)}</h3><p className="mt-1 text-sm leading-relaxed text-muted-foreground">{t(`home.prepare.${benefit.id}.description`)}</p></div></div>)}
          </div>
        </div>
      </div>
    </motion.section>
  );
}

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
            <div className="relative"><Search aria-hidden="true" className="pointer-events-none absolute start-3 top-3.5 h-4 w-4 text-muted-foreground" /><Input id="home-service-search" type="search" name="q" value={query} onChange={(event) => setQuery(event.target.value)} placeholder={t("home.finder.placeholder")} className="h-11 bg-card ps-10" /></div>
            <Button type="submit" variant="secondary" className="min-h-11">{t("home.finder.action")}<ArrowRight aria-hidden="true" className="rtl:rotate-180" /></Button>
          </form>
          <p className="mt-4 flex items-start gap-2 text-xs leading-relaxed text-muted-foreground"><Info aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0" />{t("home.finder.scope")}</p>
        </div>
        <CatalogueStatus catalogue={catalogue}>
          <div>
            <p role="status" aria-live="polite" className="mb-3 text-xs font-medium text-muted-foreground">{query.trim() ? t("home.finder.results", { count: services.length }) : t("home.finder.suggestions")}</p>
            <div className="divide-y divide-border rounded-xl border border-border bg-card">
              {displayed.map((service) => <Link key={service.id} href={serviceDetailsHref(service)} className="flex min-h-16 items-center justify-between gap-4 rounded-lg p-4 transition-colors hover:bg-secondary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"><div className="min-w-0"><h3 className="text-sm font-semibold">{language === "fr" ? service.nameFr : service.nameAr || service.nameFr}</h3>{serviceCategoryLabel(service, language) && <p className="mt-1 text-xs text-muted-foreground">{serviceCategoryLabel(service, language)}</p>}</div><ChevronRight aria-hidden="true" className="h-4 w-4 shrink-0 text-secondary rtl:rotate-180" /></Link>)}
              {!displayed.length && <div className="p-5"><p className="text-sm font-semibold">{t("home.finder.noMatch")}</p><p className="mt-2 text-sm text-muted-foreground">{t("home.finder.otherTerm")}</p><Button className="mt-3" variant="outline" onClick={() => setQuery("")}>{t("home.finder.clear")}</Button></div>}
            </div>
            {services.length > displayed.length && query.trim() && <Link href={`/services?q=${encodeURIComponent(query)}`} className="mt-4 inline-flex min-h-11 items-center gap-2 text-sm font-semibold underline underline-offset-4">{t("home.finder.allResults")}<ArrowRight aria-hidden="true" className="h-4 w-4" /></Link>}
          </div>
        </CatalogueStatus>
      </div>
    </Section>
  );
}

const trustItems = [
  { id: "protection", icon: ShieldCheck },
  { id: "access", icon: LockKeyhole },
  { id: "transparency", icon: BookOpen },
];

export function TrustSection() {
  const { t } = useI18n();
  return (
    <Section id="vos-donnees" title={t("home.trust.title")}>
      <div className="grid gap-6 md:grid-cols-3">
        {trustItems.map((item) => <div key={item.id} className="flex items-start gap-3"><item.icon aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-secondary" /><div><h3 className="text-sm font-semibold">{t(`home.trust.${item.id}.title`)}</h3><p className="mt-2 text-sm leading-relaxed text-muted-foreground">{t(`home.trust.${item.id}.description`)}</p></div></div>)}
      </div>
      <a href="/help#confidentialite-securite" className="mt-6 inline-flex min-h-11 items-center gap-2 text-sm font-semibold underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">{t("home.trust.action")}<ArrowRight aria-hidden="true" className="h-4 w-4 shrink-0 rtl:rotate-180" /></a>
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
      {updates.length ? <div className="divide-y divide-border">{updates.map((update) => <a key={update.id} href={update.href} className="block rounded-lg py-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"><p className="text-xs font-medium text-secondary">{t(update.category === "Mise à jour d’une procédure" ? "home.updates.procedure" : update.category === "Nouveau service numérique" ? "home.updates.digital" : "home.updates.practical")}</p><h3 className="mt-2 font-semibold">{update.translations?.[language]?.title ?? update.title}</h3><p className="mt-2 text-sm text-muted-foreground">{update.translations?.[language]?.summary ?? update.summary}</p><span className="mt-3 inline-flex items-center gap-2 text-sm underline underline-offset-4">{t("home.updates.read")}<ArrowRight aria-hidden="true" className="h-4 w-4" /></span></a>)}</div>
        : <div className="flex items-start gap-4 rounded-xl border border-border bg-card p-5 sm:p-6"><Newspaper aria-hidden="true" className="mt-0.5 h-6 w-6 shrink-0 text-secondary" /><div><h3 className="text-sm font-semibold">{t("home.updates.empty")}</h3><p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">{t("home.updates.description")}</p><Link href="/services" className="mt-3 inline-flex min-h-11 items-center gap-2 text-sm font-semibold underline underline-offset-4">{t("home.updates.action")}<ArrowRight aria-hidden="true" className="h-4 w-4" /></Link></div></div>}
    </Section>
  );
}

export function HomeFooter() {
  const { t } = useI18n();
  return <footer className="border-t border-border bg-background py-7"><div className={`${container} flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between`}><div><Link href="/" className="inline-flex items-center gap-2 font-bold"><Landmark aria-hidden="true" className="h-5 w-5 text-primary" />{t("app.title")}</Link><p className="mt-2 text-xs text-muted-foreground">{t("home.footer.description")}</p></div><nav aria-label={t("home.footer.label")} className="flex flex-wrap gap-x-6 gap-y-2 text-sm"><Link href="/services" className="inline-flex min-h-11 items-center hover:underline">{t("nav.services")}</Link><Link href="/help" className="inline-flex min-h-11 items-center gap-1.5 hover:underline"><CircleHelp aria-hidden="true" className="h-4 w-4" />{t("nav.help")}</Link><a href="/help#confidentialite-securite" className="inline-flex min-h-11 items-center hover:underline">{t("home.footer.privacy")}</a></nav></div></footer>;
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
