import { useEffect, useState, type ReactNode } from "react";
import { Link } from "wouter";
import { ArrowRight, ArrowUp, BookOpen, ChevronRight, CircleHelp, FileCheck2, Files, FolderCheck, FolderOpen, Info, Landmark, LockKeyhole, Newspaper, Search, ShieldCheck, UserRound } from "lucide-react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { isAuthenticated } from "@/lib/auth";
import { useListServices } from "@/lib/api-client";
import { HOME_LIFE_EVENTS, HOME_QUICK_ACTIONS } from "@/lib/home-config";
import { matchesLifeEvent, matchesServiceSearch, serviceCategoryLabel, serviceDetailsHref } from "@/lib/service-discovery";

const container = "mx-auto w-full max-w-7xl px-4 sm:px-6";
const cardLink = "group rounded-xl border border-border bg-card transition-colors hover:border-secondary/50 hover:bg-secondary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2";

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
      className={`scroll-mt-24 py-12 sm:py-16 lg:py-20 ${muted ? "border-y border-border/60 bg-muted/40" : "bg-background"}`}
    >
      <div className={container}>
        <div className="mb-7 sm:mb-9">
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
  if (catalogue.isLoading) return (
    <div role="status" aria-label="Chargement des démarches" className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {[0, 1, 2].map((key) => <div key={key} className="space-y-4 rounded-xl border bg-card p-6"><Skeleton className="h-4 w-24" /><Skeleton className="h-6 w-3/4" /><Skeleton className="h-12 w-full" /></div>)}
      <span className="sr-only">Chargement des démarches…</span>
    </div>
  );
  if (catalogue.isError) return (
    <div role="alert" className="flex flex-col items-start gap-4 rounded-xl border bg-card p-6 sm:flex-row sm:items-center sm:justify-between">
      <div><p className="font-semibold">Le catalogue est momentanément indisponible.</p><p className="mt-1 text-sm text-muted-foreground">Veuillez réessayer pour consulter les démarches disponibles.</p></div>
      <Button variant="outline" onClick={() => void catalogue.refetch()} disabled={catalogue.isFetching}>{catalogue.isFetching ? "Chargement…" : "Réessayer"}</Button>
    </div>
  );
  if (!catalogue.data?.some((service) => service.isActive !== false)) return <p role="status" className="rounded-xl border bg-card p-6 text-sm text-muted-foreground">Aucune démarche n’est disponible dans le catalogue pour le moment.</p>;
  return <>{children}</>;
}

export function HomeQuickActions() {
  return (
    <Section id="acces-rapide" title="Que souhaitez-vous faire ?" description="Accédez rapidement au service adapté à votre besoin.">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {HOME_QUICK_ACTIONS.map((action) => {
          const href = "requiresAuth" in action && action.requiresAuth ? privateHref(action.href) : action.href;
          const Component = action.href.includes("#") ? "a" : Link;
          return <Component key={action.title} href={href} className={`${cardLink} flex flex-col p-5 sm:p-6`}>
            <action.icon aria-hidden="true" className="mb-5 h-6 w-6 text-secondary" strokeWidth={1.7} />
            <h3 className="font-semibold leading-snug">{action.title}</h3>
            <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground">{action.description}</p>
            <ArrowRight aria-hidden="true" className="mt-5 h-4 w-4 self-end text-muted-foreground group-hover:text-secondary rtl:rotate-180" />
          </Component>;
        })}
      </div>
    </Section>
  );
}

