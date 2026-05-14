// API Client
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：添加token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 响应拦截器：处理401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// 认证API
export const authAPI = {
  register: (data) => apiClient.post('/auth/register', data),
  login: (username, password) => {
    return apiClient.post('/auth/login', { username, password });
  },
  getCurrentUser: () => apiClient.get('/auth/me'),
};

// 项目API
export const projectsAPI = {
  list: () => apiClient.get('/projects'),
  create: (data) => apiClient.post('/projects', data),
  get: (id) => apiClient.get(`/projects/${id}`),
  update: (id, data) => apiClient.put(`/projects/${id}`, data),
  delete: (id) => apiClient.delete(`/projects/${id}`),
  getMembers: (id) => apiClient.get(`/projects/${id}/members`),
  addMember: (id, data) => apiClient.post(`/projects/${id}/members`, data),
  removeMember: (id, userId) => apiClient.delete(`/projects/${id}/members/${userId}`),
  updateMemberRole: (id, userId, role) => apiClient.put(`/projects/${id}/members/${userId}`, { role }),
  getStats: (id) => apiClient.get(`/projects/${id}/stats`),
};

// 组织API
export const organizationsAPI = {
  list: () => apiClient.get('/organizations'),
  create: (data) => apiClient.post('/organizations', data),
  get: (id) => apiClient.get(`/organizations/${id}`),
};

// 决策API
export const decisionsAPI = {
  getPending: () => apiClient.get('/decisions/pending'),
  resolve: (id, response) => apiClient.post(`/decisions/${id}/resolve`, response),
};

// 任务API
export const tasksAPI = {
  get: (id) => apiClient.get(`/workflow/tasks/${id}`),
  getTimeline: (id) => apiClient.get(`/tasks/${id}/timeline`),
  getEvents: (id) => apiClient.get(`/workflow/tasks/${id}/events`),
  getArtifacts: (id) => apiClient.get(`/workflow/tasks/${id}/artifacts`),
  execute: (id, data) => apiClient.post(`/workflow/tasks/${id}/execute`, data),
};

export default apiClient;
