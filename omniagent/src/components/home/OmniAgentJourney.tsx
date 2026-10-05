import { useState } from "react";
import * as AccordionPrimitive from "@radix-ui/react-accordion";
import { ArrowUpRight, Compass, Copy, FolderOpen, Route, ScanLine, Send } from "lucide-react";
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

export function OmniAgentJourney() {
  const { t, isRtl } = useI18n();
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
                      <Action href={href} className="mt-2.5 sm:mt-3 inline-flex min-h-11 max-w-full items-center gap-2 rounded-md text-xs sm:text-sm font-semibold omni-journey-accent underline decoration-primary/35 underline-offset-4 transition-colors hover:decoration-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
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
