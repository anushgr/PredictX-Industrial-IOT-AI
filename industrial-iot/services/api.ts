import axios from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

api.interceptors.request.use((config) => {
  // Only access localStorage in browser environment
  try {
    if (typeof window !== "undefined" && typeof localStorage !== "undefined") {
      const token = localStorage.getItem("predictx_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
  } catch {
    // Silently fail if localStorage is not available
  }
  return config;
});

export const sensorApi = {
  live: () => api.get("/api/sensors/live"),
  history: () => api.get("/api/sensors/history"),
};

export const machineApi = {
  list: () => api.get("/api/machines"),
  byId: (id: string) => api.get(`/api/machines/${id}`),
};

export const predictionApi = {
  failure: () => api.get("/api/predict/failure"),
  alerts: () => api.get("/api/predict/alerts"),
};

export const analyticsApi = {
  summary: () => api.get("/api/analytics"),
};

export const reportApi = {
  export: (type: string, format: "pdf" | "excel" | "csv") =>
    api.post("/api/reports/export", { type, format }),
};

export const authApi = {
  login: (email: string, password: string) =>
    api.post("/api/login", { email, password }),
  users: () => api.get("/api/users"),
};

export const chatApi = {
  query: (message: string) => api.post("/api/chat/query", { message }),
};
