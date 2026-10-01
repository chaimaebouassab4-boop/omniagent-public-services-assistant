import type { Service } from "@/lib/api-client";
import { HOME_LIFE_EVENTS } from "@/lib/home-config";

const CATEGORY_LABELS: Record<string, string> = {
  civil_status: "État civil", civil: "État civil", family: "Famille",
  justice: "Justice", property: "Propriété", administrative: "Administration", general: "Services administratifs",
};

export function normalizeServiceSearch(value: string): string {
  return value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("fr").trim();
}

export function serviceCategoryLabel(service: Service): string | undefined {
  return service.category ? CATEGORY_LABELS[service.category] : undefined;
}

export function matchesServiceSearch(service: Service, query: string): boolean {
  const terms = normalizeServiceSearch(query).split(/\s+/).filter(Boolean);
  const content = normalizeServiceSearch([service.nameFr, service.nameAr, service.descriptionFr, service.descriptionAr, serviceCategoryLabel(service)].filter(Boolean).join(" "));
  return terms.every((term) => content.includes(term));
}

export function matchesLifeEvent(service: Service, eventId: string): boolean {
  const event = HOME_LIFE_EVENTS.find((item) => item.id === eventId);
  if (!event) return true;
  // Match titles, not mentions in other procedures' document descriptions.
  const title = normalizeServiceSearch(service.nameFr);
  return event.terms.some((term) => title.includes(normalizeServiceSearch(term)));
}

export function serviceDetailsHref(service: Service): string {
  return `/services?service=${service.id}`;
}
