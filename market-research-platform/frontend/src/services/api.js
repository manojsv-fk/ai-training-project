// filepath: market-research-platform/frontend/src/services/api.js
// Centralized Axios-based API client. All REST calls to the FastAPI backend go here.

import axios from 'axios';

const BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Response interceptor for global error handling
client.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || 'An error occurred';
    console.error('API Error:', message);
    return Promise.reject(error);
  }
);

// ── Documents ──────────────────────────────────────────────────────────────
export const listDocuments = (filters = {}) =>
  client.get('/api/documents', { params: filters }).then((r) => r.data);

export const getDocument = (documentId) =>
  client.get(`/api/documents/${documentId}`).then((r) => r.data);

export const uploadDocument = (file, sourceName = '') => {
  const formData = new FormData();
  formData.append('file', file);
  return client.post(`/api/documents/upload?source_name=${encodeURIComponent(sourceName)}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then((r) => r.data);
};

export const deleteDocument = (documentId) =>
  client.delete(`/api/documents/${documentId}`).then((r) => r.data);

// ── Reports ────────────────────────────────────────────────────────────────
export const listReports = (params = {}) =>
  client.get('/api/reports', { params }).then((r) => r.data);

export const getReport = (reportId) =>
  client.get(`/api/reports/${reportId}`).then((r) => r.data);

export const generateReport = (payload) =>
  client.post('/api/reports/generate', payload).then((r) => r.data);

export const exportReport = (reportId, format) =>
  client.get(`/api/reports/${reportId}/export`, {
    params: { format },
    responseType: 'blob',
  }).then((r) => r.data);

export const deleteReport = (reportId) =>
  client.delete(`/api/reports/${reportId}`).then((r) => r.data);

// ── Trends ─────────────────────────────────────────────────────────────────
export const listTrends = (filters = {}) =>
  client.get('/api/trends', { params: filters }).then((r) => r.data);

export const triggerTrendAnalysis = (documentIds = null) =>
  client.post('/api/trends/analyze', null, {
    params: documentIds ? { document_ids: documentIds } : {},
  }).then((r) => r.data);

// ── Chat ───────────────────────────────────────────────────────────────────
export const createChatSession = () =>
  client.post('/api/chat/sessions').then((r) => r.data);

export const getChatHistory = (sessionId) =>
  client.get(`/api/chat/sessions/${sessionId}`).then((r) => r.data);

export const clearChatSession = (sessionId) =>
  client.delete(`/api/chat/sessions/${sessionId}`).then((r) => r.data);

// ── News ───────────────────────────────────────────────────────────────────
export const triggerNewsSync = () =>
  client.post('/api/news/sync').then((r) => r.data);

export const getNewsConfig = () =>
  client.get('/api/news/config').then((r) => r.data);

// ── Status ─────────────────────────────────────────────────────────────────
export const getStatus = () =>
  client.get('/api/status').then((r) => r.data);

// ── Settings ───────────────────────────────────────────────────────────────
export const getSettings = () =>
  client.get('/api/settings').then((r) => r.data);

export const updateSettings = (payload) =>
  client.patch('/api/settings', payload).then((r) => r.data);

// ── Utility: trigger file download from blob ───────────────────────────────
export const downloadBlob = (blob, filename) => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};
