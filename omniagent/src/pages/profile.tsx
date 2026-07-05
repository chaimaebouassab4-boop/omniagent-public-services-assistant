import { useEffect, useState } from "react";
import { useLocation } from "wouter";
import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { LogOut } from "lucide-react";
import { fetchMe, updateMe, logout, isAuthenticated } from "@/lib/auth";

export default function Profile() {
  const { t, language, setLanguage } = useI18n();
  const [_, setLocation] = useLocation();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    fetchMe()
      .then((user) => {
        setFullName(user.fullName ?? "");
        setEmail(user.email ?? "");
        setPhone(user.phone ?? "");
      })
      .catch(() => undefined)
      .finally(() => setLoading(false));
  }, []);

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
                <Switch id="notif-email" defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <Label htmlFor="notif-sms" className="flex flex-col gap-1">
                  <span>{language === "fr" ? "Notifications par SMS" : "إشعارات SMS"}</span>
                  <span className="font-normal text-sm text-muted-foreground">
                    {language === "fr" ? "Recevoir des alertes sur votre téléphone" : "تلقي تنبيهات على هاتفك"}
                  </span>
                </Label>
                <Switch id="notif-sms" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AppLayout>
  );
}
