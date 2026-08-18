import { ReactNode, useEffect } from "react";
import { Switch, Route, Redirect, Router as WouterRouter, useLocation } from "wouter";
import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query";
import { setAuthTokenGetter } from "@workspace/api-client-react";
import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { I18nProvider, useI18n } from "@/lib/i18n";
import { trackVisit } from "@/lib/history";
import {
  getToken,
  getStoredUser,
  handleUnauthorized,
  isAuthenticated,
} from "@/lib/auth";
import NotFound from "@/pages/not-found";

// Attach the stored JWT (if any) as a Bearer token on every API request.
setAuthTokenGetter(() => getToken());

import Home from "@/pages/home";
import Login from "@/pages/login";
import Signup from "@/pages/signup";
import Services from "@/pages/services";
import Dashboard from "@/pages/dashboard";
import CaseDetail from "@/pages/case-detail";
import Chat from "@/pages/chat";
import Profile from "@/pages/profile";
import Admin from "@/pages/admin";

function handleApiError(error: unknown): void {
  if (
    typeof error === "object" &&
    error !== null &&
    "status" in error &&
    typeof error.status === "number"
  ) {
    handleUnauthorized(error.status);
  }
}

const queryClient = new QueryClient({
  queryCache: new QueryCache({ onError: handleApiError }),
  mutationCache: new MutationCache({ onError: handleApiError }),
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        if (
          typeof error === "object" &&
          error !== null &&
          "status" in error &&
          error.status === 401
        ) {
          return false;
        }
        return failureCount < 2;
      },
    },
  },
});

/** Renders children only for authenticated users; otherwise redirects to /login. */
function Protected({ children, adminOnly = false }: { children: ReactNode; adminOnly?: boolean }) {
  if (!isAuthenticated()) return <Redirect to="/login" />;
  if (adminOnly && !getStoredUser()?.isAdmin) return <Redirect to="/dashboard" />;
  return <>{children}</>;
}

/** Keeps already-authenticated users out of the login/signup pages. */
function GuestOnly({ children }: { children: ReactNode }) {
  if (isAuthenticated()) {
    return <Redirect to={getStoredUser()?.isAdmin ? "/admin" : "/dashboard"} />;
  }
  return <>{children}</>;
}

function AnalyticsTracker() {
  const [location] = useLocation();
  const { language } = useI18n();

  useEffect(() => {
    const labels: Record<string, string> = {
      "/": "Accueil",
      "/login": "Connexion",
      "/signup": "Inscription",
      "/services": "Services",
      "/chat": "Assistant IA",
      "/dashboard": "Tableau de bord",
      "/profile": "Profil",
      "/admin": "Administration",
    };
    const label = location.startsWith("/cases/") ? "Détail demande" : (labels[location] ?? location);
    trackVisit(location, label, language);
  }, [location, language]);

  return null;
}

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/login">
        <GuestOnly><Login /></GuestOnly>
      </Route>
      <Route path="/signup">
        <GuestOnly><Signup /></GuestOnly>
      </Route>
      <Route path="/services" component={Services} />
      <Route path="/chat">
        <Protected><Chat /></Protected>
      </Route>
      <Route path="/dashboard">
        <Protected><Dashboard /></Protected>
      </Route>
      <Route path="/cases/:id">
        <Protected><CaseDetail /></Protected>
      </Route>
      <Route path="/profile">
        <Protected><Profile /></Protected>
      </Route>
      <Route path="/admin">
        <Protected adminOnly><Admin /></Protected>
      </Route>
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <I18nProvider>
        <TooltipProvider>
          <WouterRouter base={import.meta.env.BASE_URL.replace(/\/$/, "")}>
            <AnalyticsTracker />
            <Router />
          </WouterRouter>
          <Toaster />
        </TooltipProvider>
      </I18nProvider>
    </QueryClientProvider>
  );
}

export default App;
