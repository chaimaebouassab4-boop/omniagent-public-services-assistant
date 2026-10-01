import { Link } from "wouter";
import { useEffect } from "react";
import {
  ArrowRight,
  Bot,
  CircleHelp,
  FileSearch,
  FolderKanban,
  Mail,
  MessageCircleQuestion,
  Phone,
} from "lucide-react";
import { AppLayout } from "@/components/layout/AppLayout";
import { Button } from "@/components/ui/button";
import { useI18n } from "@/lib/i18n";

const helpCards = [
  {
    icon: FileSearch,
    titleFr: "Démarrer une démarche",
    titleAr: "بدء إجراء إداري",
    descriptionFr: "Consultez les conditions, documents requis et délais avant de commencer.",
    descriptionAr: "اطلع على الشروط والوثائق المطلوبة والآجال قبل البدء.",
    href: "/services",
  },
  {
    icon: FolderKanban,
    titleFr: "Suivre un dossier",
    titleAr: "تتبع ملف",
    descriptionFr: "Retrouvez vos demandes en cours et leur état d'avancement.",
    descriptionAr: "اطلع على طلباتك الحالية وحالة تقدمها.",
    href: "/dashboard",
  },
  {
    icon: Bot,
    titleFr: "Utiliser l'Assistant IA",
    titleAr: "استخدام المساعد الذكي",
    descriptionFr: "Posez une question précise et recevez une réponse basée sur les procédures disponibles.",
    descriptionAr: "اطرح سؤالاً دقيقاً واحصل على جواب مبني على الإجراءات المتاحة.",
    href: "/chat",
  },
];

const faq = [
  {
    fr: "Comment savoir quels documents préparer ?",
    ar: "كيف أعرف الوثائق التي يجب إعدادها؟",
    answerFr: "Ouvrez la fiche du service concerné. La liste des pièces, les conditions et le délai indicatif y sont regroupés.",
    answerAr: "افتح صفحة الخدمة المعنية. ستجد فيها لائحة الوثائق والشروط والمدة التقريبية.",
  },
  {
    fr: "Où puis-je voir l'état de ma demande ?",
    ar: "أين يمكنني معرفة حالة طلبي؟",
    answerFr: "La page Mes dossiers affiche chaque demande et son étape actuelle. L'historique conserve aussi vos dernières activités.",
    answerAr: "تعرض صفحة ملفاتي كل طلب ومرحلته الحالية، كما يحتفظ السجل بآخر أنشطتك.",
  },
  {
    fr: "Que faire si la réponse de l'assistant est incomplète ?",
    ar: "ماذا أفعل إذا كان جواب المساعد غير مكتمل؟",
    answerFr: "Précisez la procédure, votre situation et la ville concernée. Vérifiez toujours les informations sensibles auprès de l'administration compétente.",
    answerAr: "حدد الإجراء ووضعيتك والمدينة المعنية، وتحقق دائماً من المعلومات الحساسة لدى الإدارة المختصة.",
  },
];

