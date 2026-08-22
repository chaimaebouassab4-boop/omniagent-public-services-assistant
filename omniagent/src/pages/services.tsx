import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useListServices, useCreateCase } from "@workspace/api-client-react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Clock, FileText, ArrowRight, ArrowLeft, X, Phone, Mail,
  CheckCircle, ChevronRight, Search, Star, ExternalLink
} from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { useLocation } from "wouter";
import { SERVICES_META } from "@/lib/services-data";

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

export default function Services() {
  const { language, isRtl } = useI18n();
  const { data: services, isLoading } = useListServices();
  const [selectedService, setSelectedService] = useState<ServiceFromApi | null>(null);
  const [detailService, setDetailService] = useState<ServiceFromApi | null>(null);
  const [search, setSearch] = useState("");
  const Arrow = isRtl ? ArrowLeft : ArrowRight;
  const [_, setLocation] = useLocation();

  const createCase = useCreateCase();
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: { applicantName: "", applicantEmail: "", applicantPhone: "", notes: "" },
  });

  const onSubmit = (values: z.infer<typeof formSchema>) => {
    if (!selectedService) return;
    createCase.mutate(
      { data: { ...values, serviceId: selectedService.id } },
      { onSuccess: (newCase) => { setSelectedService(null); setLocation(`/cases/${newCase.id}`); } }
    );
  };

  const filtered = (services ?? []).filter((s) => {
    const q = search.toLowerCase();
    return !q || s.nameFr.toLowerCase().includes(q) || s.nameAr.includes(q);
  });

  const getName = (s: ServiceFromApi) => language === "fr" ? s.nameFr : s.nameAr;
  const getDesc = (s: ServiceFromApi) => language === "fr" ? s.descriptionFr : s.descriptionAr;

  const meta = (id: number) => SERVICES_META[id] ?? SERVICES_META[1];

  return (
    <AppLayout>
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className={`flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 ${isRtl ? "sm:flex-row-reverse" : ""}`}>
          <div>
            <h1 className="text-3xl font-bold text-foreground">
              {language === "fr" ? "Catalogue des Services" : language === "ar" ? "فهرس الخدمات" : "كاتالوج الخدمات"}
            </h1>
            <p className="text-muted-foreground mt-1">
              {language === "fr" ? "Toutes vos démarches, un seul endroit" : language === "ar" ? "جميع إجراءاتك في مكان واحد" : "جميع خدماتك ف بلاصة واحدة"}
            </p>
          </div>
          {/* Search */}
          <div className="relative w-full sm:w-72">
            <Search className={`absolute top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground ${isRtl ? "right-3" : "left-3"}`} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder={language === "fr" ? "Rechercher un service..." : "ابحث عن خدمة..."}
              className={`w-full h-10 rounded-lg border border-border bg-card text-sm focus:outline-none focus:ring-2 focus:ring-primary/30 ${isRtl ? "pr-10 pl-4" : "pl-10 pr-4"}`}
            />
          </div>
        </div>

        {/* Grid */}
        {isLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="rounded-2xl border border-border overflow-hidden">
                <Skeleton className="h-44 w-full" />
                <div className="p-5 space-y-3">
                  <Skeleton className="h-5 w-3/4" />
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-2/3" />
                  <Skeleton className="h-9 w-full" />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
          >
            {filtered.map((service, i) => {
              const m = meta(service.id);
              return (
                <motion.div
                  key={service.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.07 }}
                  className="group flex flex-col rounded-2xl border border-border bg-card overflow-hidden hover:shadow-lg transition-all hover:-translate-y-1"
                >
                  {/* Image */}
                  <div className="relative h-44 overflow-hidden bg-muted">
                    <img
                      src={m.image}
                      alt={service.nameFr}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                    />
                    <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/10 to-transparent" />
                    <div className="absolute top-3 left-3 flex gap-2">
                      <span className="text-2xl">{m.emoji}</span>
                    </div>
                    <div className="absolute bottom-3 left-3 right-3">
                      <div className="flex items-center gap-2">
                        <Badge className="bg-white/20 text-white border-white/30 text-xs backdrop-blur-sm">
                          <Clock className="w-3 h-3 mr-1" />{service.processingDays}j
                        </Badge>
                        <Badge className="bg-white/20 text-white border-white/30 text-xs backdrop-blur-sm">
                          {m.fee}
                        </Badge>
                      </div>
                    </div>
                  </div>

                  {/* Content */}
                  <div className="flex flex-col flex-1 p-5 gap-3">
                    <div>
                      <h3 className={`font-bold text-foreground text-base leading-snug ${isRtl ? "text-right" : ""}`}>
                        {getName(service)}
                      </h3>
                      <p className="text-xs text-muted-foreground mt-0.5">
                        {language === "fr" ? service.nameAr : service.nameFr}
                      </p>
                    </div>
                    <p className={`text-sm text-muted-foreground line-clamp-2 leading-relaxed flex-1 ${isRtl ? "text-right" : ""}`}>
                      {getDesc(service)}
                    </p>

                    {/* Quick info */}
                    <div className="flex items-center gap-3 text-xs text-muted-foreground border-t border-border pt-3">
                      <div className="flex items-center gap-1">
                        <FileText className="w-3.5 h-3.5" />
                        <span>{service.requiredDocuments?.length ?? 0} {language === "fr" ? "docs" : "وثائق"}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Star className="w-3.5 h-3.5 fill-amber-400 text-amber-400" />
                        <span>{m.fee}</span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2 mt-1">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 text-xs gap-1"
                        onClick={() => setDetailService(service)}
                      >
                        {language === "fr" ? "Voir détails" : "التفاصيل"}
                        <ChevronRight className="w-3 h-3" />
                      </Button>
                      <Button
                        size="sm"
                        className="flex-1 text-xs gap-1"
                        onClick={() => setSelectedService(service)}
                      >
                        {language === "fr" ? "Déposer" : "تقديم"}
                        <Arrow className="w-3 h-3" />
                      </Button>
                    </div>
                  </div>
                </motion.div>
              );
            })}
            {filtered.length === 0 && (
              <div className="col-span-3 text-center py-16 text-muted-foreground">
                {language === "fr" ? "Aucun service trouvé." : "لم يُعثر على أي خدمة."}
              </div>
            )}
          </motion.div>
        )}
      </div>

      {/* ── DETAIL DRAWER ─────────────────────────────────────── */}
      <AnimatePresence>
        {detailService && (() => {
          const m = meta(detailService.id);
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
                className="fixed inset-0 bg-black/60 backdrop-blur-sm"
                onClick={() => setDetailService(null)}
              />
              <motion.div
                initial={{ opacity: 0, x: isRtl ? -80 : 80 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: isRtl ? -80 : 80 }}
                transition={{ type: "spring", damping: 28, stiffness: 260 }}
                className="relative z-10 w-full sm:max-w-xl max-w-full h-full bg-background shadow-2xl overflow-y-auto flex flex-col border-x border-border"
              >
                {/* Image header */}
                <div className="relative h-56 shrink-0">
                  <img src={m.image} alt={detailService.nameFr} className="w-full h-full object-cover" />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />
                  <button
                    onClick={() => setDetailService(null)}
                    aria-label="Close"
                    className={`absolute top-4 ${isRtl ? "left-4" : "right-4"} w-9 h-9 bg-black/50 hover:bg-black/75 rounded-full flex items-center justify-center text-white transition-colors backdrop-blur-sm shadow-md`}
                  >
                    <X className="w-5 h-5" />
                  </button>
                  <div className="absolute bottom-4 left-5 right-5">
                    <div className="flex flex-wrap gap-2 mb-2">
                      <Badge className="bg-primary text-white border-0 font-medium">{m.fee}</Badge>
                      <Badge className="bg-white/25 text-white border-white/40 backdrop-blur-sm font-medium">
                        <Clock className="w-3.5 h-3.5 mr-1" />{detailService.processingDays} {language === "fr" ? "jours" : "أيام"}
                      </Badge>
                    </div>
                    <h2 className="text-white font-bold text-2xl leading-tight drop-shadow-sm">{getName(detailService)}</h2>
                    <p className="text-white/80 text-xs mt-0.5">{language === "fr" ? detailService.nameAr : detailService.nameFr}</p>
                  </div>
                </div>

                <div className="p-6 space-y-6 flex-1 overflow-y-auto">
                  {/* Description */}
                  <p className="text-muted-foreground text-sm leading-relaxed">
                    {language === "fr" ? m.descLongFr : m.descLongAr}
                  </p>

                  {/* Office */}
                  <div className="flex items-start gap-3 p-3 rounded-xl bg-muted/60">
                    <ExternalLink className="w-4 h-4 text-primary mt-0.5 shrink-0" />
                    <div>
                      <p className="text-xs font-semibold text-foreground mb-0.5">{language === "fr" ? "Organisme compétent" : "الجهة المختصة"}</p>
                      <p className="text-xs text-muted-foreground">{language === "fr" ? m.office.fr : m.office.ar}</p>
                    </div>
                  </div>

                  {/* Steps */}
                  <div>
                    <h3 className="font-semibold text-foreground mb-3 text-base">
                      {language === "fr" ? "Étapes à suivre" : "الخطوات المطلوبة"}
                    </h3>
                    <div className="space-y-3">
                      {steps.map((step, i) => (
                        <div key={i} className="flex items-start gap-3">
                          <div className="w-6 h-6 rounded-full bg-primary text-white text-xs flex items-center justify-center shrink-0 font-bold mt-0.5">
                            {i + 1}
                          </div>
                          <p className="text-sm text-foreground leading-relaxed flex-1">{step}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Documents */}
                  <div>
                    <h3 className="font-semibold text-foreground mb-3 text-base">
                      {language === "fr" ? "Documents requis" : "الوثائق المطلوبة"}
                    </h3>
                    <div className="space-y-2.5">
                      {docs.map((doc, i) => (
                        <div key={i} className="flex items-start gap-2.5">
                          <CheckCircle className="w-4 h-4 text-primary shrink-0 mt-0.5" />
                          <span className="text-sm text-foreground leading-relaxed flex-1">{doc}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Tip */}
                  <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
                    <span className="text-xl shrink-0">💡</span>
                    <div>
                      <p className="text-xs font-semibold text-amber-800 dark:text-amber-300 mb-1">{language === "fr" ? "Bon à savoir" : "معلومة مفيدة"}</p>
                      <p className="text-xs text-amber-800/90 dark:text-amber-300/90 leading-relaxed">
                        {language === "fr" ? m.tip.fr : m.tip.ar}
                      </p>
                    </div>
                  </div>

                  {/* Contact support */}
                  <div>
                    <h3 className="font-semibold text-foreground mb-3 text-base">
                      {language === "fr" ? "Contacter le support" : "التواصل مع الدعم"}
                    </h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                      <a href={`mailto:${m.supportEmail}`} className="flex items-center gap-3 p-3 rounded-xl border border-border hover:border-primary/50 hover:bg-primary/5 transition-colors">
                        <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center shrink-0">
                          <Mail className="w-4 h-4 text-primary" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-foreground">Email</p>
                          <p className="text-xs text-muted-foreground truncate">{m.supportEmail}</p>
                        </div>
                      </a>
                      <a href={`tel:${m.supportPhone}`} className="flex items-center gap-3 p-3 rounded-xl border border-border hover:border-primary/50 hover:bg-primary/5 transition-colors">
                        <div className="w-8 h-8 bg-secondary/10 rounded-lg flex items-center justify-center shrink-0">
                          <Phone className="w-4 h-4 text-secondary" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-medium text-foreground">Téléphone</p>
                          <p className="text-xs text-muted-foreground">{m.supportPhone}</p>
                        </div>
                      </a>
                    </div>
                  </div>
                </div>

                {/* Sticky CTA Bottom */}
                <div className="p-4 border-t border-border bg-background/95 backdrop-blur-sm sticky bottom-0 z-20 flex gap-3 shadow-lg">
                  <Button variant="outline" className="flex-1" onClick={() => setDetailService(null)}>
                    {language === "fr" ? "Fermer" : "إغلاق"}
                  </Button>
                  <Button
                    className="flex-1 gap-2 font-medium"
                    onClick={() => { setDetailService(null); setSelectedService(detailService); }}
                  >
                    {language === "fr" ? "Déposer ma demande" : "تقديم الطلب"}
                    <Arrow className="w-4 h-4" />
                  </Button>
                </div>
              </motion.div>
            </motion.div>
          );
        })()}
      </AnimatePresence>

      {/* ── REQUEST DIALOG ────────────────────────────────────── */}
      <Dialog open={selectedService !== null} onOpenChange={(open) => !open && setSelectedService(null)}>
        <DialogContent className="sm:max-w-[440px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              {selectedService && <span>{meta(selectedService.id).emoji}</span>}
              {language === "fr" ? "Déposer une demande" : "تقديم طلب"}
            </DialogTitle>
            <DialogDescription>
              {selectedService && (
                <span className="font-medium text-foreground">{getName(selectedService)}</span>
              )}
              {" — "}{language === "fr" ? "Remplissez vos informations" : "أدخل معلوماتك"}
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
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
                      <FormLabel>{language === "fr" ? label.fr : label.ar}</FormLabel>
                      <FormControl>
                        <Input type={type ?? "text"} placeholder={placeholder} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              ))}
              <FormField
                control={form.control}
                name="notes"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>{language === "fr" ? "Notes (optionnel)" : "ملاحظات (اختياري)"}</FormLabel>
                    <FormControl><Textarea placeholder="..." {...field} /></FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <DialogFooter className="pt-2">
                <Button type="button" variant="outline" onClick={() => setSelectedService(null)}>
                  {language === "fr" ? "Annuler" : "إلغاء"}
                </Button>
                <Button type="submit" disabled={createCase.isPending}>
                  {createCase.isPending
                    ? (language === "fr" ? "Envoi..." : "جاري الإرسال...")
                    : (language === "fr" ? "Envoyer" : "إرسال")}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
