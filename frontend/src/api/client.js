import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// SECURITY: 프로덕션 환경에서 HTTPS 사용 확인
if (import.meta.env.PROD && API_BASE_URL.startsWith('http://') && !API_BASE_URL.includes('localhost')) {
  console.warn('[SECURITY] Production environment should use HTTPS for API calls');
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, // SECURITY: 15초 타임아웃 설정
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
