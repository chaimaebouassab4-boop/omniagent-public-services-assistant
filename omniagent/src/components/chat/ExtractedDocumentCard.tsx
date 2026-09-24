import { useState, useMemo } from "react";
import { useI18n } from "@/lib/i18n";
import type { ExtractedDocumentMetadata } from "@/lib/documents";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  FileText,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Sparkles,
  Pencil,
  Check,
  Calendar,
  MapPin,
  CreditCard,
  User,
  ShieldCheck,
  X,
  Send,
} from "lucide-react";

export interface ExtractedDocumentCardProps {
  metadata: ExtractedDocumentMetadata;
  file: File;
  onPreFillRequest: (fields: {
    applicantName: string;
    cinNumber: string;
    address: string;
    birthDate: string;
    documentType: string;
  }) => void;
  onSendToChat?: (customMessage?: string) => void;
  onDismiss: () => void;
  className?: string;
}

export function ExtractedDocumentCard({
  metadata,
  file,
  onPreFillRequest,
  onSendToChat,
  onDismiss,
  className = "",
}: ExtractedDocumentCardProps) {
  const { language, isRtl } = useI18n();

  // Local editable state so citizen can correct OCR typos
  const [firstName, setFirstName] = useState(metadata.first_name || "");
  const [lastName, setLastName] = useState(metadata.last_name || "");
  const [cinNumber, setCinNumber] = useState(metadata.cin_number || "");
  const [birthDate, setBirthDate] = useState(metadata.birth_date || "");
  const [address, setAddress] = useState(metadata.address || "");
  const [editingField, setEditingField] = useState<string | null>(null);

  const loadDemoProfile = () => {
    setFirstName("Ahmed");
    setLastName("Benali");
    setCinNumber("BK654321");
    setBirthDate("15/05/1992");
    setAddress("45 Boulevard d'Anfa, Casablanca");
  };

  // Generate local thumbnail URL
  const thumbnailUrl = useMemo(() => {
    if (file.type.startsWith("image/")) {
      try {
        return URL.createObjectURL(file);
      } catch {
        return null;
      }
    }
    return null;
  }, [file]);

  const docTypeLabel =
    metadata.document_type_label?.[language as "fr" | "ar" | "darija"] ||
    metadata.document_type_label?.fr ||
    metadata.document_type;

  const confidencePct = Math.round(metadata.confidence_score * 100);

  const handlePreFill = () => {
    const fullName = `${firstName} ${lastName}`.trim() || metadata.full_name || "";
    onPreFillRequest({
      applicantName: fullName,
      cinNumber,
      address,
      birthDate,
      documentType: metadata.document_type,
    });
  };

  return (
    <div
      className={`rounded-2xl border border-primary/25 bg-card/95 p-4 shadow-lg backdrop-blur-sm transition-all duration-300 ${className}`}
      dir={isRtl ? "rtl" : "ltr"}
      data-testid="extracted-document-card"
    >
      {/* ── Header: Document Badge + Status + Dismiss ────────────────────── */}
      <div className="flex items-start justify-between gap-3 pb-3 border-b border-border/50">
        <div className="flex items-center gap-3">
          {thumbnailUrl ? (
            <img
              src={thumbnailUrl}
              alt="Thumbnail"
              className="h-12 w-12 rounded-xl object-cover border border-border shadow-xs"
            />
          ) : (
            <div className="h-12 w-12 rounded-xl bg-primary/10 text-primary border border-primary/20 flex items-center justify-center shrink-0">
              <FileText className="h-6 w-6" />
            </div>
          )}
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-sm text-foreground">
                {docTypeLabel}
              </span>
              {metadata.is_valid && !metadata.is_expired ? (
                <Badge
                  variant="outline"
                  className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-[11px] gap-1 py-0.5"
                >
                  <CheckCircle2 className="w-3 h-3" />
                  {language === "fr" ? "Conforme" : "صالح"}
                </Badge>
              ) : metadata.is_expired ? (
                <Badge
                  variant="outline"
                  className="bg-destructive/10 text-destructive border-destructive/30 text-[11px] gap-1 py-0.5"
                >
                  <XCircle className="w-3 h-3" />
                  {language === "fr" ? "Expiré" : "منتهي الصلاحية"}
                </Badge>
              ) : (
                <Badge
                  variant="outline"
                  className="bg-amber-500/10 text-amber-600 border-amber-500/30 text-[11px] gap-1 py-0.5"
                >
                  <AlertTriangle className="w-3 h-3" />
                  {language === "fr" ? "À vérifier" : "تنبيه"}
                </Badge>
              )}
            </div>
            <div className="flex items-center gap-2 text-xs text-muted-foreground mt-0.5">
              <span>{file.name}</span>
              <span>•</span>
              <span className="inline-flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-primary" />
                {confidencePct}% {language === "fr" ? "confiance" : "دقة"}
              </span>
            </div>
          </div>
        </div>

        <Button
          type="button"
          variant="ghost"
          size="icon"
          className="h-8 w-8 rounded-lg text-muted-foreground hover:text-foreground shrink-0"
          onClick={onDismiss}
          title={language === "fr" ? "Fermer" : "إغلاق"}
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* ── Warnings / Anomalies Alert ───────────────────────────────────── */}
      {metadata.warnings && metadata.warnings.length > 0 && (
        <div className="mt-3 rounded-xl bg-amber-500/10 border border-amber-500/25 p-2.5 text-xs text-amber-800 dark:text-amber-300 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            {metadata.warnings.map((w, idx) => (
              <p key={idx} className="leading-snug">{w}</p>
            ))}
          </div>
        </div>
      )}

      {/* ── Extracted Editable Fields Grid ───────────────────────────────── */}
      <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2.5 text-xs">
        {/* CIN Number */}
        <div className="rounded-xl border border-border/60 bg-muted/30 p-2.5 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <CreditCard className="w-4 h-4 text-muted-foreground shrink-0" />
            <div className="flex-1 min-w-0">
              <span className="text-[10px] text-muted-foreground block font-medium">
                {language === "fr" ? "Numéro CIN" : "رقم البطاقة الوطنية"}
              </span>
              {editingField === "cin" ? (
                <Input
                  value={cinNumber}
                  onChange={(e) => setCinNumber(e.target.value)}
                  className="h-7 text-xs px-2 py-0 mt-1"
                  autoFocus
                />
              ) : (
                <span className="font-semibold text-foreground truncate block">
                  {cinNumber || "—"}
                </span>
              )}
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-6 w-6 rounded-md text-muted-foreground hover:text-primary shrink-0"
            onClick={() => setEditingField(editingField === "cin" ? null : "cin")}
          >
            {editingField === "cin" ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Pencil className="w-3.5 h-3.5" />}
          </Button>
        </div>

        {/* Full Name */}
        <div className="rounded-xl border border-border/60 bg-muted/30 p-2.5 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <User className="w-4 h-4 text-muted-foreground shrink-0" />
            <div className="flex-1 min-w-0">
              <span className="text-[10px] text-muted-foreground block font-medium">
                {language === "fr" ? "Nom & Prénom" : "الاسم الكامل"}
              </span>
              {editingField === "name" ? (
                <div className="flex gap-1.5 mt-1">
                  <Input
                    value={firstName}
                    placeholder={language === "fr" ? "Prénom" : "الاسم الشخصي"}
                    onChange={(e) => setFirstName(e.target.value)}
                    className="h-7 text-xs px-2 py-0"
                  />
                  <Input
                    value={lastName}
                    placeholder={language === "fr" ? "Nom" : "الاسم العائلي"}
                    onChange={(e) => setLastName(e.target.value)}
                    className="h-7 text-xs px-2 py-0"
                  />
                </div>
              ) : (
                <span className="font-semibold text-foreground truncate block">
                  {`${firstName} ${lastName}`.trim() || metadata.full_name || "—"}
                </span>
              )}
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-6 w-6 rounded-md text-muted-foreground hover:text-primary shrink-0"
            onClick={() => setEditingField(editingField === "name" ? null : "name")}
          >
            {editingField === "name" ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Pencil className="w-3.5 h-3.5" />}
          </Button>
        </div>

        {/* Date of Birth */}
        <div className="rounded-xl border border-border/60 bg-muted/30 p-2.5 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <Calendar className="w-4 h-4 text-muted-foreground shrink-0" />
            <div className="flex-1 min-w-0">
              <span className="text-[10px] text-muted-foreground block font-medium">
                {language === "fr" ? "Date de naissance" : "تاريخ الازدياد"}
              </span>
              {editingField === "birth" ? (
                <Input
                  value={birthDate}
                  onChange={(e) => setBirthDate(e.target.value)}
                  className="h-7 text-xs px-2 py-0 mt-1"
                  autoFocus
                />
              ) : (
                <span className="font-medium text-foreground truncate block">
                  {birthDate || "—"}
                </span>
              )}
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-6 w-6 rounded-md text-muted-foreground hover:text-primary shrink-0"
            onClick={() => setEditingField(editingField === "birth" ? null : "birth")}
          >
            {editingField === "birth" ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Pencil className="w-3.5 h-3.5" />}
          </Button>
        </div>

        {/* Address */}
        <div className="rounded-xl border border-border/60 bg-muted/30 p-2.5 flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <MapPin className="w-4 h-4 text-muted-foreground shrink-0" />
            <div className="flex-1 min-w-0">
              <span className="text-[10px] text-muted-foreground block font-medium">
                {language === "fr" ? "Adresse" : "العنوان"}
              </span>
              {editingField === "address" ? (
                <Input
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  className="h-7 text-xs px-2 py-0 mt-1"
                  autoFocus
                />
              ) : (
                <span className="font-medium text-foreground truncate block">
                  {address || "—"}
                </span>
              )}
            </div>
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="h-6 w-6 rounded-md text-muted-foreground hover:text-primary shrink-0"
            onClick={() => setEditingField(editingField === "address" ? null : "address")}
          >
            {editingField === "address" ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Pencil className="w-3.5 h-3.5" />}
          </Button>
        </div>
      </div>

      {/* ── Action Buttons: Pre-fill Request + Send to Chat ──────────────── */}
      <div className="mt-3.5 flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-border/40">
        <div>
          {!cinNumber && !firstName && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={loadDemoProfile}
              className="text-xs text-primary hover:bg-primary/10 gap-1.5 h-8 px-2.5 font-medium"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              {language === "fr" ? "Charger profil démo (Ahmed Benali)" : "ملء بملف تجريبي (أحمد بنعلي)"}
            </Button>
          )}
        </div>

        <div className="flex items-center gap-2">
          {onSendToChat && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onSendToChat()}
              className="rounded-xl text-xs gap-1.5 h-9"
            >
              <Send className="w-3.5 h-3.5" />
              {language === "fr" ? "Discuter de cette pièce" : "إرسال إلى المحادثة"}
            </Button>
          )}

          <Button
            type="button"
            size="sm"
            onClick={handlePreFill}
            className="rounded-xl text-xs gap-1.5 h-9 bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm font-medium"
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-300 animate-pulse" />
            {language === "fr" ? "Pré-remplir ma démarche" : "ملء الإجراء تلقائياً"}
          </Button>
        </div>
      </div>
    </div>
  );
}

