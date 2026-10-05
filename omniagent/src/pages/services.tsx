import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useListServices, useCreateCase } from "@workspace/api-client-react";
import { motion, AnimatePresence } from "framer-motion";
import { createPortal } from "react-dom";
import { useQuery } from "@tanstack/react-query";
import { fetchMe, isAuthenticated } from "@/lib/auth";
import {
  Clock, FileText, ArrowRight, ArrowLeft, X, Phone, Mail,
  CheckCircle, ChevronRight, Search, ExternalLink, Banknote,
  Home, Baby, Heart, ScrollText, HeartPulse, UserCheck,
  Building2, ShieldCheck, Award, FileCheck, SearchX,
  Sparkles, Upload, Loader2,
  type LucideIcon,
} from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState, useMemo, useEffect, useRef } from "react";
import { useLocation, useSearch, Link } from "wouter";
import { useToast } from "@/hooks/use-toast";
import { analyzeAndExtractDocument } from "@/lib/documents";
import { SERVICES_META } from "@/lib/services-data";
import { HOME_LIFE_EVENTS } from "@/lib/home-config";
import { matchesLifeEvent, matchesServiceSearch } from "@/lib/service-discovery";

/* ─── Form Schema ─────────────────────────────────────────────── */
const formSchema = z.object({
  applicantName: z.string().min(2),
  applicantEmail: z.string().email(),
  applicantPhone: z.string().optional(),
  notes: z.string().optional(),
});

type ServiceFromApi = {
  id: number;
  nameFr: string;
  nameAr: string;
  descriptionFr: string;
  descriptionAr: string;
  processingDays: number;
  requiredDocuments: string[] | null;
};

/* ─── Icon & Category Mappings ────────────────────────────────── */
const SERVICE_ICON_MAP: Record<number, { icon: LucideIcon; color: string; bg: string }> = {
  1:  { icon: Home,        color: "text-blue-600",   bg: "bg-blue-50 dark:bg-blue-950/40" },
  2:  { icon: Baby,        color: "text-sky-500",    bg: "bg-sky-50 dark:bg-sky-950/40" },
  3:  { icon: Heart,       color: "text-rose-500",   bg: "bg-rose-50 dark:bg-rose-950/40" },
  4:  { icon: ScrollText,  color: "text-slate-500",  bg: "bg-slate-50 dark:bg-slate-800/40" },
  5:  { icon: HeartPulse,  color: "text-emerald-500",bg: "bg-emerald-50 dark:bg-emerald-950/40" },
  6:  { icon: UserCheck,   color: "text-indigo-500", bg: "bg-indigo-50 dark:bg-indigo-950/40" },
  7:  { icon: Building2,   color: "text-purple-500", bg: "bg-purple-50 dark:bg-purple-950/40" },
  8:  { icon: ShieldCheck, color: "text-amber-600",  bg: "bg-amber-50 dark:bg-amber-950/40" },
  9:  { icon: Award,       color: "text-teal-500",   bg: "bg-teal-50 dark:bg-teal-950/40" },
  10: { icon: FileCheck,   color: "text-cyan-500",   bg: "bg-cyan-50 dark:bg-cyan-950/40" },
};

const CATEGORIES = {
  all:       { fr: "Tous",        ar: "الكل" },
  civil:     { fr: "État civil",  ar: "الحالة المدنية" },
  family:    { fr: "Famille",     ar: "الأسرة" },
  justice:   { fr: "Justice",     ar: "العدل" },
  property:  { fr: "Propriété",   ar: "العقار" },
} as const;

type CategoryKey = keyof typeof CATEGORIES;

const SERVICE_CATEGORY: Record<number, CategoryKey> = {
  1: "civil", 2: "civil", 4: "civil", 5: "civil", 10: "civil",
  3: "family", 6: "family",
  8: "justice", 9: "justice",
  7: "property",
};

/* ─── Helpers ─────────────────────────────────────────────────── */
const getIcon = (id: number) => SERVICE_ICON_MAP[id] ?? SERVICE_ICON_MAP[1];

