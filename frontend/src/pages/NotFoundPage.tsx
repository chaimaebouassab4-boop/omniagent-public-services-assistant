import { Link } from "react-router-dom";
import { Button } from "../components/ui/Button";

/** Fallback route for unknown URLs. */
export function NotFoundPage(): JSX.Element {
  return (
    <div className="grid min-h-[60vh] place-items-center text-center">
      <div>
        <h1 className="text-4xl font-extrabold text-slate-950">Page not found</h1>
        <p className="mt-3 text-slate-600">The route does not match a public service screen.</p>
        <Link to="/" className="mt-6 inline-block">
          <Button type="button">Go to services</Button>
        </Link>
      </div>
    </div>
  );
}
