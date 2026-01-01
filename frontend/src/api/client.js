import axios from 'axios';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000') + '/api/v1';

// SECURITY: 프로덕션 환경에서 HTTPS 사용 확인
if (import.meta.env.PROD && API_BASE_URL.startsWith('http://')) {
  const allowedHttpHosts = ['localhost', '127.0.0.1', '5.161.112.248'];
  const isAllowedHost = allowedHttpHosts.some(host => API_BASE_URL.includes(host));
  if (!isAllowedHost) {
    throw new Error('[SECURITY] Production environment requires HTTPS for API calls');
  }
  console.warn('[SECURITY] HTTP is used. Consider upgrading to HTTPS for production.');
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000, // SECURITY: 15초 타임아웃 설정
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

const getCookie = (name) => {
  const match = document.cookie.match(new RegExp(`(^|; )${name}=([^;]*)`));
  return match ? decodeURIComponent(match[2]) : null;
};

// Request interceptor to add CSRF token for mutating requests
apiClient.interceptors.request.use(
  (config) => {
    const method = (config.method || 'get').toLowerCase();
    if (!['get', 'head', 'options'].includes(method)) {
      const csrfToken = getCookie('csrf_token');
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 토큰 갱신 중인지 추적
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// Response interceptor to handle errors with token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // 401 에러 시 토큰 갱신 시도
    if (error.response?.status === 401 && !originalRequest._retry) {
      // 이미 갱신 중이면 대기열에 추가
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(() => apiClient(originalRequest)).catch(err => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const csrfToken = getCookie('csrf_token');
        await axios.post(
          `${API_BASE_URL}/auth/refresh`,
          null,
          {
            withCredentials: true,
            headers: csrfToken ? { 'X-CSRF-Token': csrfToken } : {},
          }
        );
        processQueue(null);
        return apiClient(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    return Promise.reject(error);
  }
);

export default apiClient;
