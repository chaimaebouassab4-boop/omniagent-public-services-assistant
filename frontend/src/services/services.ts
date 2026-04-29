import { services } from "../data/mockData";
import { apiClient } from "./apiClient";
import type { ApiSuccess, Service } from "../types/api";

/** Lists public service definitions from the backend, with seed data fallback. */
export async function listServices(): Promise<Service[]> {
  try {
    const response = await apiClient.get<ApiSuccess<Service[]>>("/api/services");
    return response.data.data;
  } catch {
    return Promise.resolve(services);
  }
}
