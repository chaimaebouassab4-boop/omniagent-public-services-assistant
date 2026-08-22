import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { useGetAdminStats, useAdminListCases, useUpdateCase, getAdminListCasesQueryKey, getGetAdminStatsQueryKey } from "@workspace/api-client-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusBadge } from "./dashboard";
import { Button } from "@/components/ui/button";
import { Link } from "wouter";
import { Check, X, Users, Eye, Monitor, Smartphone, Tablet, MapPin, TrendingUp, Globe, Clock, RotateCcw } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, CartesianGrid } from "recharts";
import { useState } from "react";
import { getVisitors } from "@/lib/history";

const COLORS = ['hsl(var(--primary))', 'hsl(var(--secondary))', '#eab308', '#22c55e', '#ef4444'];

function VisitorStats() {
  const { language, isRtl } = useI18n();
  const { data: visitors = [] } = useQuery({
    queryKey: ["admin", "visit-analytics"],
    queryFn: getVisitors,
    refetchInterval: 30_000,
  });
  const [activeTab, setActiveTab] = useState<"overview" | "live" | "pages" | "geo">("overview");

  const now = Date.now();
  const last24h = visitors.filter((v) => now - v.timestamp < 86400000);
  const last7d = visitors.filter((v) => now - v.timestamp < 7 * 86400000);
  const liveNow = visitors.filter((v) => now - v.timestamp < 300000).length;

  const pageCounts: Record<string, number> = {};
  last7d.forEach((v) => { pageCounts[v.pageLabel] = (pageCounts[v.pageLabel] || 0) + 1; });
  const pageData = Object.entries(pageCounts)
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count);

  const cityCounts: Record<string, number> = {};
  last7d.forEach((v) => { cityCounts[v.city] = (cityCounts[v.city] || 0) + 1; });
  const cityData = Object.entries(cityCounts)
    .map(([city, count]) => ({ city, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);

  const deviceCounts = { Mobile: 0, Desktop: 0, Tablette: 0 };
  last7d.forEach((v) => { deviceCounts[v.device as keyof typeof deviceCounts] = (deviceCounts[v.device as keyof typeof deviceCounts] || 0) + 1; });

  const langCounts: Record<string, number> = {};
  last7d.forEach((v) => { langCounts[v.lang] = (langCounts[v.lang] || 0) + 1; });
  const langData = Object.entries(langCounts).map(([lang, count]) => ({ lang: lang.toUpperCase(), count }));

  const hourBuckets = Array.from({ length: 24 }, (_, h) => ({
    h: `${h}h`,
    visits: last7d.filter((v) => new Date(v.timestamp).getHours() === h).length,
  }));

  const recentVisitors = visitors.slice(0, 10);

  return (
    <div className="space-y-6">
      {/* KPI bar */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Eye, value: last24h.length, labelFr: "Vues (24h)", labelAr: "مشاهدات (24 ساعة)", color: "text-primary", bg: "bg-primary/10" },
          { icon: Users, value: last7d.length, labelFr: "Visites (7j)", labelAr: "زيارات (7 أيام)", color: "text-secondary", bg: "bg-secondary/10" },
          { icon: TrendingUp, value: `${liveNow}`, labelFr: "En ligne maintenant", labelAr: "متصل الآن", color: "text-green-600", bg: "bg-green-100 dark:bg-green-900/30" },
          { icon: Globe, value: Object.keys(cityCounts).length, labelFr: "Villes actives", labelAr: "مدن نشطة", color: "text-amber-600", bg: "bg-amber-100 dark:bg-amber-900/30" },
        ].map((kpi) => (
          <Card key={kpi.labelFr} className={`border-0 shadow-sm`}>
            <CardContent className="pt-5 pb-4">
              <div className={`flex items-start gap-3 ${isRtl ? "flex-row-reverse" : ""}`}>
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${kpi.bg}`}>
                  <kpi.icon className={`w-5 h-5 ${kpi.color}`} />
                </div>
                <div className={isRtl ? "text-right" : ""}>
                  <div className="text-2xl font-bold text-foreground">{kpi.value}</div>
                  <div className="text-xs text-muted-foreground mt-0.5">
                    {language === "fr" ? kpi.labelFr : kpi.labelAr}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Sub-tabs */}
      <div className="flex gap-1 p-1 bg-muted rounded-lg w-fit">
        {(["overview", "live", "pages", "geo"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab === "overview" ? (language === "fr" ? "Aperçu" : "نظرة عامة")
              : tab === "live" ? (language === "fr" ? "En direct" : "مباشر")
              : tab === "pages" ? (language === "fr" ? "Pages" : "الصفحات")
              : (language === "fr" ? "Géographie" : "الجغرافيا")}
          </button>
        ))}
      </div>

      {activeTab === "overview" && (
        <div className="grid md:grid-cols-2 gap-6">
          <Card>
            <CardHeader><CardTitle className="text-base">{language === "fr" ? "Visites par heure (7j)" : "الزيارات حسب الساعة (7 أيام)"}</CardTitle></CardHeader>
            <CardContent className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={hourBuckets}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="h" tick={{ fontSize: 10 }} interval={3} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="visits" stroke="hsl(var(--primary))" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          <Card>
            <CardHeader><CardTitle className="text-base">{language === "fr" ? "Langues utilisées" : "اللغات المستخدمة"}</CardTitle></CardHeader>
            <CardContent className="h-52">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={langData} dataKey="count" nameKey="lang" cx="50%" cy="50%" outerRadius={70} label={({ lang, percent }) => `${lang} ${(percent * 100).toFixed(0)}%`}>
                    {langData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
          {/* Devices */}
          <Card className="md:col-span-2">
            <CardHeader><CardTitle className="text-base">{language === "fr" ? "Appareils" : "الأجهزة"}</CardTitle></CardHeader>
            <CardContent>
              <div className="flex gap-6 flex-wrap">
                {([["Mobile", Smartphone, "text-primary bg-primary/10"], ["Desktop", Monitor, "text-secondary bg-secondary/10"], ["Tablette", Tablet, "text-amber-600 bg-amber-100 dark:bg-amber-900/30"]] as const).map(([dev, Icon, cls]) => {
                  const count = deviceCounts[dev as keyof typeof deviceCounts] || 0;
                  const pct = last7d.length ? Math.round((count / last7d.length) * 100) : 0;
                  return (
                    <div key={dev} className={`flex items-center gap-3 ${isRtl ? "flex-row-reverse" : ""}`}>
                      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${cls.split(" ").slice(1).join(" ")}`}>
                        <Icon className={`w-5 h-5 ${cls.split(" ")[0]}`} />
                      </div>
                      <div className={isRtl ? "text-right" : ""}>
                        <p className="text-sm font-semibold text-foreground">{count} ({pct}%)</p>
                        <p className="text-xs text-muted-foreground">{dev}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === "live" && (
        <Card>
          <CardHeader><CardTitle className="text-base flex items-center gap-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
            {language === "fr" ? "Visites récentes (temps réel)" : "الزيارات الأخيرة (الوقت الفعلي)"}
          </CardTitle></CardHeader>
          <CardContent>
            <div className="divide-y divide-border">
              {recentVisitors.map((v) => {
                const ago = Math.floor((now - v.timestamp) / 60000);
                return (
                  <div key={v.id} className={`flex items-center gap-4 py-3 ${isRtl ? "flex-row-reverse" : ""}`}>
                    <div className="w-8 h-8 bg-muted rounded-full flex items-center justify-center shrink-0">
                      {v.device === "Mobile" ? <Smartphone className="w-4 h-4 text-muted-foreground" /> : v.device === "Desktop" ? <Monitor className="w-4 h-4 text-muted-foreground" /> : <Tablet className="w-4 h-4 text-muted-foreground" />}
                    </div>
                    <div className={`flex-1 min-w-0 ${isRtl ? "text-right" : ""}`}>
                      <p className="text-sm font-medium text-foreground">{v.pageLabel}</p>
                      <p className="text-xs text-muted-foreground">{v.city} · {v.lang.toUpperCase()}</p>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground shrink-0">
                      <Clock className="w-3 h-3" />
                      <span>{ago < 1 ? (language === "fr" ? "Maintenant" : "الآن") : `${ago} min`}</span>
                    </div>
                  </div>
                );
              })}
              {recentVisitors.length === 0 && (
                <p className="text-center py-8 text-muted-foreground text-sm">
                  {language === "fr" ? "Aucune visite récente." : "لا توجد زيارات حديثة."}
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === "pages" && (
        <Card>
          <CardHeader><CardTitle className="text-base">{language === "fr" ? "Pages les plus visitées (7j)" : "الصفحات الأكثر زيارة (7 أيام)"}</CardTitle></CardHeader>
          <CardContent className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={pageData} layout="vertical" margin={{ left: 40 }}>
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 5, 5, 0]}>
                  {pageData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {activeTab === "geo" && (
        <Card>
          <CardHeader><CardTitle className="text-base">{language === "fr" ? "Top villes (7j)" : "أفضل المدن (7 أيام)"}</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-3">
              {cityData.map(({ city, count }, i) => {
                const max = cityData[0]?.count || 1;
                return (
                  <div key={city} className={`flex items-center gap-4 ${isRtl ? "flex-row-reverse" : ""}`}>
                    <div className="w-6 text-center text-xs font-bold text-muted-foreground">{i + 1}</div>
                    <div className={`flex items-center gap-2 w-28 shrink-0 ${isRtl ? "flex-row-reverse" : ""}`}>
                      <MapPin className="w-3.5 h-3.5 text-primary" />
                      <span className="text-sm font-medium text-foreground truncate">{city}</span>
                    </div>
                    <div className="flex-1 bg-muted rounded-full h-2 overflow-hidden">
                      <div
                        className="h-2 bg-primary rounded-full transition-all"
                        style={{ width: `${(count / max) * 100}%` }}
                      />
                    </div>
                    <span className="text-sm text-muted-foreground w-8 text-right shrink-0">{count}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export default function Admin() {
  const { language, isRtl } = useI18n();
  const { data: stats } = useGetAdminStats();
  const { data: cases } = useAdminListCases();
  const updateCase = useUpdateCase();
  const queryClient = useQueryClient();
  const [activeSection, setActiveSection] = useState<"cases" | "visitors">("cases");

  const handleAction = (id: number, status: "approved" | "rejected" | "in_review" | "submitted") => {
    updateCase.mutate(
      { id, data: { status } },
      {
        onSuccess: () => {
          queryClient.invalidateQueries({ queryKey: getAdminListCasesQueryKey() });
          queryClient.invalidateQueries({ queryKey: getGetAdminStatsQueryKey() });
          queryClient.invalidateQueries({ queryKey: ["admin", "notifications"] });
        }
      }
    );
  };

  return (
    <AppLayout>
      <div className="max-w-7xl mx-auto space-y-8">
        <div className={`flex items-center justify-between ${isRtl ? "flex-row-reverse" : ""}`}>
          <div className={isRtl ? "text-right" : ""}>
            <h1 className="text-3xl font-bold text-foreground">
              {language === "fr" ? "Administration" : language === "ar" ? "لوحة الإدارة" : "لوحة الإدارة"}
            </h1>
            <p className="text-muted-foreground text-sm mt-1">
              {language === "fr" ? "Gérez les dossiers et suivez le trafic du site" : "إدارة الملفات ومتابعة حركة الموقع"}
            </p>
          </div>
          {/* Section toggle */}
          <div className="flex gap-1 p-1 bg-muted rounded-lg">
            <button
              onClick={() => setActiveSection("cases")}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeSection === "cases" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
            >
              {language === "fr" ? "Dossiers" : "الملفات"}
            </button>
            <button
              onClick={() => setActiveSection("visitors")}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${activeSection === "visitors" ? "bg-background text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}
            >
              {language === "fr" ? "Visiteurs" : "الزوار"}
            </button>
          </div>
        </div>

        {activeSection === "cases" && (
          <>
            {/* Charts */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Card>
                <CardHeader><CardTitle>{language === "fr" ? "Dossiers par Statut" : "الملفات حسب الحالة"}</CardTitle></CardHeader>
                <CardContent className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={stats?.casesByStatus || []} cx="50%" cy="50%" innerRadius={55} outerRadius={80} paddingAngle={5} dataKey="count" nameKey="status">
                        {stats?.casesByStatus.map((_, index) => <Cell key={index} fill={COLORS[index % COLORS.length]} />)}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
              <Card>
                <CardHeader><CardTitle>{language === "fr" ? "Dossiers par Service" : "الملفات حسب الخدمة"}</CardTitle></CardHeader>
                <CardContent className="h-[280px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={stats?.casesByService || []} layout="vertical" margin={{ left: 50 }}>
                      <XAxis type="number" />
                      <YAxis dataKey="serviceNameFr" type="category" width={100} tick={{ fontSize: 11 }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="hsl(var(--primary))" radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Cases table */}
            <Card>
              <CardHeader><CardTitle>{language === "fr" ? "Gestion des Dossiers" : "إدارة الملفات"}</CardTitle></CardHeader>
              <CardContent>
                <div className="rounded-xl border border-border overflow-hidden">
                  <Table>
                    <TableHeader>
                      <TableRow className="bg-muted/50">
                        <TableHead className="w-[140px] text-start font-semibold">Réf.</TableHead>
                        <TableHead className="text-start font-semibold">{language === "fr" ? "Service" : "الخدمة"}</TableHead>
                        <TableHead className="text-start font-semibold">{language === "fr" ? "Demandeur" : "مقدم الطلب"}</TableHead>
                        <TableHead className="w-[130px] text-center font-semibold">{language === "fr" ? "Statut" : "الحالة"}</TableHead>
                        <TableHead className="w-[260px] text-end font-semibold">{language === "fr" ? "Actions" : "إجراءات"}</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {cases?.map((c) => (
                        <TableRow key={c.id}>
                          <TableCell className="font-mono text-xs font-semibold text-start text-primary">
                            {c.referenceNumber}
                          </TableCell>
                          <TableCell className="text-sm font-medium text-start">
                            {language === "fr" ? c.service?.nameFr : c.service?.nameAr}
                          </TableCell>
                          <TableCell className="text-sm text-start text-muted-foreground">
                            {c.applicantName}
                          </TableCell>
                          <TableCell className="text-center">
                            <div className="flex justify-center">
                              <StatusBadge status={c.status} />
                            </div>
                          </TableCell>
                          <TableCell className="text-end">
                            <div className="flex items-center gap-1.5 justify-end flex-wrap">
                              {/* Approve button - available if not currently approved */}
                              {c.status !== "approved" && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-7 px-2.5 text-xs font-medium text-emerald-600 border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 gap-1 shadow-xs"
                                  onClick={() => handleAction(c.id, "approved")}
                                  title={language === "fr" ? "Accepter la demande" : "قبول الطلب"}
                                >
                                  <Check className="w-3.5 h-3.5" />
                                  <span>{language === "fr" ? "Accepter" : "قبول"}</span>
                                </Button>
                              )}

                              {/* Reject button - available if not currently rejected */}
                              {c.status !== "rejected" && (
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-7 px-2.5 text-xs font-medium text-red-600 border-red-300 hover:bg-red-50 hover:text-red-700 gap-1 shadow-xs"
                                  onClick={() => handleAction(c.id, "rejected")}
                                  title={language === "fr" ? "Rejeter la demande" : "رفض الطلب"}
                                >
                                  <X className="w-3.5 h-3.5" />
                                  <span>{language === "fr" ? "Rejeter" : "رفض"}</span>
                                </Button>
                              )}

                              {/* Reopen/Review button - available if decision was already made (approved or rejected) */}
                              {(c.status === "approved" || c.status === "rejected") && (
                                <Button
                                  size="sm"
                                  variant="ghost"
                                  className="h-7 px-2 text-xs text-amber-600 hover:bg-amber-50 hover:text-amber-700 gap-1"
                                  onClick={() => handleAction(c.id, "in_review")}
                                  title={language === "fr" ? "Changer la décision / Remettre en révision" : "تغيير القرار / إعادة المراجعة"}
                                >
                                  <RotateCcw className="w-3 h-3" />
                                  <span>{language === "fr" ? "Réviser" : "مراجعة"}</span>
                                </Button>
                              )}

                              {/* View full case details */}
                              <Link href={`/cases/${c.id}`}>
                                <Button
                                  size="icon"
                                  variant="ghost"
                                  className="h-7 w-7 text-muted-foreground hover:text-foreground"
                                  title={language === "fr" ? "Voir dossier complet" : "عرض الملف"}
                                >
                                  <Eye className="w-3.5 h-3.5" />
                                </Button>
                              </Link>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                      {!cases?.length && (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-10 text-muted-foreground">
                            {language === "fr" ? "Aucun dossier" : "لا توجد ملفات"}
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {activeSection === "visitors" && <VisitorStats />}
      </div>
    </AppLayout>
  );
}
