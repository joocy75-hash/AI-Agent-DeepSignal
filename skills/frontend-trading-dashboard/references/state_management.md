# 상태 관리 패턴 참조

## Context 기반 상태 관리

### 현재 프로젝트의 Context 구조

```
context/
├── AuthContext.jsx       # 인증 상태
├── ThemeContext.jsx      # 테마 (라이트/다크)
├── WebSocketContext.jsx  # WebSocket 연결
└── StrategyContext.jsx   # 전략 상태
```

---

## AuthContext (인증)

### 구조

```jsx
const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);       // {id, email, role}
  const [token, setToken] = useState(null);     // JWT 토큰
  const [loading, setLoading] = useState(true); // 초기 로드 중

  // localStorage에서 토큰 복원
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const userEmail = localStorage.getItem('userEmail');

    if (storedToken && userEmail) {
      const payload = decodeToken(storedToken);
      setUser({
        id: payload.user_id,
        email: userEmail,
        role: payload.role || 'user'
      });
      setToken(storedToken);
    }
    setLoading(false);
  }, []);

  const login = async (email, password, totpCode = null) => {
    const data = await authAPI.login(email, password, totpCode);

    // 2FA 필요
    if (data.requires_2fa) {
      return { requires_2fa: true, user_id: data.user_id };
    }

    // 토큰 저장
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('userEmail', email);

    const payload = decodeToken(data.access_token);
    setUser({
      id: payload.user_id,
      email,
      role: payload.role || 'user'
    });
    setToken(data.access_token);

    return { success: true };
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userEmail');
    setUser(null);
    setToken(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      login,
      logout,
      loading,
      isAuthenticated: !!user,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};
```

### 사용 예

```jsx
// 컴포넌트에서 사용
const MyComponent = () => {
  const { user, isAuthenticated, logout } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" />;
  }

  return (
    <div>
      <p>Welcome, {user.email}</p>
      <button onClick={logout}>로그아웃</button>
    </div>
  );
};
```

---

## Protected Route 패턴

```jsx
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (!isAuthenticated) {
    // 로그인 후 원래 페이지로 리다이렉트하기 위해 현재 위치 저장
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
};

// 사용
<Route
  path="/dashboard"
  element={
    <ProtectedRoute>
      <Dashboard />
    </ProtectedRoute>
  }
/>
```

---

## Admin Route 패턴

```jsx
const AdminRoute = ({ children }) => {
  const { user, isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <LoadingSpinner size="lg" />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (user.role !== 'admin') {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-400">접근 권한 없음</h1>
          <p className="text-gray-400 mt-2">관리자만 접근할 수 있습니다</p>
        </div>
      </div>
    );
  }

  return children;
};
```

---

## 새 Context 생성 템플릿

```jsx
// context/NewContext.jsx
import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import apiClient from '../api/client';

const NewContext = createContext(null);

export const NewProvider = ({ children }) => {
  // 상태
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 데이터 페칭
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get('/api/data');
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.message || err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  // 데이터 추가
  const addItem = useCallback(async (item) => {
    try {
      const response = await apiClient.post('/api/data', item);
      setData(prev => [...prev, response.data]);
      return { success: true, data: response.data };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  // 데이터 수정
  const updateItem = useCallback(async (id, updates) => {
    try {
      const response = await apiClient.put(`/api/data/${id}`, updates);
      setData(prev => prev.map(item =>
        item.id === id ? response.data : item
      ));
      return { success: true, data: response.data };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  // 데이터 삭제
  const deleteItem = useCallback(async (id) => {
    try {
      await apiClient.delete(`/api/data/${id}`);
      setData(prev => prev.filter(item => item.id !== id));
      return { success: true };
    } catch (err) {
      return { success: false, error: err.message };
    }
  }, []);

  // 초기 로드
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const value = {
    data,
    loading,
    error,
    fetchData,
    addItem,
    updateItem,
    deleteItem,
  };

  return (
    <NewContext.Provider value={value}>
      {children}
    </NewContext.Provider>
  );
};

export const useNew = () => {
  const context = useContext(NewContext);
  if (!context) {
    throw new Error('useNew must be used within NewProvider');
  }
  return context;
};
```

---

## 커스텀 훅 패턴

### useAsync - 비동기 작업 관리

```jsx
const useAsync = (asyncFn, immediate = true) => {
  const [state, setState] = useState({
    data: null,
    loading: immediate,
    error: null,
  });

  const execute = useCallback(async (...args) => {
    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      const data = await asyncFn(...args);
      setState({ data, loading: false, error: null });
      return { success: true, data };
    } catch (error) {
      setState({ data: null, loading: false, error });
      return { success: false, error };
    }
  }, [asyncFn]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, []);

  return { ...state, execute };
};

// 사용
const { data, loading, error, execute } = useAsync(
  () => apiClient.get('/api/data'),
  true
);
```

### useLocalStorage - 로컬 스토리지 동기화

```jsx
const useLocalStorage = (key, initialValue) => {
  const [storedValue, setStoredValue] = useState(() => {
    try {
      const item = localStorage.getItem(key);
      return item ? JSON.parse(item) : initialValue;
    } catch (error) {
      return initialValue;
    }
  });

  const setValue = useCallback((value) => {
    try {
      const valueToStore = value instanceof Function ? value(storedValue) : value;
      setStoredValue(valueToStore);
      localStorage.setItem(key, JSON.stringify(valueToStore));
    } catch (error) {
      console.error('Error saving to localStorage:', error);
    }
  }, [key, storedValue]);

  return [storedValue, setValue];
};

// 사용
const [settings, setSettings] = useLocalStorage('userSettings', {
  theme: 'dark',
  notifications: true,
});
```

### useDebounce - 디바운스

```jsx
const useDebounce = (value, delay = 300) => {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
};

// 사용 (검색)
const [searchTerm, setSearchTerm] = useState('');
const debouncedSearch = useDebounce(searchTerm, 500);

useEffect(() => {
  if (debouncedSearch) {
    searchAPI(debouncedSearch);
  }
}, [debouncedSearch]);
```

### useInterval - 주기적 실행

```jsx
const useInterval = (callback, delay) => {
  const savedCallback = useRef();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    if (delay === null) return;

    const tick = () => savedCallback.current();
    const id = setInterval(tick, delay);

    return () => clearInterval(id);
  }, [delay]);
};

// 사용 (폴링)
useInterval(() => {
  fetchBotStatus();
}, 5000);
```

---

## 상태 업데이트 패턴

### 낙관적 업데이트 (Optimistic Update)

```jsx
const deleteItemOptimistic = async (id) => {
  // 1. 현재 상태 백업
  const previousItems = [...items];

  // 2. UI 즉시 업데이트 (낙관적)
  setItems(prev => prev.filter(item => item.id !== id));

  try {
    // 3. API 호출
    await apiClient.delete(`/api/items/${id}`);
  } catch (error) {
    // 4. 실패 시 롤백
    setItems(previousItems);
    message.error('삭제 실패');
  }
};
```

### 배치 업데이트

```jsx
const updateMultipleItems = async (updates) => {
  // 여러 업데이트를 한 번에 처리
  setItems(prev => {
    const newItems = [...prev];
    updates.forEach(({ id, changes }) => {
      const index = newItems.findIndex(item => item.id === id);
      if (index !== -1) {
        newItems[index] = { ...newItems[index], ...changes };
      }
    });
    return newItems;
  });
};
```
