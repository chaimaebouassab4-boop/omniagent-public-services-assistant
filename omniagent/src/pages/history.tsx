import { useI18n } from "@/lib/i18n";
import { AppLayout } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { motion } from "framer-motion";
import { History, Trash2, Globe, Clock, ArrowRight, ArrowLeft } from "lucide-react";
import { useState, useEffect } from "react";
import { getHistory, clearHistory, type VisitEntry } from "@/lib/history";
import { Link } from "wouter";

const PAGE_LABELS: Record<string, { fr: string; ar: string; color: string }> = {
  "/": { fr: "Accueil", ar: "الرئيسية", color: "bg-primary/10 text-primary" },
  "/services": { fr: "Services", ar: "الخدمات", color: "bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400" },
  "/chat": { fr: "Assistant IA", ar: "المساعد الذكي", color: "bg-violet-100 text-violet-700 dark:bg-violet-900/30 dark:text-violet-400" },
  "/dashboard": { fr: "Mes dossiers", ar: "قضاياي", color: "bg-teal-100 text-teal-700 dark:bg-teal-900/30 dark:text-teal-400" },
  "/login": { fr: "Connexion", ar: "دخول", color: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400" },
  "/signup": { fr: "Inscription", ar: "تسجيل", color: "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400" },
  "/admin": { fr: "Administration", ar: "لوحة الإدارة", color: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400" },
};

function getPageLabel(page: string, lang: string) {
  const info = PAGE_LABELS[page];
  if (!info) return { label: page, color: "bg-muted text-muted-foreground" };
  return { label: lang === "ar" || lang === "darija" ? info.ar : info.fr, color: info.color };
}

function formatTime(ts: number, lang: string) {
  const now = Date.now();
  const diff = now - ts;
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);
  if (lang === "fr") {
    if (mins < 1) return "À l'instant";
    if (mins < 60) return `Il y a ${mins} min`;
    if (hours < 24) return `Il y a ${hours}h`;
    return `Il y a ${days} jour${days > 1 ? "s" : ""}`;
  } else {
    if (mins < 1) return "الآن";
    if (mins < 60) return `منذ ${mins} دقيقة`;
    if (hours < 24) return `منذ ${hours} ساعة`;
    return `منذ ${days} يوم`;
  }
}

function groupByDate(entries: VisitEntry[]) {
  const groups: Record<string, VisitEntry[]> = {};
  entries.forEach((e) => {
    const d = new Date(e.timestamp);
    const key = d.toLocaleDateString("fr-MA", { weekday: "long", day: "numeric", month: "long" });
    if (!groups[key]) groups[key] = [];
    groups[key].push(e);
  });
  return Object.entries(groups);
}

export default function HistoryPage() {
  const { language, isRtl } = useI18n();
  const [entries, setEntries] = useState<VisitEntry[]>([]);
  const [confirmed, setConfirmed] = useState(false);

  useEffect(() => {
    setEntries(getHistory());
  }, []);

  const handleClear = () => {
    if (!confirmed) { setConfirmed(true); return; }
    clearHistory();
    setEntries([]);
    setConfirmed(false);
  };

  const grouped = groupByDate(entries);
  const Arrow = isRtl ? ArrowLeft : ArrowRight;

  return (
    <AppLayout>
      <div className="max-w-3xl mx-auto space-y-8">
        {/* Header */}
        <div className={`flex items-center justify-between ${isRtl ? "flex-row-reverse" : ""}`}>
          <div className={isRtl ? "text-right" : ""}>
            <h1 className="text-3xl font-bold text-foreground flex items-center gap-3">
              <History className="w-7 h-7 text-primary" />
              {language === "fr" ? "Mon historique" : language === "ar" ? "سجل زياراتي" : "سجل الزيارات ديالي"}
            </h1>
            <p className="text-muted-foreground mt-1 text-sm">
              {language === "fr"
                ? `${entries.length} page${entries.length > 1 ? "s" : ""} visitée${entries.length > 1 ? "s" : ""}`
                : `${entries.length} صفحة تمت زيارتها`}
            </p>
          </div>
          {entries.length > 0 && (
            <Button
              variant={confirmed ? "destructive" : "outline"}
              size="sm"
              className="gap-2"
              onClick={handleClear}
            >
              <Trash2 className="w-4 h-4" />
              {confirmed
                ? (language === "fr" ? "Confirmer" : "تأكيد")
                : (language === "fr" ? "Effacer" : "مسح")}
            </Button>
          )}
        </div>

        {/* Empty state */}
        {entries.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
            className="text-center py-24 flex flex-col items-center gap-4"
          >
            <div className="w-16 h-16 bg-muted rounded-full flex items-center justify-center">
              <History className="w-7 h-7 text-muted-foreground" />
            </div>
            <div>
              <p className="font-semibold text-foreground">
                {language === "fr" ? "Aucun historique" : "لا يوجد سجل"}
              </p>
              <p className="text-sm text-muted-foreground mt-1">
                {language === "fr" ? "Naviguez dans l'application pour voir vos visites ici." : "تصفح التطبيق لرؤية زياراتك هنا."}
              </p>
            </div>
            <Button asChild className="gap-2 mt-2">
              <Link href="/services">
                {language === "fr" ? "Voir les services" : "عرض الخدمات"}
                <Arrow className="w-4 h-4" />
              </Link>
            </Button>
          </motion.div>
        )}

        {/* Timeline */}
        {grouped.map(([date, items]) => (
          <div key={date} className="space-y-3">
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-widest pb-1 border-b border-border">
              {date}
            </p>
            <div className="space-y-2">
              {items.map((entry, i) => {
                const { label, color } = getPageLabel(entry.page, language);
                return (
                  <motion.div
                    key={entry.id}
                    initial={{ opacity: 0, x: isRtl ? 10 : -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className={`flex items-center gap-4 p-4 bg-card border border-border rounded-xl hover:border-primary/30 transition-colors ${isRtl ? "flex-row-reverse" : ""}`}
                  >
                    <div className="w-9 h-9 bg-muted rounded-lg flex items-center justify-center shrink-0">
                      <Globe className="w-4 h-4 text-muted-foreground" />
                    </div>
                    <div className={`flex-1 min-w-0 ${isRtl ? "text-right" : ""}`}>
                      <div className={`flex items-center gap-2 ${isRtl ? "flex-row-reverse" : ""}`}>
                        <Badge className={`text-xs px-2 py-0.5 rounded-full border-0 font-medium ${color}`}>
                          {label}
                        </Badge>
                        <span className="text-xs text-muted-foreground truncate">{entry.page}</span>
                      </div>
                      <div className={`flex items-center gap-1 mt-1 text-xs text-muted-foreground ${isRtl ? "flex-row-reverse" : ""}`}>
                        <Clock className="w-3 h-3" />
                        <span>{formatTime(entry.timestamp, language)}</span>
                        <span>·</span>
                        <span className="uppercase">{entry.lang}</span>
                      </div>
                    </div>
                    <Link href={entry.page} className="shrink-0 text-muted-foreground hover:text-primary transition-colors">
                      <Arrow className="w-4 h-4" />
                    </Link>
                  </motion.div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </AppLayout>
  );
}
