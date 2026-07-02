import axios from "axios";

const BASE_URL = "http://localhost:8080/api";
const api = axios.create({ baseURL: BASE_URL });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const registerCitizen = (data) => api.post("/applications/register", data);
export const loginCitizen = (data) => api.post("/applications/login", data);
export const createApplication = (data) => api.post("/applications/", data);
export const listApplications = () => api.get("/applications/");
export const getApplication = (id) => api.get(`/applications/${id}`);
export const processApplication = (id) => api.post(`/applications/${id}/process`);
export const uploadDocument = (formData) => api.post("/documents/upload", formData, { headers: { "Content-Type": "multipart/form-data" } });
export const extractDocument = (id) => api.post(`/documents/${id}/extract`);
export const getDocumentUrl = (id) => api.get(`/documents/${id}/url`);
export const submitComplaint = (data) => api.post("/complaints/", data);
export const listComplaints = () => api.get("/complaints/");
export const scoreFraud = (appId) => api.post(`/fraud/score/${appId}`);
export const queryRAG = (data) => api.post("/rag/query", data);
export const getAdminDashboard = () => api.get("/admin/dashboard");
export const getForecast = (days = 30) => api.get(`/admin/forecast?days=${days}`);
export const getFraudAlerts = () => api.get("/admin/fraud-alerts");

export default api;
