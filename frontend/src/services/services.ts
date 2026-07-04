import { services } from "../data/mockData";
import { apiClient } from "./apiClient";
import type { ApiSuccess, Service } from "../types/api";

interface BackendService {
  id: string;
  name_ar?: string;
  name_fr?: string;
  name_darija?: string;
  description_ar?: string;
  description_fr?: string;
  avg_days?: number;
  required_docs?: string[];
}

function normalizeServiceId(serviceId: string): Service["id"] | null {
  const map: Record<string, Service["id"]> = {
    licence: "licence",
    permit: "permit",
    residence: "residence",
    residence_certificate: "residence",
    birth: "birth",
    birth_certificate: "birth",
    marriage: "marriage",
    marriage_contract: "marriage"
  };

  return map[serviceId] ?? null;
}

/** Lists public service definitions from the backend, with seed data fallback. */
export async function listServices(): Promise<Service[]> {
  try {
    const response = await apiClient.get<ApiSuccess<BackendService[]>>("/api/services");
    return response.data.data
      .map((service) => {
        const id = normalizeServiceId(service.id);
        if (!id) {
          return null;
        }

        return {
          id,
          name: service.name_fr ?? service.name_darija ?? service.name_ar ?? service.id,
          description: service.description_fr ?? service.description_ar ?? "",
          requiredDocuments: service.required_docs ?? [],
          averageProcessingDays: service.avg_days ?? 0
        } satisfies Service;
      })
      .filter((service): service is Service => service !== null);
  } catch {
    return Promise.resolve(services);
  }
}
