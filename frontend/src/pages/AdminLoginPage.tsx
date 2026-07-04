import { ShieldCheck } from "lucide-react";
import { AdminLoginForm } from "../components/forms/AdminLoginForm";
import { Card, CardContent, CardHeader } from "../components/ui/Card";

/** Administrator authentication page. */
export function AdminLoginPage(): JSX.Element {
  return (
    <div className="mx-auto grid min-h-[70vh] max-w-md place-items-center">
      <Card className="w-full">
        <CardHeader className="text-center">
          <ShieldCheck className="mx-auto h-10 w-10 text-primary" aria-hidden="true" />
          <h1 className="mt-3 text-2xl font-extrabold text-slate-950">Admin sign in</h1>
          <p className="mt-1 text-sm text-slate-500">Protected case management panel</p>
        </CardHeader>
        <CardContent>
          <AdminLoginForm />
        </CardContent>
      </Card>
    </div>
  );
}
