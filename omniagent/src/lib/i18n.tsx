import { createContext, useContext, useState, useEffect, ReactNode } from "react";

export type Language = "ar" | "fr" | "darija";

type Translations = Record<string, Record<Language, string>>;

export const translations: Translations = {
  "app.title": { ar: "أومني إيجنت", fr: "OmniAgent", darija: "أومني إيجنت" },
  "app.tagline": { ar: "مساعدك الذكي للخدمات الإدارية", fr: "Votre assistant IA pour les services publics", darija: "المساعد ديالك للخدمات الإدارية" },
  "nav.home": { ar: "الرئيسية", fr: "Accueil", darija: "الرئيسية" },
  "nav.services": { ar: "الخدمات", fr: "Services", darija: "الخدمات" },
  "nav.dashboard": { ar: "ملفاتي", fr: "Mes dossiers", darija: "ملفاتي" },
  "nav.chat": { ar: "المساعد الذكي", fr: "Assistant IA", darija: "المساعد الذكي" },
  "nav.admin": { ar: "الإدارة", fr: "Administration", darija: "الإدارة" },
  "nav.profile": { ar: "الملف الشخصي", fr: "Profil", darija: "الملف الشخصي" },
  "action.request": { ar: "طلب الآن", fr: "Demander", darija: "طلب دابا" },
  "action.submit": { ar: "إرسال", fr: "Soumettre", darija: "صيفط" },
  "action.cancel": { ar: "إلغاء", fr: "Annuler", darija: "إلغاء" },
  "status.submitted": { ar: "مقدم", fr: "Soumis", darija: "مقدم" },
  "status.in_review": { ar: "قيد المراجعة", fr: "En révision", darija: "قيد المراجعة" },
  "status.approved": { ar: "مقبول", fr: "Approuvé", darija: "مقبول" },
  "status.rejected": { ar: "مرفوض", fr: "Rejeté", darija: "مرفوض" },
  "status.pending_documents": { ar: "وثائق ناقصة", fr: "Documents en attente", darija: "وثائق ناقصة" },
  "services.title": { ar: "دليل الخدمات", fr: "Catalogue des Services", darija: "الخدمات الإدارية" },
  "services.processing": { ar: "أيام العمل", fr: "jours ouvrables", darija: "أيام العمل" },
  "services.docs": { ar: "وثائق مطلوبة", fr: "documents requis", darija: "وثائق مطلوبة" },
  "dashboard.active": { ar: "القضايا النشطة", fr: "Dossiers Actifs", darija: "القضايا النشطة" },
  "dashboard.pending_docs": { ar: "وثائق معلقة", fr: "Documents en Attente", darija: "وثائق معلقة" },
  "dashboard.avg_time": { ar: "متوسط وقت المعالجة", fr: "Temps Moyen de Traitement", darija: "متوسط وقت المعالجة" },
  "dashboard.approved": { ar: "تمت الموافقة", fr: "Approuvés", darija: "تمت الموافقة" },
  "chat.placeholder": { ar: "اكتب رسالتك...", fr: "Écrivez votre message...", darija: "كتب رسالتك..." },
  "chat.suggested": { ar: "أسئلة مقترحة", fr: "Questions suggérées", darija: "أسئلة مقترحة" },
  "profile.title": { ar: "الملف الشخصي والإعدادات", fr: "Profil & Paramètres", darija: "الملف الشخصي والإعدادات" },
  "admin.title": { ar: "لوحة الإدارة", fr: "Tableau de Bord Administration", darija: "لوحة الإدارة" },
};

interface I18nContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
  isRtl: boolean;
}

const I18nContext = createContext<I18nContextType | undefined>(undefined);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [language, setLanguageState] = useState<Language>("fr");

  useEffect(() => {
    const saved = localStorage.getItem("omniagent_lang") as Language;
    if (saved && ["ar", "fr", "darija"].includes(saved)) {
      setLanguageState(saved);
    }
  }, []);

  const setLanguage = (lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem("omniagent_lang", lang);
  };

  const isRtl = language === "ar" || language === "darija";

  useEffect(() => {
    document.documentElement.dir = isRtl ? "rtl" : "ltr";
    document.documentElement.lang = language;
  }, [language, isRtl]);

  const t = (key: string): string => {
    if (!translations[key]) {
      return key;
    }
    return translations[key][language];
  };

  return (
    <I18nContext.Provider value={{ language, setLanguage, t, isRtl }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  const context = useContext(I18nContext);
  if (context === undefined) {
    throw new Error("useI18n must be used within an I18nProvider");
  }
  return context;
}
