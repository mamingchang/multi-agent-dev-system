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
  register: (data) => apiClient.post('/api/auth/register', data),
  login: (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    return apiClient.post('/api/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  getCurrentUser: () => apiClient.get('/api/auth/me'),
};

// 项目API
export const projectsAPI = {
  list: () => apiClient.get('/api/projects'),
  create: (data) => apiClient.post('/api/projects', data),
  get: (id) => apiClient.get(`/api/projects/${id}`),
  update: (id, data) => apiClient.put(`/api/projects/${id}`, data),
  delete: (id) => apiClient.delete(`/api/projects/${id}`),
  getMembers: (id) => apiClient.get(`/api/projects/${id}/members`),
  addMember: (id, data) => apiClient.post(`/api/projects/${id}/members`, data),
  removeMember: (id, userId) => apiClient.delete(`/api/projects/${id}/members/${userId}`),
  updateMemberRole: (id, userId, role) => apiClient.put(`/api/projects/${id}/members/${userId}`, { role }),
  getStats: (id) => apiClient.get(`/api/projects/${id}/stats`),
};

// 决策API
export const decisionsAPI = {
  getPending: () => apiClient.get('/api/decisions/pending'),
  resolve: (id, response) => apiClient.post(`/api/decisions/${id}/resolve`, response),
};

// 任务API
export const tasksAPI = {
  getTimeline: (id) => apiClient.get(`/api/tasks/${id}/timeline`),
};

export default apiClient;
