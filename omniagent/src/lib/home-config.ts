import { BookOpen, FolderOpen, ListChecks, Search, House, Heart, FileQuestion, BriefcaseBusiness, Plane, GraduationCap } from "lucide-react";

// Entry points only: procedure content always comes from /api/services.
export const HOME_QUICK_ACTIONS = [
  { id: "inform", icon: BookOpen, href: "/services" },
  { id: "prepare", icon: FolderOpen, href: "/services" },
  { id: "track", icon: ListChecks, href: "/dashboard", requiresAuth: true },
  { id: "find", icon: Search, href: "/#trouver-un-service" },
];

export const HOME_LIFE_EVENTS = [
  { id: "moving", icon: House, terms: ["résidence", "domicile"] },
  { id: "marriage", icon: Heart, terms: ["mariage", "célibat"] },
  { id: "lost-document", icon: FileQuestion, terms: ["perte", "duplicata", "remplacement"] },
  { id: "business", icon: BriefcaseBusiness, terms: ["entreprise", "registre de commerce", "création de société"] },
  { id: "travel", icon: Plane, terms: ["passeport", "visa", "voyage"] },
  { id: "work", icon: GraduationCap, terms: ["emploi", "travail", "professionnelle", "professionnel"] },
];
