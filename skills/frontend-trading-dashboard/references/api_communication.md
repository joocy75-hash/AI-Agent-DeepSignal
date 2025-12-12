# API 통신 패턴 참조

## API 클라이언트 설정

### 현재 프로젝트의 클라이언트 (api/client.js)

```javascript
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,  // 15초 타임아웃
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request Interceptor - 토큰 자동 추가
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

// Response Interceptor - 에러 처리
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 401 에러: 토큰 만료
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

---

## API 모듈 패턴

### 인증 API (api/auth.js)

```javascript
import apiClient from './client';

export const authAPI = {
  login: async (email, password, totpCode = null) => {
    const response = await apiClient.post('/auth/login', {
      email,
      password,
      totp_code: totpCode,
    });
    return response.data;
  },

  register: async (email, password, passwordConfirm, name, phone) => {
    const response = await apiClient.post('/auth/register', {
      email,
      password,
      password_confirm: passwordConfirm,
      name,
      phone,
    });
    return response.data;
  },

  changePassword: async (oldPassword, newPassword) => {
    const response = await apiClient.post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
    return response.data;
  },

  // 2FA
  enable2FA: async () => {
    const response = await apiClient.post('/2fa/enable');
    return response.data;
  },

  verify2FA: async (code) => {
    const response = await apiClient.post('/2fa/verify', { code });
    return response.data;
  },

  disable2FA: async () => {
    const response = await apiClient.post('/2fa/disable');
    return response.data;
  },
};
```

### 봇 API (api/bot.js)

```javascript
import apiClient from './client';

export const botAPI = {
  start: async (strategyId) => {
    const response = await apiClient.post('/bot/start', {
      strategy_id: strategyId,
    });
    return response.data;
  },

  stop: async () => {
    const response = await apiClient.post('/bot/stop');
    return response.data;
  },

  getStatus: async () => {
    const response = await apiClient.get('/bot/status');
    return response.data;
  },

  getLogs: async (limit = 100) => {
    const response = await apiClient.get('/bot/logs', {
      params: { limit },
    });
    return response.data;
  },
};
```

### 거래 API (api/trades.js)

```javascript
import apiClient from './client';

export const tradesAPI = {
  list: async (params = {}) => {
    const response = await apiClient.get('/trades', { params });
    return response.data;
  },

  get: async (id) => {
    const response = await apiClient.get(`/trades/${id}`);
    return response.data;
  },

  getStats: async () => {
    const response = await apiClient.get('/trades/stats');
    return response.data;
  },
};
```

### 차트 API (api/chart.js)

```javascript
import apiClient from './client';

export const chartAPI = {
  getCandles: async (symbol, interval = '1h', limit = 500) => {
    const response = await apiClient.get('/chart/candles', {
      params: { symbol, interval, limit },
    });
    return response.data;
  },
};
```

### 백테스트 API (api/backtest.js)

```javascript
import apiClient from './client';

export const backtestAPI = {
  run: async (params) => {
    const response = await apiClient.post('/backtest/run', params);
    return response.data;
  },

  getResult: async (id) => {
    const response = await apiClient.get(`/backtest/result/${id}`);
    return response.data;
  },

  getHistory: async (page = 1, limit = 10) => {
    const response = await apiClient.get('/backtest/history', {
      params: { page, limit },
    });
    return response.data;
  },
};
```

---

## 에러 처리 패턴

### 기본 에러 처리

```javascript
const fetchData = async () => {
  try {
    const response = await apiClient.get('/api/data');
    return response.data;
  } catch (error) {
    // Axios 에러 구조
    if (error.response) {
      // 서버가 응답을 반환 (4xx, 5xx)
      const { status, data } = error.response;

      switch (status) {
        case 400:
          throw new Error(data.error?.message || '잘못된 요청입니다');
        case 401:
          throw new Error('인증이 필요합니다');
        case 403:
          throw new Error('접근 권한이 없습니다');
        case 404:
          throw new Error('리소스를 찾을 수 없습니다');
        case 429:
          throw new Error('요청이 너무 많습니다. 잠시 후 다시 시도하세요');
        case 500:
          throw new Error('서버 오류가 발생했습니다');
        default:
          throw new Error(data.error?.message || '오류가 발생했습니다');
      }
    } else if (error.request) {
      // 요청이 전송되었지만 응답이 없음
      throw new Error('서버에 연결할 수 없습니다');
    } else {
      // 요청 설정 중 오류
      throw new Error(error.message);
    }
  }
};
```

### 에러 핸들링 훅

```javascript
const useAPI = (apiFunction) => {
  const [state, setState] = useState({
    data: null,
    loading: false,
    error: null,
  });

  const execute = useCallback(async (...args) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const data = await apiFunction(...args);
      setState({ data, loading: false, error: null });
      return { success: true, data };
    } catch (error) {
      const errorMessage = error.response?.data?.error?.message
        || error.message
        || '오류가 발생했습니다';

      setState({ data: null, loading: false, error: errorMessage });
      return { success: false, error: errorMessage };
    }
  }, [apiFunction]);

  return { ...state, execute };
};