export function LifeEventSection({ catalogue }: { catalogue: Catalogue }) {
  const available = (catalogue.data ?? []).filter((service) => service.isActive !== false);
  return (
    <Section id="situations" title="Vos démarches selon votre situation" description="Commencez par votre besoin, OmniAgent vous aide à identifier les démarches utiles." muted>
      <CatalogueStatus catalogue={catalogue}>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {HOME_LIFE_EVENTS.map((event) => {
            const supported = available.some((service) => matchesLifeEvent(service, event.id));
            const content = <><event.icon aria-hidden="true" className={`h-5 w-5 shrink-0 ${supported ? "text-secondary" : "text-muted-foreground"}`} /><div className="min-w-0 flex-1"><h3 className="text-sm font-semibold sm:text-base">{event.title}</h3>{!supported && <p className="mt-1 text-xs text-muted-foreground">Bientôt disponible</p>}</div>{supported && <ChevronRight aria-hidden="true" className="h-4 w-4 shrink-0 text-muted-foreground rtl:rotate-180" />}</>;
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
  // The API has no popularity metric: preserve its order, without invented counts.
  const services = (catalogue.data ?? []).filter((service) => service.isActive !== false).slice(0, 6);
  return (
    <Section id="demarches" title="Démarches les plus consultées" description="Découvrez une sélection de démarches disponibles dans le catalogue OmniAgent.">
      <CatalogueStatus catalogue={catalogue}>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {services.map((service) => <Link key={service.id} href={serviceDetailsHref(service)} className={`${cardLink} flex flex-col p-5 sm:p-6`}>
            <div className="mb-4 flex items-center gap-2 text-xs font-medium text-secondary"><FileCheck2 aria-hidden="true" className="h-4 w-4" />{serviceCategoryLabel(service) ?? "Démarche administrative"}</div>
            <h3 className="font-semibold leading-snug">{service.nameFr}</h3>
            <p className="mt-3 line-clamp-3 flex-1 text-sm leading-relaxed text-muted-foreground">{service.descriptionFr}</p>
            <span className="mt-5 flex items-center justify-between gap-3 border-t border-border pt-4 text-sm font-semibold">Voir la démarche<ArrowRight aria-hidden="true" className="h-4 w-4 text-secondary rtl:rotate-180" /></span>
          </Link>)}
        </div>
      </CatalogueStatus>
      <div className="mt-6"><Button variant="outline" asChild><Link href="/services">Toutes les démarches<ArrowRight aria-hidden="true" className="rtl:rotate-180" /></Link></Button></div>
    </Section>
  );
}

const preparationSteps = [
  { title: "Votre profil", icon: UserRound, href: "/profile" },
  { title: "Vos documents", icon: Files, href: "/profile" },
  { title: "Précontrôle", icon: FileCheck2, href: "/services" },
  { title: "Dossier préparé", icon: FolderCheck, href: "/dashboard" },
];
const preparationBenefits = [
  { title: "Réutilisez vos informations", description: "Évitez de saisir plusieurs fois les mêmes données.", icon: UserRound },
  { title: "Analysez vos documents", description: "Repérez les informations illisibles, manquantes ou à vérifier.", icon: FileCheck2 },
  { title: "Préparez votre dossier", description: "Regroupez les éléments utiles avant de poursuivre la démarche.", icon: FolderOpen },
];

export function PreparationFlow() {
  const reduceMotion = useReducedMotion();
  return (
    <motion.section
      id="preparer"
      aria-labelledby="preparer-title"
      initial={reduceMotion ? false : { opacity: 0, y: 18 }}
      whileInView={reduceMotion ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.12 }}
      transition={{ duration: reduceMotion ? 0 : 0.45, ease: "easeOut" }}
      className="border-y border-border/60 bg-secondary/5 py-12 sm:py-16 lg:py-20"
    >
      <div className={`${container} grid gap-9 lg:grid-cols-[1fr_1.1fr] lg:items-center lg:gap-14`}>
        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-widest text-secondary">Votre espace citoyen</p>
          <h2 id="preparer-title" className="text-2xl font-bold tracking-tight sm:text-3xl">Préparez votre démarche avant de la déposer</h2>
          <p className="mt-4 text-sm leading-relaxed text-muted-foreground sm:text-base">OmniAgent vous aide à réutiliser vos informations, organiser vos documents et identifier les éléments à vérifier avant de poursuivre votre démarche.</p>
          <Button asChild className="mt-6 h-auto min-h-11 whitespace-normal text-center"><Link href="/services">Préparer une démarche<ArrowRight aria-hidden="true" className="rtl:rotate-180" /></Link></Button>
        </div>
        <div className="rounded-xl border border-border bg-card p-5 sm:p-7">
          <ol aria-label="Les étapes de préparation" className="grid gap-2 sm:grid-cols-4">
            {preparationSteps.map((step, index) => <li key={step.title} className="relative flex items-center gap-3 sm:block sm:text-center">
              <Link href={step.href === "/services" ? step.href : privateHref(step.href)} className="inline-flex min-h-11 items-center gap-3 rounded-lg px-2 py-3 text-sm font-medium transition-colors hover:bg-secondary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring sm:flex-col sm:px-1">
                <step.icon aria-hidden="true" className="h-5 w-5 shrink-0 text-secondary" />{step.title}
              </Link>
              {index < preparationSteps.length - 1 && <ChevronRight aria-hidden="true" className="ms-auto h-4 w-4 rotate-90 text-muted-foreground sm:absolute sm:-end-3 sm:top-4 sm:rotate-0 rtl:sm:rotate-180" />}
            </li>)}
          </ol>
          <div className="mt-5 space-y-5 border-t border-border pt-6">
            {preparationBenefits.map((benefit) => <div key={benefit.title} className="flex items-start gap-3"><benefit.icon aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0 text-secondary" /><div><h3 className="text-sm font-semibold">{benefit.title}</h3><p className="mt-1 text-sm leading-relaxed text-muted-foreground">{benefit.description}</p></div></div>)}
          </div>
        </div>
      </div>
    </motion.section>
  );
}

const journey = ["Comprendre", "Préparer", "Réutiliser", "Vérifier", "Agir", "Suivre"];

export function OmniAgentJourney() {
  return (
    <Section id="accompagnement" title="Un accompagnement à chaque étape" description="De la recherche d’information jusqu’au suivi de votre démarche, OmniAgent vous accompagne progressivement tout en laissant les décisions officielles à l’administration compétente.">
      <ol className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6" aria-label="Votre parcours avec OmniAgent">
        {journey.map((step, index) => <li key={step} className="flex items-center gap-3 border-b border-border py-3"><span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-secondary/10 text-xs font-semibold text-secondary">{index + 1}</span><span className="text-sm font-semibold">{step}</span>{index < journey.length - 1 && <ArrowRight aria-hidden="true" className="ms-auto h-3.5 w-3.5 shrink-0 rotate-90 text-muted-foreground sm:rotate-0 rtl:sm:rotate-180" />}</li>)}
      </ol>
    </Section>
  );
}

export function ServiceFinder({ catalogue }: { catalogue: Catalogue }) {
  const [query, setQuery] = useState("");
  const services = (catalogue.data ?? []).filter((service) => service.isActive !== false && matchesServiceSearch(service, query));
  const displayed = services.slice(0, query.trim() ? 6 : 3);
  return (
    <Section id="trouver-un-service" title="Trouvez le service compétent" description="Recherchez l’administration, le portail ou le service correspondant à votre démarche." muted>
      <div className="grid gap-6 lg:grid-cols-[1fr_1.1fr] lg:gap-12">
        <div>
          <form action="/services" method="get" className="space-y-3">
            <label htmlFor="home-service-search" className="block text-sm font-semibold">Quelle démarche recherchez-vous ?</label>
            <div className="relative"><Search aria-hidden="true" className="pointer-events-none absolute start-3 top-3.5 h-4 w-4 text-muted-foreground" /><Input id="home-service-search" type="search" name="q" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Rechercher par service, administration ou démarche..." className="h-11 bg-card ps-10" /></div>
            <Button type="submit" variant="secondary" className="min-h-11">Rechercher dans le catalogue<ArrowRight aria-hidden="true" className="rtl:rotate-180" /></Button>
          </form>
          <p className="mt-4 flex items-start gap-2 text-xs leading-relaxed text-muted-foreground"><Info aria-hidden="true" className="mt-0.5 h-4 w-4 shrink-0" />La recherche porte actuellement sur les démarches du catalogue. Les coordonnées des administrations et les points d’accueil ne sont pas encore référencés.</p>
        </div>
        <CatalogueStatus catalogue={catalogue}>
          <div>
            <p role="status" aria-live="polite" className="mb-3 text-xs font-medium text-muted-foreground">{query.trim() ? `${services.length} démarche${services.length > 1 ? "s" : ""} trouvée${services.length > 1 ? "s" : ""}` : "Quelques démarches pour commencer"}</p>
            <div className="divide-y divide-border rounded-xl border border-border bg-card">
              {displayed.map((service) => <Link key={service.id} href={serviceDetailsHref(service)} className="flex min-h-16 items-center justify-between gap-4 rounded-lg p-4 transition-colors hover:bg-secondary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"><div className="min-w-0"><h3 className="text-sm font-semibold">{service.nameFr}</h3>{serviceCategoryLabel(service) && <p className="mt-1 text-xs text-muted-foreground">{serviceCategoryLabel(service)}</p>}</div><ChevronRight aria-hidden="true" className="h-4 w-4 shrink-0 text-secondary rtl:rotate-180" /></Link>)}
              {!displayed.length && <div className="p-5"><p className="text-sm font-semibold">Aucune démarche ne correspond à votre recherche.</p><p className="mt-2 text-sm text-muted-foreground">Essayez un autre terme ou consultez l’ensemble du catalogue.</p><Button className="mt-3" variant="outline" onClick={() => setQuery("")}>Effacer la recherche</Button></div>}
            </div>
            {services.length > displayed.length && query.trim() && <Link href={`/services?q=${encodeURIComponent(query)}`} className="mt-4 inline-flex min-h-11 items-center gap-2 text-sm font-semibold underline underline-offset-4">Voir tous les résultats<ArrowRight aria-hidden="true" className="h-4 w-4" /></Link>}
          </div>
        </CatalogueStatus>
      </div>
    </Section>
  );
}

const trustItems = [
  { title: "Protection des données", description: "Vos informations sont utilisées pour les fonctions nécessaires au service : profil, préparation des dossiers et analyse des documents.", icon: ShieldCheck },
  { title: "Accès sécurisé", description: "L’accès à vos données et documents personnels nécessite une connexion et des contrôles d’accès.", icon: LockKeyhole },
  { title: "Transparence", description: "Vous pouvez comprendre quelles informations sont utilisées et dans quel objectif.", icon: BookOpen },
];

export function TrustSection() {
  return (
    <Section id="vos-donnees" title="Vos données, sous contrôle">
      <div className="grid gap-6 md:grid-cols-3">
        {trustItems.map((item) => <div key={item.title} className="flex items-start gap-3"><item.icon aria-hidden="true" className="mt-0.5 h-5 w-5 shrink-0 text-secondary" /><div><h3 className="text-sm font-semibold">{item.title}</h3><p className="mt-2 text-sm leading-relaxed text-muted-foreground">{item.description}</p></div></div>)}
      </div>
      <a href="/help#confidentialite-securite" className="mt-6 inline-flex min-h-11 items-center gap-2 text-sm font-semibold underline underline-offset-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring">En savoir plus sur la confidentialité et la sécurité<ArrowRight aria-hidden="true" className="h-4 w-4 shrink-0 rtl:rotate-180" /></a>
    </Section>
  );
}

export interface PublicUpdate {
  id: string;
  title: string;
  summary: string;
  category: "Mise à jour d’une procédure" | "Nouveau service numérique" | "Information pratique";
  href: string;
}

export function PublicUpdates({ updates = [] }: { updates?: PublicUpdate[] }) {
  return (
    <Section id="actualites" title="Actualités des démarches et services publics" muted>
      {updates.length ? <div className="divide-y divide-border">{updates.map((update) => <a key={update.id} href={update.href} className="block rounded-lg py-4 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"><p className="text-xs font-medium text-secondary">{update.category}</p><h3 className="mt-2 font-semibold">{update.title}</h3><p className="mt-2 text-sm text-muted-foreground">{update.summary}</p><span className="mt-3 inline-flex items-center gap-2 text-sm underline underline-offset-4">Lire l’information<ArrowRight aria-hidden="true" className="h-4 w-4" /></span></a>)}</div>
        : <div className="flex items-start gap-4 rounded-xl border border-border bg-card p-5 sm:p-6"><Newspaper aria-hidden="true" className="mt-0.5 h-6 w-6 shrink-0 text-secondary" /><div><h3 className="text-sm font-semibold">Aucune actualité publiée pour le moment</h3><p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted-foreground">Les informations vérifiées concernant les démarches et services publics seront présentées ici lorsqu’elles seront disponibles.</p><Link href="/services" className="mt-3 inline-flex min-h-11 items-center gap-2 text-sm font-semibold underline underline-offset-4">Consulter les démarches disponibles<ArrowRight aria-hidden="true" className="h-4 w-4" /></Link></div></div>}
    </Section>
  );
}

export function HomeFooter() {
  return <footer className="border-t border-border bg-background py-7"><div className={`${container} flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between`}><div><Link href="/" className="inline-flex items-center gap-2 font-bold"><Landmark aria-hidden="true" className="h-5 w-5 text-primary" />OmniAgent</Link><p className="mt-2 text-xs text-muted-foreground">Un accompagnement pour vos démarches administratives.</p></div><nav aria-label="Liens de pied de page" className="flex flex-wrap gap-x-6 gap-y-2 text-sm"><Link href="/services" className="inline-flex min-h-11 items-center hover:underline">Services</Link><Link href="/help" className="inline-flex min-h-11 items-center gap-1.5 hover:underline"><CircleHelp aria-hidden="true" className="h-4 w-4" />Aide</Link><a href="/help#confidentialite-securite" className="inline-flex min-h-11 items-center hover:underline">Confidentialité et sécurité</a></nav></div></footer>;
}

function ScrollToTopButton() {
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
          aria-label="Remonter en haut"
          title="Remonter en haut"
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
  // Share the catalogue query and React Query cache with the existing Services page.
  const catalogue = useListServices();
  return <div lang="fr" dir="ltr"><HomeQuickActions /><LifeEventSection catalogue={catalogue} /><PopularServices catalogue={catalogue} /><PreparationFlow /><OmniAgentJourney /><ServiceFinder catalogue={catalogue} /><TrustSection /><PublicUpdates /><HomeFooter /><ScrollToTopButton /></div>;
}
