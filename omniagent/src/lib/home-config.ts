import { BookOpen, FolderOpen, ListChecks, Search, House, Heart, FileQuestion, BriefcaseBusiness, Plane, GraduationCap } from "lucide-react";

// Entry points only: procedure content always comes from /api/services.
export const HOME_QUICK_ACTIONS = [
  { title: "Je m’informe", description: "Comprendre une démarche, ses étapes et les documents nécessaires.", icon: BookOpen, href: "/services" },
  { title: "Je prépare mon dossier", description: "Rassembler vos informations et préparer les pièces nécessaires.", icon: FolderOpen, href: "/services" },
  { title: "Je suis ma démarche", description: "Consulter l’état de vos dossiers préparés dans OmniAgent.", icon: ListChecks, href: "/dashboard", requiresAuth: true },
  { title: "Je trouve le bon service", description: "Identifier le service ou le portail correspondant à votre besoin.", icon: Search, href: "/#trouver-un-service" },
];

export const HOME_LIFE_EVENTS = [
  { id: "moving", title: "Je déménage", icon: House, terms: ["résidence", "domicile"] },
  { id: "marriage", title: "Je me marie", icon: Heart, terms: ["mariage", "célibat"] },
  { id: "lost-document", title: "Je perds un document", icon: FileQuestion, terms: ["perte", "duplicata", "remplacement"] },
  { id: "business", title: "Je crée une entreprise", icon: BriefcaseBusiness, terms: ["entreprise", "registre de commerce", "création de société"] },
  { id: "travel", title: "Je prépare un voyage", icon: Plane, terms: ["passeport", "visa", "voyage"] },
  { id: "work", title: "Je démarre ma vie professionnelle", icon: GraduationCap, terms: ["emploi", "travail", "professionnelle", "professionnel"] },
];