// 사용
const { data, loading, error, execute } = useAPI(tradesAPI.list);

useEffect(() => {
  execute({ limit: 50 });
}, [execute]);
```

---

## WebSocket 통신

### 연결 관리

```javascript
const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const wsRef = useRef(null);
  const reconnectAttempts = useRef(0);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLastMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);

      // 자동 재연결 (최대 5회)
      if (reconnectAttempts.current < 5) {
        reconnectAttempts.current++;
        setTimeout(connect, 3000 * reconnectAttempts.current);
      }
    };

    wsRef.current = ws;
  }, [url]);

  const send = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return { isConnected, lastMessage, send, disconnect };
};
```

### 사용 예

```jsx
const TradingView = () => {
  const { user, token } = useAuth();
  const wsUrl = `ws://localhost:8000/ws/user/${user.id}?token=${token}`;
  const { isConnected, lastMessage, send } = useWebSocket(wsUrl);

  useEffect(() => {
    if (lastMessage) {
      switch (lastMessage.type) {
        case 'price_update':
          // 가격 업데이트 처리
          break;
        case 'order_filled':
          // 주문 체결 알림
          notification.success({
            message: '주문 체결',
            description: `${lastMessage.symbol} 주문이 체결되었습니다`,
          });
          break;
        case 'bot_log':
          // 봇 로그 처리
          break;
      }
    }
  }, [lastMessage]);

  return (
    <div>
      <ConnectionStatus connected={isConnected} />
      {/* 나머지 UI */}
    </div>
  );
};
```

---

## 요청 최적화

### 요청 취소 (AbortController)

```javascript
const useCancellableRequest = () => {
  const abortControllerRef = useRef(null);

  const makeRequest = useCallback(async (requestFn) => {
    // 이전 요청 취소
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // 새 AbortController 생성
    abortControllerRef.current = new AbortController();

    try {
      const response = await requestFn(abortControllerRef.current.signal);
      return response;
    } catch (error) {
      if (error.name === 'AbortError' || error.name === 'CanceledError') {
        console.log('Request cancelled');
        return null;
      }
      throw error;
    }
  }, []);

  // Cleanup
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return makeRequest;
};

// 사용
const makeRequest = useCancellableRequest();

const search = async (query) => {
  const result = await makeRequest((signal) =>
    apiClient.get('/api/search', {
      params: { q: query },
      signal,
    })
  );
  return result?.data;
};
```

### 요청 캐싱

```javascript
const cache = new Map();

const cachedFetch = async (key, fetchFn, ttl = 60000) => {
  const cached = cache.get(key);

  if (cached && Date.now() - cached.timestamp < ttl) {
    return cached.data;
  }

  const data = await fetchFn();
  cache.set(key, { data, timestamp: Date.now() });
  return data;
};

// 사용
const getMarketData = async (symbol) => {
  return cachedFetch(
    `market_${symbol}`,
    () => apiClient.get(`/market/${symbol}`).then(r => r.data),
    5000  // 5초 캐시
  );
};
```

### 병렬 요청

```javascript
const fetchDashboardData = async () => {
  const [balance, positions, trades] = await Promise.all([
    apiClient.get('/account/balance'),
    apiClient.get('/account/positions'),
    apiClient.get('/trades?limit=10'),
  ]);

  return {
    balance: balance.data,
    positions: positions.data,
    trades: trades.data,
  };
};
```