/** Loading skeleton shown while AI is running OCR and anomaly detection */
export function DocumentScanningSkeleton({
  filename,
  isRtl = false,
  language = "darija",
}: {
  filename: string;
  isRtl?: boolean;
  language?: string;
}) {
  return (
    <div
      className="rounded-2xl border border-primary/30 bg-primary/5 p-4 shadow-sm relative overflow-hidden"
      dir={isRtl ? "rtl" : "ltr"}
    >
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-primary/20 text-primary flex items-center justify-center animate-pulse shrink-0">
          <Sparkles className="w-5 h-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-foreground">
              {language === "fr"
                ? "Analyse intelligente du document..."
                : "جاري الفحص الذكي للوثيقة..."}
            </span>
          </div>
          <p className="text-[11px] text-muted-foreground truncate mt-0.5">
            {filename} · {language === "fr" ? "OCR + Détection d'anomalies en cours" : "استخراج البيانات والتحقق من الصلاحية"}
          </p>
        </div>
      </div>

      {/* Animated glowing scanning bar */}
      <div className="mt-3 h-1.5 w-full bg-primary/10 rounded-full overflow-hidden">
        <div className="h-full bg-primary rounded-full animate-[progress_1.5s_ease-in-out_infinite] w-2/3" />
      </div>
    </div>
  );
}
