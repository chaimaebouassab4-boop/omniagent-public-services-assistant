import { ArrowRight, Building2, FileCheck2, Home, Landmark } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { listServices } from "../services/services";
import type { Service } from "../types/api";
import { Button } from "../components/ui/Button";
import { Card, CardContent } from "../components/ui/Card";
import { LoadingState } from "../components/ui/LoadingState";

const icons = {
  licence: Building2,
  permit: Landmark,
  residence: Home,
  birth: FileCheck2
};

const localCardContent = {
  licence: {
    title: "Rokhsa Tijariya",
    titleAr: "رخصة تجارية",
    description: "Bda talab dyal lmaktab w ttb3 kol marhala b sohola.",
    accent: "from-[#0f3d5e] to-[#0f766e]",
    sketch: "🏪"
  },
  permit: {
    title: "Tarkhis Bina",
    titleAr: "ترخيص البناء",
    description: "Sift watha2iq dial l'bina w tchouf jawb lhandassa.",
    accent: "from-[#c66a14] to-[#8b4c1b]",
    sketch: "🧱"
  },
  residence: {
    title: "Shahadat Sakan",
    titleAr: "شهادة السكنى",
    description: "Dir talab shahada dyal skan b tariqa wadha.",
    accent: "from-[#0f766e] to-[#1d5d54]",
    sketch: "🏠"
  },
  birth: {
    title: "Rasm Izdiyad",
    titleAr: "رسم الازدياد",
    description: "Khrej noskha men rasm l'izdiyad bla ta3qid.",
    accent: "from-[#b45309] to-[#7c2d12]",
    sketch: "📜"
  }
};