const DOCUMENT_NAMES: Record<string, { fr: string; ar: string }> = {
  both_ids: { fr: "Copies des CIN des deux époux", ar: "نسخ بطاقتي التعريف الوطنية للزوجين" },
  birth_certificates: { fr: "Actes de naissance des deux époux", ar: "عقود الازدياد للزوجين" },
  witness_documents: { fr: "Documents des témoins", ar: "وثائق الشهود" },
  national_id: { fr: "Carte d'Identité Nationale (CIN)", ar: "بطاقة التعريف الوطنية" },
  proof_of_residence: { fr: "Justificatif de domicile (Eau/Électricité)", ar: "إثبات السكن (فاتورة ماء/كهرباء)" },
  address_confirmation: { fr: "Attestation d'habitation", ar: "شهادة السكنى / السكن" },
  parent_id: { fr: "CIN du parent / tuteur légal", ar: "بطاقة التعريف للولي الشرعي" },
  marriage_certificate: { fr: "Acte de mariage des parents", ar: "عقد زواج الوالدين" },
  hospital_record: { fr: "Avis de naissance médical", ar: "إشعار الولادة الطبي" },
  declarant_id: { fr: "CIN du déclarant", ar: "بطاقة التعريف للمصرح" },
  medical_death_notice: { fr: "Constat de décès médical", ar: "شهادة الوفاة الطبية" },
  family_book: { fr: "Livret de famille", ar: "الدفتر العائلي" },
  residence_proof: { fr: "Justificatif de résidence", ar: "إثبات الإقامة" },
  witness_declaration: { fr: "Déclaration des témoins", ar: "تصريح الشهود" },
  birth_certificate: { fr: "Acte de naissance", ar: "عقد الازدياد" },
  non_property_proof: { fr: "Attestation de non-propriété", ar: "شهادة عدم الملكية" },
  tax_id: { fr: "Numéro d'identification fiscale", ar: "الرقم الضريبي" },
  identity_photos: { fr: "Photos d'identité récentes", ar: "صور شمسية حديثة" },
  diploma_copy: { fr: "Copie du diplôme", ar: "نسخة من الدبلوم" },
  tribunal_receipt: { fr: "Récépissé du tribunal", ar: "وصل المحكمة" },
  criminal_record_req: { fr: "Extrait de casier judiciaire", ar: "السجل العدلي" },
};

const getDocumentLabel = (reqKey: string, lang: string) => {
  const normLang = lang === "fr" ? "fr" : "ar";
  if (DOCUMENT_NAMES[reqKey]) {
    return DOCUMENT_NAMES[reqKey][normLang];
  }
  return reqKey
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
};