export default function Help() {
  const { language, isRtl } = useI18n();
  const isFrench = language === "fr";

  useEffect(() => {
    if (window.location.hash === "#confidentialite-securite") {
      document.getElementById("confidentialite-securite")?.scrollIntoView();
    }
  }, []);

  return (
    <AppLayout>
      <div className="space-y-8" dir={isRtl ? "rtl" : "ltr"}>
        <section className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
          <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_auto] lg:items-center">
            <div>
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-primary">
                <CircleHelp className="h-4 w-4" />
                <span>{isFrench ? "Centre d'aide OmniAgent" : "مركز مساعدة OmniAgent"}</span>
              </div>
              <h1 className="text-3xl font-bold tracking-tight text-[#17365d] dark:text-foreground sm:text-4xl">
                {isFrench ? "Comment pouvons-nous vous aider ?" : "كيف يمكننا مساعدتك؟"}
              </h1>
              <p className="mt-3 max-w-2xl text-muted-foreground">
                {isFrench
                  ? "Retrouvez rapidement les réponses essentielles pour vos démarches, vos dossiers et l'Assistant IA."
                  : "اعثر بسرعة على الأجوبة الأساسية المتعلقة بإجراءاتك وملفاتك والمساعد الذكي."}
              </p>
            </div>
            <Button asChild className="gap-2 justify-self-start lg:justify-self-end">
              <Link href="/chat">
                <MessageCircleQuestion className="h-4 w-4" />
                {isFrench ? "Poser une question" : "طرح سؤال"}
              </Link>
            </Button>
          </div>
        </section>

        <section className="grid gap-4 md:grid-cols-3">
          {helpCards.map((card) => (
            <Link
              key={card.href}
              href={card.href}
              className="group rounded-xl border border-border bg-card p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-primary/30 hover:shadow-md"
            >
              <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                <card.icon className="h-5 w-5" />
              </span>
              <h2 className="mt-4 font-semibold text-[#17365d] dark:text-foreground">{isFrench ? card.titleFr : card.titleAr}</h2>
              <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{isFrench ? card.descriptionFr : card.descriptionAr}</p>
              <span className="mt-4 flex items-center gap-1 text-sm font-semibold text-primary">
                {isFrench ? "Ouvrir" : "فتح"}<ArrowRight className={`h-4 w-4 transition-transform group-hover:translate-x-1 ${isRtl ? "rotate-180" : ""}`} />
              </span>
            </Link>
          ))}
        </section>

        <section id="questions-frequentes" className="rounded-2xl border border-border bg-card p-6 shadow-sm sm:p-8">
          <h2 className="text-xl font-bold text-[#17365d] dark:text-foreground">{isFrench ? "Questions fréquentes" : "الأسئلة الشائعة"}</h2>
          <div className="mt-5 divide-y divide-border">
            {faq.map((item) => (
              <details key={item.fr} className="group py-4 first:pt-0 last:pb-0">
                <summary className="cursor-pointer list-none font-semibold text-foreground marker:hidden">
                  <span className="flex items-center justify-between gap-4">
                    {isFrench ? item.fr : item.ar}
                    <span className="text-xl font-normal text-primary transition-transform group-open:rotate-45">+</span>
                  </span>
                </summary>
                <p className="mt-3 max-w-3xl text-sm leading-relaxed text-muted-foreground">{isFrench ? item.answerFr : item.answerAr}</p>
              </details>
            ))}
          </div>
        </section>

        <section id="confidentialite-securite" lang="fr" dir="ltr" aria-labelledby="confidentialite-title" className="scroll-mt-24 rounded-xl border border-border bg-card p-6 sm:p-8">
          <h2 id="confidentialite-title" className="text-xl font-bold text-foreground">Confidentialité et sécurité de votre espace</h2>
          <div className="mt-5 space-y-5 text-sm leading-relaxed text-muted-foreground">
            <div><h3 className="font-semibold text-foreground">À quoi servent vos informations ?</h3><p className="mt-2">Les informations de votre profil permettent de préremplir vos dossiers. Les documents que vous ajoutez peuvent être analysés pour extraire des informations et repérer les éléments à vérifier, puis réutilisés dans les démarches que vous préparez.</p></div>
            <div><h3 className="font-semibold text-foreground">Qui peut accéder à vos dossiers ?</h3><p className="mt-2">Votre espace personnel nécessite une connexion. Les contrôles d’accès limitent la consultation à vos propres dossiers et aux comptes d’administration autorisés pour leur traitement dans OmniAgent.</p></div>
            <div><h3 className="font-semibold text-foreground">Comment gérer vos informations ?</h3><p className="mt-2">Vous pouvez consulter et modifier les informations de votre profil, ainsi que consulter ou supprimer les documents personnels depuis votre espace. La préparation d’un dossier peut conserver une copie des informations et documents utilisés pour cette démarche.</p><Link href="/profile" className="mt-3 inline-flex min-h-11 items-center font-semibold text-foreground underline underline-offset-4">Gérer mon profil et mes documents</Link></div>
            <p className="border-t border-border pt-4">Les vérifications d’OmniAgent servent à vous accompagner dans la préparation. Elles ne remplacent pas la décision de l’administration compétente.</p>
          </div>
        </section>

        <section className="rounded-2xl border border-primary/20 bg-primary/5 p-6 sm:p-8">
          <h2 className="text-xl font-bold text-[#17365d] dark:text-foreground">{isFrench ? "Besoin d'une aide supplémentaire ?" : "هل تحتاج إلى مساعدة إضافية؟"}</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            {isFrench ? "Notre équipe peut vous orienter vers le service compétent." : "يمكن لفريقنا توجيهك إلى المصلحة المختصة."}
          </p>
          <div className="mt-4 flex flex-wrap gap-3 text-sm">
            <span className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2"><Mail className="h-4 w-4 text-primary" /> support@omniagent.ma</span>
            <span className="flex items-center gap-2 rounded-lg border bg-card px-3 py-2"><Phone className="h-4 w-4 text-primary" /> +212 5 00 00 00 00</span>
          </div>
        </section>
      </div>
    </AppLayout>
  );
}