/** Service selection landing page for citizens starting a request. */
export function HomePage(): JSX.Element {
  const [services, setServices] = useState<Service[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    listServices()
      .then(setServices)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) {
    return <LoadingState />;
  }

  return (
    <div className="grid gap-8 pb-20">
      <section className="relative grid gap-5 overflow-hidden rounded-xl border border-[#d9ccb8] bg-[#fffdf8] p-6 shadow-panel lg:grid-cols-[1.2fr_0.8fr] lg:p-8">
        <div className="pointer-events-none absolute inset-0 opacity-20" aria-hidden="true">
          <div className="h-full w-full bg-[radial-gradient(circle_at_20%_20%,rgba(15,61,94,0.3),transparent_35%),radial-gradient(circle_at_80%_15%,rgba(217,119,6,0.3),transparent_30%)]" />
        </div>
        <div>
          <p className="text-sm font-bold uppercase tracking-wide text-[#0f766e]">Marhba bik</p>
          <h1 className="max-w-3xl text-3xl font-extrabold tracking-normal text-slate-950 sm:text-5xl">
            Khadamat l'idariya b lmaghribiya
          </h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-slate-600">
            Khayar service, hder m3a lmosaa3id, sft watha2iq, w tb3 dossier dyalk marhala b marhala.
          </p>
          <p className="mt-2 max-w-2xl text-lg text-[#6b4f3a]">
            منصة قريبة ليك، بسيطة وواضحة
          </p>
          <p className="mt-1 max-w-2xl text-sm text-slate-500">
            Version francaise disponible pour les demarches administratives.
          </p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/cases">
              <Button type="button" className="bg-[#0f3d5e] hover:bg-[#0d324c]">
                Ttba3 dossier
              </Button>
            </Link>
            <Link to="/chat/licence">
              <Button type="button" variant="outline" className="border-[#0f3d5e] text-[#0f3d5e]">
                Bda lhadra
              </Button>
            </Link>
          </div>
        </div>
        <div className="relative grid content-start gap-3 rounded-xl border border-[#e9dcc7] bg-white/80 p-4 backdrop-blur">
          {["Tsjil talab", "Morajaat watha2iq", "Qarar nihai"].map((label, index) => (
            <div key={label} className="flex items-center gap-3 rounded-lg bg-[#fff8ef] p-3 shadow-sm">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-[#0f766e] text-sm font-bold text-white">
                {index + 1}
              </span>
              <span className="text-sm font-semibold text-[#6b4f3a]">{label}</span>
            </div>
          ))}
        </div>
      </section>

      <section aria-labelledby="services-title" className="grid gap-4">
        <h2 id="services-title" className="text-2xl font-extrabold text-slate-950">
          Khadamat lmatlouba
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {services.map((service) => {
            const Icon = icons[service.id];
            const local = localCardContent[service.id];
            return (
              <Card key={service.id} className="overflow-hidden border-[#dfd1bd] bg-[#fffdfa]">
                <CardContent className="grid h-full gap-4 p-0">
                  <div className={`h-24 bg-gradient-to-r ${local.accent} p-4 text-white`}>
                    <div className="flex items-center justify-between">
                      <span className="text-3xl">{local.sketch}</span>
                      <span className="rounded-full border border-white/45 px-2 py-1 text-xs font-bold">
                        Handcrafted
                      </span>
                    </div>
                  </div>
                  <div className="px-4 pb-4">
                    <span className="grid h-11 w-11 place-items-center rounded-lg border border-[#d5c3ab] bg-[#fff8ef] text-[#0f766e]">
                    <Icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <div>
                    <h3 className="mt-3 text-lg font-extrabold text-slate-950">{local.title}</h3>
                    <p className="text-sm font-semibold text-[#0f766e]">{local.titleAr}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-700">{local.description}</p>
                    <p className="mt-1 text-xs text-slate-500">{service.description}</p>
                  </div>
                  <p className="text-sm font-semibold text-[#6b4f3a]">
                    Moudat lmoraja3a: {service.averageProcessingDays} iyam
                  </p>
                  <Link to={`/chat/${service.id}`} className="mt-auto">
                    <Button type="button" variant="outline" className="w-full border-[#0f3d5e] text-[#0f3d5e]">
                      Bda talab <ArrowRight className="h-4 w-4" aria-hidden="true" />
                    </Button>
                  </Link>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <Card className="border-[#dfd1bd] bg-white/95 lg:col-span-2">
          <CardContent className="p-5">
            <h2 className="text-2xl font-extrabold text-slate-950">Qisas Naja7 Akhira</h2>
            <p className="text-sm text-[#6b4f3a]">Recent Success Stories</p>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              {[
                {
                  name: "Amina, Salé",
                  quote:
                    "Dossier dyali dyal shahadat skan tsala f 3 iyam. Kolchi kan mnhad wa msshel."
                },
                {
                  name: "Youssef, Fès",
                  quote:
                    "Lchat jawabni 3la watha2iq lli khasni w ma bqitch ndour bin l'idaRat."
                }
              ].map((story) => (
                <article key={story.name} className="rounded-xl border border-[#e8dac7] bg-[#fff8ef] p-4">
                  <p className="text-sm leading-6 text-slate-700">"{story.quote}"</p>
                  <p className="mt-3 text-sm font-extrabold text-[#0f3d5e]">{story.name}</p>
                </article>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="border-[#dfd1bd] bg-white/95">
          <CardContent className="p-5">
            <h2 className="text-xl font-extrabold text-slate-950">Mosa3ada & Da3m</h2>
            <p className="text-sm text-[#6b4f3a]">Help & Support</p>
            <ul className="mt-4 grid gap-3 text-sm text-slate-700">
              <li className="rounded-lg bg-[#fff8ef] p-3">Ila 3ndek mochkil, ktb lina fel chat moubachara.</li>
              <li className="rounded-lg bg-[#fff8ef] p-3">Kayn support b Darija, العربية, ou Français.</li>
              <li className="rounded-lg bg-[#fff8ef] p-3">Hotline: 05 37 00 00 00</li>
            </ul>
          </CardContent>
        </Card>
      </section>

      <section className="rounded-xl border border-[#dccdb8] bg-[#fffdf8] p-5">
        <h2 className="text-2xl font-extrabold text-slate-950">Makatib l3omomiya</h2>
        <p className="text-sm text-[#6b4f3a]">Local government offices</p>
        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {[
            { city: "Rabat", office: "Moqata3at Hassan", phone: "05 37 22 11 00" },
            { city: "Casablanca", office: "Moqata3at Maârif", phone: "05 22 98 33 21" },
            { city: "Marrakech", office: "Moqata3at Gueliz", phone: "05 24 44 18 90" }
          ].map((item) => (
            <article key={item.city} className="rounded-xl border border-[#e8dac7] bg-white p-4">
              <h3 className="text-lg font-extrabold text-[#0f3d5e]">{item.city}</h3>
              <p className="mt-1 text-sm text-slate-600">{item.office}</p>
              <p className="mt-2 text-sm font-bold text-[#0f766e]">{item.phone}</p>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
