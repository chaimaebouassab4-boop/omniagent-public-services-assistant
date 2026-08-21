import { useEffect, useRef, useState } from "react";
import { useLocation } from "wouter";
import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { LogOut, IdCard, FileText, Upload, Loader2, CheckCircle2, Eye } from "lucide-react";
import { fetchMe, updateMe, logout, isAuthenticated, type PersonalDocument } from "@/lib/auth";
import { fetchCinPreview, uploadProfileCin, uploadPersonalDocument, validateFile, CIN_UPLOAD_TYPES } from "@/lib/documents";
import { useToast } from "@/hooks/use-toast";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

export default function Profile() {
  const { t, language, setLanguage } = useI18n();
  const [_, setLocation] = useLocation();
  const { toast } = useToast();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [notifyEmail, setNotifyEmail] = useState(true);
  const [notifySms, setNotifySms] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const [cinFileName, setCinFileName] = useState<string | null>(null);
  const [personalDocuments, setPersonalDocuments] = useState<PersonalDocument[]>([]);
  const [uploadingCin, setUploadingCin] = useState(false);
  const [viewingCin, setViewingCin] = useState(false);
  const [cinPreviewUrl, setCinPreviewUrl] = useState<string | null>(null);
  const [cinPreviewType, setCinPreviewType] = useState("");
  const [uploadingDoc, setUploadingDoc] = useState(false);
  const cinInputRef = useRef<HTMLInputElement>(null);
  const docInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchMe()
      .then((user) => {
        setFullName(user.fullName ?? "");
        setEmail(user.email ?? "");
        setPhone(user.phone ?? "");
        setNotifyEmail(user.notifyEmail ?? true);
        setNotifySms(user.notifySms ?? false);
        setCinFileName(user.cinFileName ?? null);
        setPersonalDocuments(user.personalDocuments ?? []);
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, []);

  const rejectionToast = (reason: string) => {
    toast({
      variant: "destructive",
      title: language === "fr" ? "Fichier refusé" : "الملف مرفوض",
      description:
        reason === "too_large"
          ? (language === "fr" ? "Taille maximale : 10 MB." : "الحجم الأقصى: 10 ميغابايت.")
          : (language === "fr" ? "Format non accepté." : "صيغة غير مقبولة."),
    });
  };

  const handleCinSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    const reason = validateFile(file, CIN_UPLOAD_TYPES);
    if (reason) return rejectionToast(reason);

    setUploadingCin(true);
    try {
      const user = await uploadProfileCin(file);
      setCinFileName(user.cinFileName ?? file.name);
      toast({
        title: language === "fr" ? "CIN enregistrée" : "تم حفظ البطاقة الوطنية",
        description: file.name,
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Échec de l'envoi" : "فشل الإرسال",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setUploadingCin(false);
    }
  };

  const handleDocSelected = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file) return;
    const reason = validateFile(file);
    if (reason) return rejectionToast(reason);

    setUploadingDoc(true);
    try {
      const user = await uploadPersonalDocument(file);
      setPersonalDocuments(user.personalDocuments ?? []);
      toast({
        title: language === "fr" ? "Document ajouté" : "تمت إضافة الوثيقة",
        description: file.name,
      });
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Échec de l'envoi" : "فشل الإرسال",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setUploadingDoc(false);
    }
  };

  const handleViewCin = async () => {
    setViewingCin(true);
    try {
      const blob = await fetchCinPreview();
      if (cinPreviewUrl) URL.revokeObjectURL(cinPreviewUrl);
      setCinPreviewType(blob.type);
      setCinPreviewUrl(URL.createObjectURL(blob));
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Impossible d'afficher la CIN" : "تعذر عرض البطاقة الوطنية",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setViewingCin(false);
    }
  };

  useEffect(() => {
    return () => {
      if (cinPreviewUrl) URL.revokeObjectURL(cinPreviewUrl);
    };
  }, [cinPreviewUrl]);

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    try {
      await updateMe({ fullName, phone });
      setSaved(true);
    } finally {
      setSaving(false);
    }
  };

  const handleLogout = () => {
    logout();
    setLocation("/login");
  };

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-foreground">{t("profile.title")}</h1>
          {isAuthenticated() && (
            <Button variant="outline" onClick={handleLogout} className="gap-2">
              <LogOut className="w-4 h-4" />
              {language === "fr" ? "Déconnexion" : "تسجيل الخروج"}
            </Button>
          )}
        </div>

        <div className="grid gap-6">
          <Card>
            <CardHeader>
              <CardTitle>{language === "fr" ? "Informations Personnelles" : "المعلومات الشخصية"}</CardTitle>
              <CardDescription>{language === "fr" ? "Mettez à jour vos informations" : "تحديث معلوماتك"}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-2">
                <Label htmlFor="name">{language === "fr" ? "Nom complet" : "الاسم الكامل"}</Label>
                <Input id="name" value={fullName} onChange={(e) => setFullName(e.target.value)} disabled={loading} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="email">{language === "fr" ? "Email" : "البريد الإلكتروني"}</Label>
                <Input id="email" type="email" value={email} disabled dir="ltr" />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="phone">{language === "fr" ? "Téléphone" : "رقم الهاتف"}</Label>
                <Input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} disabled={loading} dir="ltr" />
              </div>
              <div className="flex items-center gap-3">
                <Button onClick={handleSave} disabled={saving || loading}>
                  {saving ? (language === "fr" ? "Enregistrement..." : "جاري الحفظ...") : t("action.submit")}
                </Button>
                {saved && (
                  <span className="text-sm text-green-600">
                    {language === "fr" ? "Enregistré ✓" : "تم الحفظ ✓"}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{language === "fr" ? "Mes Documents" : "وثائقي"}</CardTitle>
              <CardDescription>
                {language === "fr"
                  ? "Importez votre CIN et vos documents personnels (PDF ou image, 10 MB max)"
                  : "استورد بطاقتك الوطنية ووثائقك الشخصية (PDF أو صورة، 10 ميغابايت كحد أقصى)"}
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Hidden file inputs */}
              <input
                ref={cinInputRef}
                type="file"
                accept=".png,.pdf,image/png,application/pdf"
                className="hidden"
                onChange={handleCinSelected}
                data-testid="input-cin-file"
              />
              <input
                ref={docInputRef}
                type="file"
                accept=".png,.pdf,.jpg,.jpeg,.webp,application/pdf,image/png,image/jpeg,image/webp"
                className="hidden"
                onChange={handleDocSelected}
                data-testid="input-personal-file"
              />

              {/* CIN */}
              <div className="flex items-center gap-4 p-4 rounded-lg border bg-card">
                <IdCard className="w-8 h-8 text-primary shrink-0" />
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-semibold">
                    {language === "fr" ? "Carte d'Identité Nationale (CIN)" : "البطاقة الوطنية للتعريف"}
                  </div>
                  {cinFileName ? (
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5">
                      <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />
                      <span className="truncate" title={cinFileName}>{cinFileName}</span>
                    </div>
                  ) : (
                    <div className="text-xs text-muted-foreground mt-0.5">
                      {language === "fr" ? "Aucun fichier importé (PNG ou PDF)" : "لم يتم استيراد أي ملف (PNG أو PDF)"}
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  {cinFileName && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5"
                      disabled={viewingCin || loading}
                      onClick={handleViewCin}
                      data-testid="button-view-cin"
                    >
                      {viewingCin ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Eye className="w-3.5 h-3.5" />}
                      {language === "fr" ? "Voir" : "عرض"}
                    </Button>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    disabled={uploadingCin || loading}
                    onClick={() => cinInputRef.current?.click()}
                    data-testid="button-upload-cin"
                  >
                    {uploadingCin ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                    {cinFileName
                      ? (language === "fr" ? "Remplacer" : "استبدال")
                      : (language === "fr" ? "Importer" : "استيراد")}
                  </Button>
                </div>
              </div>

              {/* Personal documents */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="text-sm font-semibold">
                    {language === "fr" ? "Autres documents" : "وثائق أخرى"}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-1.5"
                    disabled={uploadingDoc || loading}
                    onClick={() => docInputRef.current?.click()}
                    data-testid="button-upload-personal"
                  >
                    {uploadingDoc ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Upload className="w-3.5 h-3.5" />}
                    {language === "fr" ? "Ajouter" : "إضافة"}
                  </Button>
                </div>
                <div className="space-y-2">
                  {personalDocuments.map((doc) => (
                    <div key={doc.id} className="flex items-center gap-3 p-3 rounded-lg border bg-card">
                      <FileText className="w-5 h-5 text-primary shrink-0" />
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium truncate" title={doc.name}>{doc.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {formatSize(doc.size)} · {new Date(doc.uploadedAt).toLocaleDateString()}
                        </div>
                      </div>
                      <Badge variant="outline" className="border-amber-300 bg-amber-50 text-amber-700 shrink-0">
                        {language === "fr" ? "Importé" : "مستورد"}
                      </Badge>
                    </div>
                  ))}
                  {!personalDocuments.length && (
                    <div className="text-sm text-muted-foreground text-center py-3 border rounded-lg border-dashed">
                      {language === "fr" ? "Aucun document personnel." : "لا توجد وثائق شخصية."}
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{language === "fr" ? "Préférences de Langue" : "تفضيلات اللغة"}</CardTitle>
            </CardHeader>
            <CardContent>
              <RadioGroup value={language} onValueChange={(v) => setLanguage(v as any)}>
                <div className="flex items-center space-x-2 space-x-reverse mb-3">
                  <RadioGroupItem value="darija" id="l-darija" />
                  <Label htmlFor="l-darija">الدارجة المغربية</Label>
                </div>
                <div className="flex items-center space-x-2 space-x-reverse mb-3">
                  <RadioGroupItem value="ar" id="l-ar" />
                  <Label htmlFor="l-ar">العربية الفصحى</Label>
                </div>
                <div className="flex items-center space-x-2 space-x-reverse">
                  <RadioGroupItem value="fr" id="l-fr" />
                  <Label htmlFor="l-fr">Français</Label>
                </div>
              </RadioGroup>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{language === "fr" ? "Notifications" : "الإشعارات"}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <Label htmlFor="notif-email" className="flex flex-col gap-1">
                  <span>{language === "fr" ? "Notifications par Email" : "إشعارات البريد الإلكتروني"}</span>
                  <span className="font-normal text-sm text-muted-foreground">
                    {language === "fr" ? "Recevoir des mises à jour sur vos dossiers" : "تلقي تحديثات حول قضاياك"}
                  </span>
                </Label>
                <Switch
                  id="notif-email"
                  checked={notifyEmail}
                  onCheckedChange={async (checked) => {
                    setNotifyEmail(checked);
                    try {
                      await updateMe({ notifyEmail: checked });
                      toast({
                        title: language === "fr" ? "Préférence enregistrée" : "تم حفظ التفضيل",
                        description: checked
                          ? (language === "fr" ? "Notifications email activées" : "إشعارات البريد مفعلة")
                          : (language === "fr" ? "Notifications email désactivées" : "إشعارات البريد معطلة"),
                      });
                    } catch {
                      setNotifyEmail(!checked);
                    }
                  }}
                />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="notif-sms" className="flex flex-col gap-1">
                  <span>{language === "fr" ? "Notifications par SMS" : "إشعارات SMS"}</span>
                  <span className="font-normal text-sm text-muted-foreground">
                    {language === "fr" ? "Recevoir des alertes sur votre téléphone" : "تلقي تنبيهات على هاتفك"}
                  </span>
                </Label>
                <Switch
                  id="notif-sms"
                  checked={notifySms}
                  onCheckedChange={async (checked) => {
                    setNotifySms(checked);
                    try {
                      await updateMe({ notifySms: checked });
                      toast({
                        title: language === "fr" ? "Préférence enregistrée" : "تم حفظ التفضيل",
                        description: checked
                          ? (language === "fr" ? "Notifications SMS activées" : "إشعارات SMS مفعلة")
                          : (language === "fr" ? "Notifications SMS désactivées" : "إشعارات SMS معطلة"),
                      });
                    } catch {
                      setNotifySms(!checked);
                    }
                  }}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
      <Dialog
        open={Boolean(cinPreviewUrl)}
        onOpenChange={(open) => {
          if (!open && cinPreviewUrl) {
            URL.revokeObjectURL(cinPreviewUrl);
            setCinPreviewUrl(null);
          }
        }}
      >
        <DialogContent className="max-w-4xl h-[85vh] flex flex-col">
          <DialogHeader>
            <DialogTitle>
              {language === "fr" ? "Carte d'Identité Nationale (CIN)" : "البطاقة الوطنية للتعريف"}
            </DialogTitle>
            <DialogDescription>{cinFileName}</DialogDescription>
          </DialogHeader>
          <div className="flex-1 min-h-0 overflow-auto rounded-lg border bg-muted/20">
            {cinPreviewUrl && cinPreviewType === "application/pdf" ? (
              <iframe
                src={cinPreviewUrl}
                title={cinFileName ?? "CIN"}
                className="w-full h-full min-h-[60vh]"
              />
            ) : cinPreviewUrl ? (
              <img
                src={cinPreviewUrl}
                alt={language === "fr" ? "Aperçu de la CIN" : "معاينة البطاقة الوطنية"}
                className="w-full h-full object-contain"
              />
            ) : null}
          </div>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
