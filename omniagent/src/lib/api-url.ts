const DEFAULT_RAILWAY_URL = "https://omniagent-public-services-assistant-production.up.railway.app";
const configuredBase = (import.meta.env.VITE_API_BASE_URL || DEFAULT_RAILWAY_URL).replace(/\/$/, "");

/** Resolve one backend path for both the Vite proxy and direct deployments. */
export function apiUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${configuredBase}${normalizedPath}`;
}
