import axios, { AxiosError, type AxiosInstance } from "axios";
import { tokenStorage } from "./tokenStorage";
import type { ApiErrorBody } from "../types/api";

const baseURL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

/** Axios instance configured for the public services backend API. */
export const apiClient: AxiosInstance = axios.create({
  baseURL,
  headers: {
    "Content-Type": "application/json"
  },
  timeout: 15_000
});

apiClient.interceptors.request.use((config) => {
  const token = tokenStorage.getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiErrorBody>) => {
    if (error.response?.status === 401) {
      tokenStorage.clear();
    }

    const message =
      error.response?.data?.error ?? error.message ?? "Unexpected API error";
    return Promise.reject(new Error(message));
  }
);
