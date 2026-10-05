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
import { LogOut, IdCard, FileText, Upload, Loader2, CheckCircle2, Eye, Download, Trash2, Sun, Moon, Monitor } from "lucide-react";
import { useTheme } from "next-themes";
import { fetchMe, updateMe, logout, isAuthenticated, type PersonalDocument } from "@/lib/auth";
import { fetchCinPreview, fetchPersonalDocPreview, uploadProfileCin, uploadPersonalDocument, validateFile, CIN_UPLOAD_TYPES, deletePersonalDocument } from "@/lib/documents";
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
  const { t, language, setLanguage, isRtl } = useI18n();
  const { theme, setTheme } = useTheme();
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
  const [personalPreviewDoc, setPersonalPreviewDoc] = useState<{ name: string; url: string; mimeType: string } | null>(null);
  const [viewingPersonalDocId, setViewingPersonalDocId] = useState<string | null>(null);
  const [docToDelete, setDocToDelete] = useState<PersonalDocument | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
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

  const handleViewPersonalDoc = async (doc: PersonalDocument) => {
    setViewingPersonalDocId(doc.id);
    try {
      const blob = await fetchPersonalDocPreview(doc.id);
      if (personalPreviewDoc?.url) URL.revokeObjectURL(personalPreviewDoc.url);
      const url = URL.createObjectURL(blob);
      setPersonalPreviewDoc({ name: doc.name, url, mimeType: blob.type || doc.mimeType || "application/pdf" });
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Impossible d'afficher le document" : "تعذر عرض الوثيقة",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setViewingPersonalDocId(null);
    }
  };

  const handleDownloadPersonalDoc = async (doc: PersonalDocument) => {
    try {
      const blob = await fetchPersonalDocPreview(doc.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = doc.name;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Échec du téléchargement" : "فشل التحميل",
        description: err instanceof Error ? err.message : undefined,
      });
    }
  };

  const confirmDeletePersonalDoc = async () => {
    if (!docToDelete) return;
    setIsDeleting(true);
    try {
      const updatedUser = await deletePersonalDocument(docToDelete.id);
      setPersonalDocuments(updatedUser.personalDocuments ?? []);
      toast({
        title: language === "fr" ? "Document supprimé" : "تم حذف الوثيقة بنجاح",
        description: docToDelete.name,
      });
      setDocToDelete(null);
    } catch (err) {
      toast({
        variant: "destructive",
        title: language === "fr" ? "Échec de suppression" : "فشل الحذف",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setIsDeleting(false);
    }
  };

  useEffect(() => {
    return () => {
      if (cinPreviewUrl) URL.revokeObjectURL(cinPreviewUrl);
      if (personalPreviewDoc?.url) URL.revokeObjectURL(personalPreviewDoc.url);
    };
  }, [cinPreviewUrl, personalPreviewDoc]);

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
      <div className="max-w-3xl mx-auto space-y-6 sm:space-y-8">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">{t("profile.title")}</h1>
          {isAuthenticated() && (
            <Button variant="outline" onClick={handleLogout} className="gap-2 w-full sm:w-auto">
              <LogOut className="w-4 h-4" />
              {language === "fr" ? "Déconnexion" : "تسجيل الخروج"}
            </Button>
          )}
        </div>

        <div className="grid gap-4 sm:gap-6">
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
              <div className="flex flex-col sm:flex-row sm:items-center gap-3 sm:gap-4 p-3.5 sm:p-4 rounded-lg border bg-card">
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <IdCard className="w-7 h-7 sm:w-8 sm:h-8 text-primary shrink-0" />
                  <div className="min-w-0 flex-1">
                    <div className="text-sm font-semibold">
                      {language === "fr" ? "Carte d'Identité Nationale (CIN)" : "البطاقة الوطنية للتعريف"}
                    </div>
                    {cinFileName ? (
                      <div className="flex items-center gap-1.5 text-xs text-muted-foreground mt-0.5">
                        <CheckCircle2 className="w-3.5 h-3.5 text-green-600 shrink-0" />
                        <span className="truncate" title={cinFileName}>{cinFileName}</span>
                      </div>
                    ) : (
                      <div className="text-xs text-muted-foreground mt-0.5">
                        {language === "fr" ? "Aucun fichier importé (PNG ou PDF)" : "لم يتم استيراد أي ملف (PNG أو PDF)"}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0 pt-2 sm:pt-0 border-t border-border/50 sm:border-t-0">
                  {cinFileName && (
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 flex-1 sm:flex-none"
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
                    className="gap-1.5 flex-1 sm:flex-none"
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
                    <div key={doc.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 sm:gap-3 p-3 rounded-lg border bg-card hover:bg-muted/20 transition-colors">
                      <div className="flex items-start sm:items-center gap-3 min-w-0 flex-1">
                        <FileText className="w-5 h-5 text-primary shrink-0 mt-0.5 sm:mt-0" />
                        <div className="min-w-0 flex-1">
                          <div className="text-sm font-medium truncate" title={doc.name}>{doc.name}</div>
                          <div className="text-xs text-muted-foreground">
                            {formatSize(doc.size)} · {new Date(doc.uploadedAt).toLocaleDateString()}
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center justify-between sm:justify-end gap-1.5 shrink-0 pt-2 sm:pt-0 border-t border-border/50 sm:border-t-0">
                        <Badge variant="outline" className="border-amber-300 bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300 shrink-0">
                          {language === "fr" ? "Importé" : "مستورد"}
                        </Badge>

                        {/* View Button */}
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 text-primary hover:bg-primary/10"
                          title={language === "fr" ? "Consulter" : "معاينة"}
                          disabled={viewingPersonalDocId === doc.id}
                          onClick={() => handleViewPersonalDoc(doc)}
                        >
                          {viewingPersonalDocId === doc.id ? (
                            <Loader2 className="w-4 h-4 animate-spin text-primary" />
                          ) : (
                            <Eye className="w-4 h-4" />
                          )}
                        </Button>

                        {/* Download Button */}
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 text-muted-foreground hover:text-foreground"
                          title={language === "fr" ? "Télécharger" : "تحميل"}
                          onClick={() => handleDownloadPersonalDoc(doc)}
                        >
                          <Download className="w-4 h-4" />
                        </Button>

                        {/* Delete Button */}
                        <Button
                          size="icon"
                          variant="ghost"
                          className="h-8 w-8 text-red-500 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950/40"
                          title={language === "fr" ? "Supprimer" : "حذف الوثيقة"}
                          onClick={() => setDocToDelete(doc)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
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
              <CardTitle>{language === "fr" ? "Apparence et Thème" : "المظهر والسمة"}</CardTitle>
              <CardDescription>
                {language === "fr"
                  ? "Choisissez entre le mode clair, le mode sombre (nuit) ou l'adaptation automatique au système."
                  : "اختر بين الوضع النهاري، الوضع الليلي، أو التوافق التلقائي مع نظام جهازك."}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup value={theme ?? "system"} onValueChange={(v) => setTheme(v)}>
                <div className="flex items-center space-x-2 space-x-reverse mb-3">
                  <RadioGroupItem value="light" id="theme-light" />
                  <Label htmlFor="theme-light" className="flex items-center gap-2 cursor-pointer">
                    <Sun className="w-4 h-4 text-amber-500" />
                    <span>{language === "fr" ? "Mode clair (Jour)" : "الوضع النهاري"}</span>
                  </Label>
                </div>
                <div className="flex items-center space-x-2 space-x-reverse mb-3">
                  <RadioGroupItem value="dark" id="theme-dark" />
                  <Label htmlFor="theme-dark" className="flex items-center gap-2 cursor-pointer">
                    <Moon className="w-4 h-4 text-sky-400" />
                    <span>{language === "fr" ? "Mode sombre (Nuit)" : "الوضع الليلي"}</span>
                  </Label>
                </div>
                <div className="flex items-center space-x-2 space-x-reverse">
                  <RadioGroupItem value="system" id="theme-system" />
                  <Label htmlFor="theme-system" className="flex items-center gap-2 cursor-pointer">
                    <Monitor className="w-4 h-4 text-muted-foreground" />
                    <span>{language === "fr" ? "Automatique (Système)" : "تلقائي (حسب النظام)"}</span>
                  </Label>
                </div>
              </RadioGroup>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>{language === "fr" ? "Notifications" : "الإشعارات"}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
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
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 sm:pt-0 border-t border-border/50 sm:border-t-0">
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
        <DialogContent className="w-[calc(100vw-1.5rem)] sm:max-w-4xl h-[85vh] flex flex-col p-3 sm:p-6" dir={isRtl ? "rtl" : "ltr"}>
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

      {/* Personal Document Viewer Modal */}
      <Dialog
        open={Boolean(personalPreviewDoc)}
        onOpenChange={(open) => {
          if (!open && personalPreviewDoc) {
            URL.revokeObjectURL(personalPreviewDoc.url);
            setPersonalPreviewDoc(null);
          }
        }}
      >
        <DialogContent className="w-[calc(100vw-1.5rem)] sm:max-w-4xl h-[85vh] flex flex-col p-3 sm:p-6" dir={isRtl ? "rtl" : "ltr"}>
          <DialogHeader className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 pb-3 border-b">
            <div className="text-start min-w-0 flex-1">
              <DialogTitle className="text-base sm:text-lg font-bold truncate max-w-full sm:max-w-[500px]">
                {personalPreviewDoc?.name}
              </DialogTitle>
              <DialogDescription className="text-xs text-muted-foreground mt-0.5">
                {language === "fr" ? "Aperçu du document personnel" : "معاينة الوثيقة الشخصية"}
              </DialogDescription>
            </div>
            {personalPreviewDoc && (
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5 shrink-0 w-full sm:w-auto justify-center"
                onClick={() => {
                  const a = document.createElement("a");
                  a.href = personalPreviewDoc.url;
                  a.download = personalPreviewDoc.name;
                  document.body.appendChild(a);
                  a.click();
                  document.body.removeChild(a);
                }}
              >
                <Download className="w-3.5 h-3.5" />
                <span>{language === "fr" ? "Télécharger" : "تحميل"}</span>
              </Button>
            )}
          </DialogHeader>
          <div className="flex-1 min-h-0 overflow-auto rounded-xl border bg-muted/30 flex items-center justify-center p-2">
            {personalPreviewDoc?.mimeType === "application/pdf" || personalPreviewDoc?.name.toLowerCase().endsWith(".pdf") ? (
              <iframe
                src={personalPreviewDoc.url}
                title={personalPreviewDoc.name}
                className="w-full h-full min-h-[60vh] rounded-lg"
              />
            ) : personalPreviewDoc ? (
              <img
                src={personalPreviewDoc.url}
                alt={personalPreviewDoc.name}
                className="max-w-full max-h-full object-contain rounded-lg shadow-sm"
              />
            ) : null}
          </div>
        </DialogContent>
      </Dialog>

      {/* Professional Delete Confirmation Modal */}
      <Dialog
        open={Boolean(docToDelete)}
        onOpenChange={(open) => {
          if (!open && !isDeleting) setDocToDelete(null);
        }}
      >
        <DialogContent className="w-[calc(100vw-1.5rem)] max-w-md p-4 sm:p-7 rounded-2xl shadow-2xl" dir={isRtl ? "rtl" : "ltr"}>
          <div className="flex flex-col items-center text-center space-y-4 pt-2">
            <div className="w-14 h-14 rounded-full bg-red-100 dark:bg-red-950/60 flex items-center justify-center text-red-600 ring-8 ring-red-50 dark:ring-red-950/30">
              <Trash2 className="w-7 h-7" />
            </div>
            <div className="space-y-2">
              <DialogTitle className="text-xl font-bold">
                {language === "fr" ? "Supprimer le document ?" : "تأكيد حذف الوثيقة"}
              </DialogTitle>
              <DialogDescription className="text-sm text-muted-foreground leading-relaxed px-2">
                {language === "fr" ? (
                  <>
                    Êtes-vous sûr de vouloir supprimer définitivement <span className="font-semibold text-foreground font-mono text-xs px-1.5 py-0.5 rounded bg-muted">"{docToDelete?.name}"</span> ? Cette action ne peut pas être annulée.
                  </>
                ) : (
                  <>
                    هل أنت متأكد من رغبتك في حذف الوثيقة <span className="font-semibold text-foreground font-mono text-xs px-1.5 py-0.5 rounded bg-muted">"{docToDelete?.name}"</span> نهائياً؟ لن تتمكن من استرجاع هذا الملف.
                  </>
                )}
              </DialogDescription>
            </div>
          </div>
          <div className="flex items-center justify-center gap-3 pt-5 border-t mt-4">
            <Button
              variant="outline"
              className="flex-1 h-10 font-medium"
              disabled={isDeleting}
              onClick={() => setDocToDelete(null)}
            >
              {language === "fr" ? "Annuler" : "تراجع"}
            </Button>
            <Button
              variant="destructive"
              className="flex-1 h-10 gap-2 bg-red-600 hover:bg-red-700 text-white font-medium"
              disabled={isDeleting}
              onClick={confirmDeletePersonalDoc}
            >
              {isDeleting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
              <span>{language === "fr" ? "Supprimer" : "تأكيد الحذف"}</span>
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </AppLayout>
  );
}