/* ─── Component ───────────────────────────────────────────────── */
export default function Services() {
  const { language, isRtl, t } = useI18n();
  const { data: services, isLoading } = useListServices();
  const queryString = useSearch();
  const params = useMemo(() => new URLSearchParams(queryString), [queryString]);
  const lifeEvent = HOME_LIFE_EVENTS.find((event) => event.id === params.get("lifeEvent"));
  const openedQueryRef = useRef<string | null>(null);
  const [selectedService, setSelectedService] = useState<ServiceFromApi | null>(null);
  const [detailService, setDetailService] = useState<ServiceFromApi | null>(null);
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState<CategoryKey>("all");
  const Arrow = isRtl ? ArrowLeft : ArrowRight;
  const [_, setLocation] = useLocation();

  const createCase = useCreateCase();
  const profile = useQuery({ queryKey: ["profile"], queryFn: fetchMe, staleTime: 0, enabled: isAuthenticated() });
  const [documentSelections, setDocumentSelections] = useState<Record<string, string>>({});
  const { toast } = useToast();
  const cinInputRef = useRef<HTMLInputElement>(null);
  const [isScanningCin, setIsScanningCin] = useState(false);

  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { applicantName: "", applicantEmail: "", applicantPhone: "", notes: "" },
  });

  useEffect(() => {
    setSearch(params.get("q") ?? "");
    setActiveCategory("all");
  }, [params]);

  useEffect(() => {
    if (!services || openedQueryRef.current === queryString) return;
    openedQueryRef.current = queryString;
    const serviceId = Number(params.get("service"));
    const requestedService = services.find((service) => service.id === serviceId && service.isActive !== false);
    setDetailService(requestedService ?? null);
  }, [services, params, queryString]);

  // Check for pre-filled data passed from chat.tsx (Feature 2 Task 2.2)
  useEffect(() => {
    if (!profile.data || !selectedService) return;
    form.reset({ applicantName: profile.data.fullName, applicantEmail: profile.data.email,
      applicantPhone: profile.data.phone ?? "", notes: "" });
    setDocumentSelections({});
  }, [selectedService?.id, profile.data?.id]);

  useEffect(() => {
    try {
      const saved = sessionStorage.getItem("omniagent_prefill");
      if (saved) {
        const parsed = JSON.parse(saved);
        if (parsed.applicantName) {
          form.setValue("applicantName", parsed.applicantName);
        }
        const notesExtra = [
          parsed.cinNumber ? `CIN: ${parsed.cinNumber}` : "",
          parsed.address ? `Adresse: ${parsed.address}` : "",
          parsed.birthDate ? `Né(e) le: ${parsed.birthDate}` : "",
        ].filter(Boolean).join(" | ");
        if (notesExtra) {
          form.setValue("notes", notesExtra);
        }

        // Auto-open first service dialog if none opened
        if (!selectedService && services && services.length > 0) {
          setSelectedService(services[0]);
          toast({
            title: language === "fr" ? "Données pré-remplies !" : "تم ملء البيانات تلقائياً!",
            description:
              language === "fr"
                ? `Les informations de votre ${parsed.documentType || "CIN"} ont été appliquées.`
                : "تم استخدام معلومات بطاقتك الوطنية بنجاح.",
          });
          sessionStorage.removeItem("omniagent_prefill");
        }
      }
    } catch {
      // ignore
    }
  }, [services, selectedService, form, language, toast]);

  const handleCinScan = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;

    setIsScanningCin(true);
    try {
      const data = await analyzeAndExtractDocument(file, language);
      if (data.full_name) {
        form.setValue("applicantName", data.full_name);
      } else if (data.first_name || data.last_name) {
        form.setValue("applicantName", `${data.first_name || ""} ${data.last_name || ""}`.trim());
      }
      const notesParts = [
        data.cin_number ? `CIN: ${data.cin_number}` : "",
        data.address ? `Adresse: ${data.address}` : "",
        data.birth_date ? `Né(e) le: ${data.birth_date}` : "",
      ].filter(Boolean).join(" | ");
      if (notesParts) {
        const currentNotes = form.getValues("notes") || "";
        form.setValue("notes", currentNotes ? `${currentNotes}\n${notesParts}` : notesParts);
      }

      toast({
        title: language === "fr" ? "CIN analysée avec succès !" : "تم فحص البطاقة بنجاح!",
        description:
          language === "fr"
            ? `Nom: ${form.getValues("applicantName")} · Confiance: ${Math.round(data.confidence_score * 100)}%`
            : "تم ملء الحقول بالبيانات المستخرجة.",
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Erreur de scan" : "خطأ في فحص الوثيقة",
        description: err instanceof Error ? err.message : String(err),
      });
    } finally {
      setIsScanningCin(false);
    }
  };

  const onSubmit = (values: z.infer<typeof formSchema>, submit = true) => {
    if (!selectedService) return;
    createCase.mutate(
      { data: { ...values, serviceId: selectedService.id, submit,
        documentReferences: Object.entries(documentSelections).filter(([, id]) => !!id).map(([requirement, documentId]) => ({ requirement, documentId })) } },
      {
        onSuccess: (newCase) => { setSelectedService(null); setLocation(`/cases/${newCase.id}`); },
        onError: (error) => toast({ variant: "destructive", title: language === "fr" ? "Demande impossible" : "تعذر إنشاء الطلب", description: error.message }),
      }
    );
  };

  const filtered = useMemo(() => {
    return (services ?? []).filter((s) => {
      const matchesSearch = matchesServiceSearch(s, search);
      const matchesCategory = activeCategory === "all" || SERVICE_CATEGORY[s.id] === activeCategory;
      return s.isActive !== false && matchesSearch && matchesCategory && (!lifeEvent || matchesLifeEvent(s, lifeEvent.id));
    });
  }, [services, search, activeCategory, lifeEvent]);

  const getName = (s: ServiceFromApi) => language === "fr" ? s.nameFr : s.nameAr;
  const getDesc = (s: ServiceFromApi) => language === "fr" ? s.descriptionFr : s.descriptionAr;
  const meta = (id: number) => SERVICES_META[id] ?? SERVICES_META[1];

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto space-y-6">

        {/* ── Breadcrumb ──────────────────────────────────────── */}
        <nav className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Link href="/" className="hover:text-foreground transition-colors">
            {language === "fr" ? "Accueil" : "الرئيسية"}
          </Link>
          <ChevronRight className="w-3 h-3" />
          <span className="text-foreground font-medium">
            {language === "fr" ? "Services" : "الخدمات"}
          </span>
        </nav>

        {/* ── Page Header ─────────────────────────────────────── */}
        <div className={`flex flex-col md:flex-row items-start md:items-end justify-between gap-4 ${isRtl ? "md:flex-row-reverse" : ""}`}>
          <div className="space-y-1.5">
            <h1 className="text-xl sm:text-2xl font-semibold text-foreground tracking-tight">
              {language === "fr" ? "Catalogue des services" : "فهرس الخدمات"}
            </h1>
            <p className="text-sm text-muted-foreground max-w-lg">
              {language === "fr"
                ? "Trouvez rapidement le service administratif dont vous avez besoin."
                : "ابحث بسرعة عن الخدمة الإدارية التي تحتاجها."}
            </p>
          </div>
          {/* Search */}
          <div className="relative w-full md:w-72">
            <Search className={`absolute top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground ${isRtl ? "right-3" : "left-3"}`} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={language === "fr" ? "Rechercher un service…" : "ابحث عن خدمة…"}
              className={`w-full h-9 rounded-lg border border-border bg-card text-sm placeholder:text-muted-foreground/60 focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50 transition-colors ${isRtl ? "pr-9 pl-3" : "pl-9 pr-3"}`}
            />
          </div>
        </div>

        {/* ── Category Filters ────────────────────────────────── */}
        {lifeEvent && <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-border bg-card p-3 text-sm"><p>{t(`home.life.${lifeEvent.id}`)}</p><Button variant="outline" size="sm" onClick={() => setLocation("/services")}>{t("home.popular.all")}</Button></div>}
        <div className={`flex items-center gap-1 overflow-x-auto max-w-full pb-1 scrollbar-none ${isRtl ? "flex-row-reverse" : ""}`}>
          {(Object.keys(CATEGORIES) as CategoryKey[]).map((key) => (
            <button
              key={key}
              onClick={() => setActiveCategory(key)}
              className={`px-3.5 py-1.5 rounded-md text-xs font-medium whitespace-nowrap transition-colors shrink-0 ${
                activeCategory === key
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted"
              }`}
            >
              {language === "fr" ? CATEGORIES[key].fr : CATEGORIES[key].ar}
            </button>
          ))}
        </div>

        {/* ── Service Grid ────────────────────────────────────── */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-xl border border-border bg-card p-4 sm:p-5 space-y-3">
                <div className="flex items-center gap-3">
                  <Skeleton className="h-10 w-10 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </div>
                </div>
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-2/3" />
                <Skeleton className="h-8 w-full" />
              </div>
            ))}
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {filtered.map((service, i) => {
              const m = meta(service.id);
              const iconInfo = getIcon(service.id);
              const Icon = iconInfo.icon;

              return (
                <motion.div
                  key={service.id}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="group flex flex-col rounded-xl border border-border bg-card overflow-hidden hover:shadow-md hover:border-primary/40 transition-all duration-200"
                >
                  <div className="flex flex-col flex-1 p-4 sm:p-5 gap-3 sm:gap-4">
                    {/* Icon + Status row */}
                    <div className="flex items-start justify-between">
                      <div className={`w-10 h-10 rounded-lg ${iconInfo.bg} flex items-center justify-center`}>
                        <Icon className={`w-5 h-5 ${iconInfo.color}`} />
                      </div>
                      <span className="flex items-center gap-1.5 text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        {language === "fr" ? "Disponible" : "متاح"}
                      </span>
                    </div>

                    {/* Title */}
                    <div>
                      <h3 className={`font-semibold text-foreground text-[15px] leading-snug ${isRtl ? "text-right" : ""}`}>
                        {getName(service)}
                      </h3>
                      <p className={`text-[11px] text-muted-foreground/70 mt-0.5 ${isRtl ? "text-right" : ""}`}>
                        {language === "fr" ? service.nameAr : service.nameFr}
                      </p>
                    </div>

                    {/* Description */}
                    <p className={`text-sm text-muted-foreground line-clamp-2 leading-relaxed flex-1 ${isRtl ? "text-right" : ""}`}>
                      {getDesc(service)}
                    </p>

                    {/* Admin info */}
                    <div className="flex flex-col gap-1.5 pt-3 border-t border-border/60 text-xs text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Clock className="w-3.5 h-3.5 shrink-0 opacity-60" />
                        <span>
                          {language === "fr" ? "Délai estimé" : "المدة المتوقعة"} : <span className="text-foreground font-medium">{service.processingDays} {language === "fr" ? "jours" : "أيام"}</span>
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 shrink-0 opacity-60" />
                        <span>
                          {language === "fr" ? "Documents requis" : "الوثائق المطلوبة"} : <span className="text-foreground font-medium">{service.requiredDocuments?.length ?? 0}</span>
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <Banknote className="w-3.5 h-3.5 shrink-0 opacity-60" />
                        <span>
                          {language === "fr" ? "Frais" : "الرسوم"} : <span className="text-foreground font-medium">{m.fee}</span>
                        </span>
                      </div>
                    </div>

                    {/* CTA */}
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full mt-1 text-xs font-medium text-primary border-primary/30 hover:bg-primary/5 hover:border-primary/50 gap-1.5 justify-center transition-colors"
                      onClick={() => setDetailService(service)}
                    >
                      {language === "fr" ? "Consulter le service" : "الاطلاع على الخدمة"}
                      <Arrow className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </motion.div>
              );
            })}

            {/* Empty State */}
            {filtered.length === 0 && (
              <div className="col-span-full flex flex-col items-center justify-center py-20 text-center">
                <div className="w-14 h-14 rounded-full bg-muted flex items-center justify-center mb-4">
                  <SearchX className="w-6 h-6 text-muted-foreground" />
                </div>
                <h3 className="text-base font-semibold text-foreground mb-1">
                  {language === "fr" ? "Aucun service trouvé" : "لم يُعثر على أي خدمة"}
                </h3>
                <p className="text-sm text-muted-foreground max-w-sm mb-4">
                  {language === "fr"
                    ? "Nous n'avons trouvé aucun service correspondant à votre recherche."
                    : "لم نعثر على أي خدمة تطابق بحثك."}
                </p>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => { setSearch(""); setActiveCategory("all"); setLocation("/services"); }}
                  className="text-xs"
                >
                  {language === "fr" ? "Réinitialiser les filtres" : "إعادة تعيين"}
                </Button>
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* ── DETAIL DRAWER ─────────────────────────────────────── */}
      {createPortal(<AnimatePresence>
        {detailService && (() => {
          const m = meta(detailService.id);
          const iconInfo = getIcon(detailService.id);
          const Icon = iconInfo.icon;
          const steps = language === "fr" ? m.stepsFr : m.stepsAr;
          const docs = language === "fr" ? m.docsRequiredFr : m.docsRequiredAr;
          return (
            <motion.div
              key="detail"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className={`fixed inset-0 z-50 flex ${isRtl ? "justify-start" : "justify-end"} overflow-hidden`}
              dir={isRtl ? "rtl" : "ltr"}
            >
              <div
                className="fixed inset-0 bg-black/50 backdrop-blur-sm"
                onClick={() => setDetailService(null)}
              />
              <motion.div
                initial={{ opacity: 0, x: isRtl ? -60 : 60 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: isRtl ? -60 : 60 }}
                transition={{ type: "spring", damping: 30, stiffness: 280 }}
                className="relative z-10 w-full sm:max-w-xl max-w-full h-full bg-background shadow-2xl overflow-y-auto flex flex-col border-x border-border"
              >
                {/* Header with icon (no image) */}
                <div className={`relative p-4 pb-4 sm:p-6 sm:pb-5 ${iconInfo.bg}`}>
                  <button
                    onClick={() => setDetailService(null)}
                    aria-label="Close"
                    className={`absolute top-3 sm:top-4 ${isRtl ? "left-3 sm:left-4" : "right-3 sm:right-4"} w-8 h-8 bg-black/10 hover:bg-black/20 rounded-full flex items-center justify-center text-foreground transition-colors`}
                  >
                    <X className="w-4 h-4" />
                  </button>

                  <div className={`w-12 h-12 rounded-xl bg-white/80 dark:bg-white/10 flex items-center justify-center mb-4 shadow-sm`}>
                    <Icon className={`w-6 h-6 ${iconInfo.color}`} />
                  </div>

                  <div className="flex items-center gap-2 mb-2">
                    <span className="px-2 py-0.5 text-[11px] font-medium rounded-md bg-primary/10 text-primary">
                      {m.fee}
                    </span>
                    <span className="flex items-center gap-1 px-2 py-0.5 text-[11px] font-medium rounded-md bg-muted text-muted-foreground">
                      <Clock className="w-3 h-3" />
                      {detailService.processingDays} {language === "fr" ? "jours" : "أيام"}
                    </span>
                  </div>
                  <h2 className="font-semibold text-lg sm:text-xl text-foreground leading-tight">{getName(detailService)}</h2>
                  <p className="text-xs text-muted-foreground mt-0.5">{language === "fr" ? detailService.nameAr : detailService.nameFr}</p>
                </div>

                <div className="p-4 space-y-4 sm:p-6 sm:space-y-6 flex-1 overflow-y-auto">
                  {/* Description */}
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {language === "fr" ? m.descLongFr : m.descLongAr}
                  </p>

                  {/* Office */}
                  <div className="flex items-start gap-3 p-3 rounded-lg bg-muted/50 border border-border/50">
                    <ExternalLink className="w-4 h-4 text-secondary mt-0.5 shrink-0" />
                    <div>
                      <p className="text-xs font-semibold text-foreground mb-0.5">{language === "fr" ? "Organisme compétent" : "الجهة المختصة"}</p>
                      <p className="text-xs text-muted-foreground">{language === "fr" ? m.office.fr : m.office.ar}</p>
                    </div>
                  </div>

                  {/* Steps */}
                  <div>
                    <h3 className="font-semibold text-foreground mb-3 text-sm">
                      {language === "fr" ? "Étapes à suivre" : "الخطوات المطلوبة"}
                    </h3>
                    <div className="space-y-3">
                      {steps.map((step, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="w-6 h-6 rounded-full bg-primary text-primary-foreground text-xs flex items-center justify-center shrink-0 font-semibold mt-0.5">
                            {i + 1}
                          </div>
                          <p className="text-sm text-foreground leading-relaxed flex-1">{step}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Documents */}
                  <div>
                    <h3 className="font-semibold text-foreground mb-3 text-sm">
                      {language === "fr" ? "Documents requis" : "الوثائق المطلوبة"}
                    </h3>
                    <div className="space-y-2">
                      {docs.map((doc, i) => (
                        <div key={i} className="flex items-start gap-2.5">
                          <CheckCircle className="w-4 h-4 text-secondary shrink-0 mt-0.5" />
                          <span className="text-sm text-foreground leading-relaxed flex-1">{doc}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Tip */}
                  <div className="flex items-start gap-3 p-4 rounded-lg bg-blue-50 dark:bg-blue-950/20 border border-blue-100 dark:border-blue-900/30">
                    <div className="w-5 h-5 rounded-full bg-blue-100 dark:bg-blue-900/40 flex items-center justify-center shrink-0 mt-0.5">
                      <span className="text-blue-600 dark:text-blue-400 text-[10px] font-bold">i</span>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-blue-800 dark:text-blue-300 mb-0.5">{language === "fr" ? "Bon à savoir" : "معلومة مفيدة"}</p>
                      <p className="text-xs text-blue-700/90 dark:text-blue-300/80 leading-relaxed">
                        {language === "fr" ? m.tip.fr : m.tip.ar}
                      </p>
                    </div>
                  </div>

                  {/* Contact support */}
                  <div>
                    <h3 className="font-semibold text-foreground mb-3 text-sm">
                      {language === "fr" ? "Contacter le support" : "التواصل مع الدعم"}
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <a href={`mailto:${m.supportEmail}`} className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-secondary/40 hover:bg-secondary/5 transition-colors">
                        <div className="w-8 h-8 bg-secondary/10 rounded-lg flex items-center justify-center shrink-0">
                          <Mail className="w-4 h-4 text-secondary" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-foreground">Email</p>
                          <p className="text-xs text-muted-foreground truncate">{m.supportEmail}</p>
                        </div>
                      </a>
                      <a href={`tel:${m.supportPhone}`} className="flex items-center gap-3 p-3 rounded-lg border border-border hover:border-secondary/40 hover:bg-secondary/5 transition-colors">
                        <div className="w-8 h-8 bg-secondary/10 rounded-lg flex items-center justify-center shrink-0">
                          <Phone className="w-4 h-4 text-secondary" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-foreground">{language === "fr" ? "Téléphone" : "الهاتف"}</p>
                          <p className="text-xs text-muted-foreground">{m.supportPhone}</p>
                        </div>
                      </a>
                    </div>
                  </div>
                </div>

                {/* Sticky CTA Bottom */}
                <div className="p-3 sm:p-4 border-t border-border bg-background/95 backdrop-blur-sm sticky bottom-0 z-20 flex flex-col sm:flex-row gap-2 sm:gap-3">
                  <Button variant="outline" className="w-full sm:flex-1" onClick={() => setDetailService(null)}>
                    {language === "fr" ? "Fermer" : "إغلاق"}
                  </Button>
                  <Button
                    className="w-full sm:flex-1 gap-2 font-medium bg-primary hover:bg-primary/90 text-primary-foreground"
                    onClick={() => {
                      if (!isAuthenticated()) {
                        setLocation(`/login?returnTo=${encodeURIComponent(`/services?service=${detailService.id}`)}`);
                        return;
                      }
                      setDetailService(null);
                      setSelectedService(detailService);
                    }}
                  >
                    {language === "fr" ? "Démarrer la démarche" : "بدء الإجراء"}
                    <Arrow className="w-4 h-4" />
                  </Button>
                </div>
              </motion.div>
            </motion.div>
          );
        })()}
      </AnimatePresence>, document.body)}

      {/* ── REQUEST DIALOG ────────────────────────────────────── */}
      <Dialog open={selectedService !== null} onOpenChange={(open) => !open && setSelectedService(null)}>
        <DialogContent className="w-[calc(100vw-1.5rem)] sm:max-w-[480px] max-h-[90vh] sm:max-h-[85vh] flex flex-col p-0 overflow-hidden" dir={isRtl ? "rtl" : "ltr"}>
          <DialogHeader className="p-4 pb-3 sm:p-5 sm:pb-3 border-b border-border shrink-0">
            <DialogTitle className="flex items-center gap-2.5 text-base">
              {selectedService && (() => {
                const iconInfo = getIcon(selectedService.id);
                const Icon = iconInfo.icon;
                return (
                  <div className={`w-7 h-7 rounded-md ${iconInfo.bg} flex items-center justify-center shrink-0`}>
                    <Icon className={`w-4 h-4 ${iconInfo.color}`} />
                  </div>
                );
              })()}
              <span>{language === "fr" ? "Démarrer la démarche" : "بدء الإجراء"}</span>
            </DialogTitle>
            <DialogDescription className="text-xs text-muted-foreground mt-0.5">
              {selectedService && (
                <span className="font-medium text-foreground">{getName(selectedService)}</span>
              )}
              {" — "}{language === "fr" ? "Remplissez vos informations" : "أدخل معلوماتك"}
            </DialogDescription>
          </DialogHeader>

          <Form {...form}>
            <form onSubmit={form.handleSubmit((values) => onSubmit(values, true))} className="flex flex-col flex-1 overflow-hidden">
              <div className="p-4 space-y-3.5 sm:p-5 sm:space-y-4 overflow-y-auto flex-1">
                {/* Feature 2: Smart OCR Auto-fill Button */}
                <div className="rounded-xl border border-primary/20 bg-primary/5 p-3 flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3">
                  <div className="flex items-center gap-2.5 min-w-0">
                    <div className="w-8 h-8 rounded-lg bg-primary/10 text-primary flex items-center justify-center shrink-0">
                      <Sparkles className="w-4 h-4 text-amber-500 animate-pulse" />
                    </div>
                    <div className="min-w-0">
                      <div className="text-xs font-semibold text-foreground">
                        {language === "fr" ? "Auto-remplir avec ma CIN" : "ملء تلقائي عبر البطاقة الوطنية"}
                      </div>
                      <p className="text-[11px] text-muted-foreground truncate">
                        {language === "fr" ? "Scannez votre CIN pour remplir en 1 clic" : "فحص ذكي للبطاقة لملء البيانات فوراً"}
                      </p>
                    </div>
                  </div>
                  <input
                    ref={cinInputRef}
                    type="file"
                    accept="application/pdf,image/jpeg,image/png,image/webp"
                    className="hidden"
                    onChange={handleCinScan}
                    data-testid="input-scan-cin"
                  />
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    disabled={isScanningCin}
                    onClick={() => cinInputRef.current?.click()}
                    className="shrink-0 text-xs gap-1.5 h-8 border-primary/30 hover:bg-primary/10 text-primary font-medium w-full sm:w-auto justify-center"
                  >
                    {isScanningCin ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <Upload className="w-3.5 h-3.5" />
                    )}
                    {isScanningCin
                      ? (language === "fr" ? "Scan en cours…" : "جاري الفحص…")
                      : (language === "fr" ? "Scanner" : "فحص")}
                  </Button>
                </div>

                {[
                  { name: "applicantName" as const, label: { fr: "Nom complet", ar: "الاسم الكامل" }, placeholder: "Ahmed Benali" },
                  { name: "applicantEmail" as const, label: { fr: "Email", ar: "البريد الإلكتروني" }, type: "email", placeholder: "ahmed@example.ma" },
                  { name: "applicantPhone" as const, label: { fr: "Téléphone", ar: "رقم الهاتف" }, placeholder: "+212 6..." },
                ].map(({ name, label, placeholder, type }) => (
                  <FormField
                    key={name}
                    control={form.control}
                    name={name}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel className="text-xs font-medium">{language === "fr" ? label.fr : label.ar}</FormLabel>
                        <FormControl>
                          <Input className="h-9 text-xs" type={type ?? "text"} placeholder={placeholder} {...field} />
                        </FormControl>
                        <FormMessage className="text-xs" />
                      </FormItem>
                    )}
                  />
                ))}

                {/* Required Documents Selector Section */}
                {selectedService?.requiredDocuments && selectedService.requiredDocuments.length > 0 && (
                  <div className="space-y-3 pt-3 border-t border-border/70">
                    <div className="text-xs font-semibold text-foreground flex items-center gap-1.5">
                      <FileText className="w-3.5 h-3.5 text-primary" />
                      <span>{language === "fr" ? "Documents requis à associer" : "الوثائق المطلوبة للإرفاق"}</span>
                    </div>
                    {profile.isError && (
                      <p className="text-xs text-destructive">
                        {language === "fr" ? "Profil indisponible. Réessayez." : "الملف الشخصي غير متاح."}
                      </p>
                    )}
                    {selectedService.requiredDocuments.map((requirement) => (
                      <div key={requirement} className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground block">
                          {getDocumentLabel(requirement, language)}
                        </label>
                        <select
                          className="w-full h-9 rounded-md border border-input bg-background px-3 py-1 text-xs shadow-sm focus:outline-none focus:ring-1 focus:ring-primary/50 transition-colors"
                          value={documentSelections[requirement] ?? ""}
                          onChange={(e) =>
                            setDocumentSelections((previous) => ({
                              ...previous,
                              [requirement]: e.target.value,
                            }))
                          }
                        >
                          <option value="">
                            {language === "fr"
                              ? "Déposer plus tard / choisir du profil"
                              : "الإيداع لاحقاً / اختيار من الملف الشخصي"}
                          </option>
                          {profile.data?.reusableDocuments?.map((doc) => (
                            <option key={doc.id} value={doc.id}>
                              {doc.name}
                            </option>
                          ))}
                        </select>
                      </div>
                    ))}
                  </div>
                )}

                <FormField
                  control={form.control}
                  name="notes"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel className="text-xs font-medium">{language === "fr" ? "Notes (optionnel)" : "ملاحظات (اختياري)"}</FormLabel>
                      <FormControl><Textarea className="text-xs min-h-[70px]" placeholder="..." {...field} /></FormControl>
                      <FormMessage className="text-xs" />
                    </FormItem>
                  )}
                />
              </div>

              <DialogFooter className="p-3 sm:p-4 border-t border-border bg-muted/20 flex flex-col-reverse sm:flex-row items-stretch sm:items-center justify-end gap-2 shrink-0">
                <Button type="button" variant="outline" size="sm" className="h-8 text-xs w-full sm:w-auto" onClick={() => setSelectedService(null)}>
                  {language === "fr" ? "Annuler" : "إلغاء"}
                </Button>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  className="h-8 text-xs w-full sm:w-auto"
                  disabled={createCase.isPending}
                  onClick={form.handleSubmit((values) => onSubmit(values, false))}
                >
                  {language === "fr" ? "Brouillon" : "مسودة"}
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  className="h-8 text-xs bg-primary hover:bg-primary/90 text-primary-foreground font-medium w-full sm:w-auto"
                  disabled={createCase.isPending}
                >
                  {createCase.isPending
                    ? (language === "fr" ? "Envoi…" : "جاري الإرسال…")
                    : (language === "fr" ? "Envoyer la demande" : "إرسال الطلب")}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
