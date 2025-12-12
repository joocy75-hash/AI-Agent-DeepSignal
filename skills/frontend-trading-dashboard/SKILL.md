# Frontend Trading Dashboard Skill

> AI 자동매매 플랫폼 프론트엔드 개발을 위한 완벽 가이드

## Description

이 스킬은 다음 상황에서 사용합니다:

- React 기반 거래 대시보드 컴포넌트 개발
- 실시간 차트 및 데이터 시각화 구현
- 주문 폼, 잔고 표시 등 거래 UI 개발
- WebSocket 실시간 데이터 연동
- 상태 관리 및 API 통신 구현
- **다중 봇 관리 UI 개발**
- **2FA 인증 UI 구현**
- **Refresh Token 자동 갱신**

**트리거 키워드**: "대시보드", "차트 컴포넌트", "거래 UI", "실시간 데이터", "프론트엔드", "React", "봇 관리", "2FA"

---

## 📌 최신 업데이트 (2025-12-12)

### ✅ 완료된 작업

- **Refresh Token 연동** 완료 (`context/AuthContext.jsx`)
  - 로그인 시 refresh_token 저장
  - 토큰 만료 5분 전 자동 갱신
  - 4분마다 주기적 체크
- **봇 관리 페이지** 구현 완료 (`pages/BotManagement.jsx`)
- **2FA 설정 UI** 구현 (`components/settings/TwoFactorSetup.jsx`)
- **Ant Design 기반 다크 테마** 적용

### 📎 참조 문서

- 차트 시그널 마커 가이드 → `docs/CHART_SIGNAL_MARKERS_GUIDE.md`
- 보안 강화 가이드 → `docs/SECURITY_PRIORITY_TASKS.md`
- 배포 전 점검 → `docs/PRE_DEPLOYMENT_AUDIT.md`

---

## 1. 프로젝트 구조

```
frontend/src/
├── components/           # 재사용 가능 컴포넌트
│   ├── layout/          # MainLayout (사이드바, 헤더)
│   │   └── MainLayout.jsx
│   ├── dashboard/       # 대시보드 컴포넌트
│   │   ├── BalanceCard.jsx
│   │   └── StatsCard.jsx
│   ├── bot/             # ⭐ 봇 관리 컴포넌트
│   │   ├── AllocationBar.jsx    # 잔고 할당 시각화
│   │   ├── BotCard.jsx          # 봇 카드
│   │   ├── AddBotCard.jsx       # 봇 추가 + 생성 모달
│   │   ├── BotStatsModal.jsx    # 봇 통계 모달
│   │   └── EditBotModal.jsx     # 봇 편집 모달
│   ├── settings/        # 설정 컴포넌트
│   │   ├── ApiKeySettings.jsx
│   │   ├── RiskSettings.jsx
│   │   └── TwoFactorSetup.jsx   # ⭐ 2FA 설정
│   ├── realtime/        # 실시간 컴포넌트
│   └── backtest/        # 백테스트 컴포넌트
├── pages/               # 페이지 컴포넌트 (Lazy Loaded)
│   ├── Dashboard.jsx    # 메인 대시보드
│   ├── Trading.jsx      # 거래 페이지 (차트 + 주문)
│   ├── BotManagement.jsx # ⭐ 봇 관리 페이지
│   ├── Settings.jsx     # 설정
│   └── BacktestingPage.jsx # 백테스트
├── api/                 # API 통신 모듈 (15개)
│   ├── client.js        # Axios 클라이언트 (인터셉터)
│   ├── auth.js          # ⭐ 인증 API + 2FA API + Refresh Token
│   ├── botInstances.js  # 봇 인스턴스 API
│   ├── account.js       # 계정/잔고 API
│   ├── bitget.js        # Bitget 마켓 API
│   ├── chart.js         # 차트 데이터 API
│   ├── annotations.js   # 어노테이션 API
│   └── ...
├── context/             # React Context (상태 관리)
│   ├── AuthContext.jsx  # ⭐ 인증 상태 (Refresh Token 포함)
│   └── StrategyContext.jsx # 전략 상태
└── hooks/               # 커스텀 훅
```

---

## 2. 기술 스택

| 기술 | 버전 | 용도 |
|------|------|------|
| **React** | 18.x | UI 라이브러리 |
| **Vite** | 5.x | 빌드 도구 |
| **Ant Design** | 5.x | UI 컴포넌트 |
| **Axios** | 1.x | HTTP 클라이언트 |
| **Lightweight Charts** | 4.x | 캔들스틱 차트 |
| **Recharts** | 2.x | 통계 차트 |
| **React Router** | 6.x | 라우팅 |

---

## 3. 인증 시스템 (Refresh Token 포함)

### 3.1 AuthContext (업데이트됨)

```jsx
// context/AuthContext.jsx
import { createContext, useState, useContext, useEffect, useCallback } from 'react';
import { authAPI } from '../api/auth';

// 토큰 디코딩
const decodeToken = (token) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    return JSON.parse(atob(base64));
  } catch {
    return null;
  }
};

// 토큰 만료 임박 확인 (5분 버퍼)
const isTokenExpiringSoon = (token) => {
  const payload = decodeToken(token);
  if (!payload?.exp) return true;
  
  const expirationTime = payload.exp * 1000;
  const bufferTime = 5 * 60 * 1000; // 5분
  return Date.now() > (expirationTime - bufferTime);
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(null);
  const [refreshToken, setRefreshToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // ⭐ 토큰 갱신 함수
  const refreshAccessToken = useCallback(async () => {
    const storedRefreshToken = localStorage.getItem('refreshToken');
    if (!storedRefreshToken) return null;

    try {
      console.log('[Auth] Refreshing access token...');
      const response = await authAPI.refreshToken(storedRefreshToken);
      
      if (response.access_token) {
        localStorage.setItem('token', response.access_token);
        setToken(response.access_token);
        
        // 새 refresh token이 있으면 갱신
        if (response.refresh_token) {
          localStorage.setItem('refreshToken', response.refresh_token);
          setRefreshToken(response.refresh_token);
        }
        
        console.log('[Auth] Token refreshed successfully');
        return response.access_token;
      }
    } catch (error) {
      console.error('[Auth] Token refresh failed:', error);
      logout();
      return null;
    }
  }, []);

  // 초기화: 저장된 토큰 로드
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    const storedRefreshToken = localStorage.getItem('refreshToken');
    const userEmail = localStorage.getItem('userEmail');
    const userId = localStorage.getItem('userId');
    const userRole = localStorage.getItem('userRole');

    if (storedToken && userEmail) {
      // 토큰 만료 확인
      if (isTokenExpiringSoon(storedToken) && storedRefreshToken) {
        refreshAccessToken();
      }

      setUser({ id: parseInt(userId), email: userEmail, role: userRole || 'user' });
      setToken(storedToken);
      setRefreshToken(storedRefreshToken);
      setLoading(false);
    } else {
      setLoading(false);
    }
  }, [refreshAccessToken]);

  // ⭐ 자동 토큰 갱신 (4분마다)
  useEffect(() => {
    if (!token) return;

    const checkAndRefresh = async () => {
      if (isTokenExpiringSoon(token)) {
        await refreshAccessToken();
      }
    };

    const interval = setInterval(checkAndRefresh, 4 * 60 * 1000);
    return () => clearInterval(interval);
  }, [token, refreshAccessToken]);

  // 로그인 (refresh_token 저장)
  const login = async (email, password, totpCode = null) => {
    const data = await authAPI.login(email, password, totpCode);

    if (data.requires_2fa) {
      return { requires_2fa: true, user_id: data.user_id };
    }

    const newToken = data.access_token;
    const newRefreshToken = data.refresh_token;  // ⭐ 새로 추가

    const payload = decodeToken(newToken);
    
    localStorage.setItem('token', newToken);
    localStorage.setItem('userEmail', email);
    localStorage.setItem('userId', payload?.user_id);
    
    if (newRefreshToken) {
      localStorage.setItem('refreshToken', newRefreshToken);
      setRefreshToken(newRefreshToken);
    }
    
    if (payload?.role) {
      localStorage.setItem('userRole', payload.role);
    }

    setUser({ id: payload?.user_id, email, role: payload?.role || 'user' });
    setToken(newToken);
    return { success: true };
  };

  // 로그아웃 (모든 토큰 제거)
  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');  // ⭐ 새로 추가
    localStorage.removeItem('userEmail');
    localStorage.removeItem('userId');
    localStorage.removeItem('userRole');
    setUser(null);
    setToken(null);
    setRefreshToken(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      refreshToken,
      login,
      logout,
      loading,
      isAuthenticated: !!user,
      refreshAccessToken,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
};
```

### 3.2 인증 API (auth.js)

```javascript
// api/auth.js
import apiClient from './client';

export const authAPI = {
  // 로그인 (access_token + refresh_token 반환)
  login: async (email, password, totpCode = null) => {
    const payload = { email, password };
    if (totpCode) payload.totp_code = totpCode;
    const response = await apiClient.post('/auth/login', payload);
    return response.data;
    // 응답: { access_token, refresh_token, token_type }
  },

  // ⭐ Refresh Token으로 Access Token 갱신
  refreshToken: async (refreshToken) => {
    const response = await apiClient.post('/auth/refresh', {
      refresh_token: refreshToken
    });
    return response.data;
    // 응답: { access_token, refresh_token?, token_type }
  },

  register: async (email, password, passwordConfirm, name, phone) => {
    const response = await apiClient.post('/auth/register', {
      email, password, password_confirm: passwordConfirm, name, phone
    });
    return response.data;
  },

  changePassword: async (currentPassword, newPassword) => {
    const response = await apiClient.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },
};

// 2FA API
export const twoFactorAPI = {
  getStatus: () => apiClient.get('/auth/2fa/status').then(r => r.data),
  setup: () => apiClient.post('/auth/2fa/setup').then(r => r.data),
  verify: (code) => apiClient.post('/auth/2fa/verify', { code }).then(r => r.data),
  disable: (code, password) => apiClient.post('/auth/2fa/disable', { code, password }).then(r => r.data),
};
```

---

## 4. 다크 테마 스타일

### 4.1 색상 팔레트

```css
/* index.css */
:root {
  --bg-primary: #0d0d14;      /* 메인 배경 */
  --bg-secondary: #1a1a2e;    /* 카드 배경 */
  --bg-tertiary: #16213e;     /* 입력 필드 배경 */
  --border-color: #2d2d44;    /* 테두리 */
  --text-primary: #ffffff;    /* 주요 텍스트 */
  --text-secondary: #a0a0b0;  /* 보조 텍스트 */
  --accent-green: #00d26a;    /* 수익/상승 */
  --accent-red: #ff4757;      /* 손실/하락 */
  --accent-blue: #5c7cfa;     /* 강조/링크 */
}
```

### 4.2 Ant Design 다크 테마 오버라이드

```css
/* Ant Design 컴포넌트 다크 테마 */
.ant-card {
  background: var(--bg-secondary) !important;
  border-color: var(--border-color) !important;
}

.ant-modal-content {
  background: var(--bg-secondary) !important;
}

.ant-input, .ant-select-selector, .ant-input-number {
  background: var(--bg-tertiary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}

.ant-btn-primary {
  background: var(--accent-blue) !important;
  border-color: var(--accent-blue) !important;
}
```

---

## 5. API 클라이언트

### 5.1 기본 클라이언트 (client.js)

```javascript
// api/client.js
import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

// Request: 토큰 자동 추가
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

// Response: 401 시 로그아웃 또는 토큰 갱신
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Refresh Token 시도 로직은 AuthContext에서 처리
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
```

### 5.2 봇 인스턴스 API

```javascript
// api/botInstances.js
import apiClient from './client';

const botInstancesAPI = {
  list: () => apiClient.get('/bot-instances/list').then(r => r.data),
  
  create: (data) => apiClient.post('/bot-instances/create', data).then(r => r.data),
  get: (botId) => apiClient.get(`/bot-instances/${botId}`).then(r => r.data),
  update: (botId, data) => apiClient.patch(`/bot-instances/${botId}`, data).then(r => r.data),
  delete: (botId) => apiClient.delete(`/bot-instances/${botId}`).then(r => r.data),
  
  start: (botId) => apiClient.post(`/bot-instances/${botId}/start`).then(r => r.data),
  stop: (botId) => apiClient.post(`/bot-instances/${botId}/stop`).then(r => r.data),
  startAll: () => apiClient.post('/bot-instances/start-all').then(r => r.data),
  stopAll: () => apiClient.post('/bot-instances/stop-all').then(r => r.data),
  
  getStats: (botId) => apiClient.get(`/bot-instances/${botId}/stats`).then(r => r.data),
  getSummary: () => apiClient.get('/bot-instances/stats/summary').then(r => r.data),
};

export default botInstancesAPI;
```

---

## 6. 컴포넌트 패턴

### 6.1 BotCard 컴포넌트

```jsx
// components/bot/BotCard.jsx
import { Card, Tag, Button, Tooltip, Popconfirm } from 'antd';
import { 
  PlayCircleOutlined, PauseCircleOutlined, 
  EditOutlined, DeleteOutlined, LineChartOutlined 
} from '@ant-design/icons';

const BotCard = ({ bot, onStart, onStop, onEdit, onDelete, onViewStats }) => {
  const isRunning = bot.is_running;
  const pnl = bot.total_pnl || 0;
  const pnlColor = pnl >= 0 ? '#00d26a' : '#ff4757';

  return (
    <Card
      style={{
        background: '#1a1a2e',
        border: isRunning ? '1px solid #00d26a' : '1px solid #2d2d44',
        boxShadow: isRunning ? '0 0 10px rgba(0, 210, 106, 0.3)' : 'none',
      }}
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ color: '#fff' }}>{bot.name}</span>
          <Tag color={bot.bot_type === 'ai_trend' ? 'blue' : 'purple'}>
            {bot.bot_type === 'ai_trend' ? 'AI 추세' : '그리드'}
          </Tag>
          {isRunning && <Tag color="green">실행 중</Tag>}
        </div>
      }
      actions={[
        isRunning ? (
          <Tooltip title="중지">
            <Button icon={<PauseCircleOutlined />} onClick={() => onStop(bot.id)} />
          </Tooltip>
        ) : (
          <Tooltip title="시작">
            <Button icon={<PlayCircleOutlined />} onClick={() => onStart(bot.id)} />
          </Tooltip>
        ),
        <Tooltip title="통계">
          <Button icon={<LineChartOutlined />} onClick={() => onViewStats(bot.id)} />
        </Tooltip>,
        <Tooltip title="편집">
          <Button icon={<EditOutlined />} onClick={() => onEdit(bot)} />
        </Tooltip>,
        <Popconfirm title="삭제하시겠습니까?" onConfirm={() => onDelete(bot.id)}>
          <Button icon={<DeleteOutlined />} danger />
        </Popconfirm>,
      ]}
    >
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div>
          <span style={{ color: '#a0a0b0', fontSize: 12 }}>PNL</span>
          <div style={{ color: pnlColor, fontSize: 18, fontWeight: 600 }}>
            {pnl >= 0 ? '+' : ''}{pnl.toFixed(2)} USDT
          </div>
        </div>
        <div>
          <span style={{ color: '#a0a0b0', fontSize: 12 }}>승률</span>
          <div style={{ color: '#fff', fontSize: 18, fontWeight: 600 }}>
            {(bot.win_rate || 0).toFixed(1)}%
          </div>
        </div>
        <div>
          <span style={{ color: '#a0a0b0', fontSize: 12 }}>심볼</span>
          <div style={{ color: '#fff' }}>{bot.symbol}</div>
        </div>
        <div>
          <span style={{ color: '#a0a0b0', fontSize: 12 }}>할당</span>
          <div style={{ color: '#fff' }}>{bot.allocation_percent}%</div>
        </div>
      </div>
    </Card>
  );
};

export default BotCard;
```

### 6.2 AllocationBar 컴포넌트

```jsx
// components/bot/AllocationBar.jsx
import { Tooltip } from 'antd';

const COLORS = ['#5c7cfa', '#00d26a', '#ffd43b', '#ff6b6b', '#cc5de8', '#20c997'];

const AllocationBar = ({ bots, totalAllocation }) => {
  const available = 100 - totalAllocation;

  return (
    <div style={{ marginBottom: 24 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
        <span style={{ color: '#a0a0b0' }}>잔고 할당</span>
        <span style={{ color: '#fff' }}>{totalAllocation.toFixed(1)}% 사용 중</span>
      </div>
      
      <div style={{ 
        display: 'flex', 
        height: 24, 
        borderRadius: 12, 
        overflow: 'hidden',
        background: '#2d2d44',
      }}>
        {bots.map((bot, i) => (
          <Tooltip key={bot.id} title={`${bot.name}: ${bot.allocation_percent}%`}>
            <div
              style={{
                width: `${bot.allocation_percent}%`,
                background: COLORS[i % COLORS.length],
                transition: 'width 0.3s',
              }}
            />
          </Tooltip>
        ))}
      </div>
    </div>
  );
};

export default AllocationBar;
```

---

## 7. 차트 구현

### 7.1 캔들스틱 차트 (Lightweight Charts)

```jsx
// components/TradingChart.jsx
import { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';
import apiClient from '../api/client';

const TradingChart = ({ symbol, interval = '15m' }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: 400,
      layout: {
        background: { type: 'solid', color: '#0d0d14' },
        textColor: '#a0a0b0',
      },
      grid: {
        vertLines: { color: '#2d2d44' },
        horzLines: { color: '#2d2d44' },
      },
      crosshair: { mode: 1 },
      timeScale: { timeVisible: true, borderColor: '#2d2d44' },
      rightPriceScale: { borderColor: '#2d2d44' },
    });

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#00d26a',
      downColor: '#ff4757',
      borderDownColor: '#ff4757',
      borderUpColor: '#00d26a',
      wickDownColor: '#ff4757',
      wickUpColor: '#00d26a',
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    const handleResize = () => {
      chart.applyOptions({ width: chartContainerRef.current.clientWidth });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, []);

  // 데이터 로드
  useEffect(() => {
    const fetchCandles = async () => {
      try {
        const response = await apiClient.get('/chart/candles', {
          params: { symbol, interval, limit: 500 }
        });

        const candles = response.data.map(c => ({
          time: c.timestamp / 1000,
          open: parseFloat(c.open),
          high: parseFloat(c.high),
          low: parseFloat(c.low),
          close: parseFloat(c.close),
        }));

        candleSeriesRef.current?.setData(candles);
      } catch (err) {
        console.error('Failed to fetch candles:', err);
      }
    };

    if (candleSeriesRef.current) fetchCandles();
  }, [symbol, interval]);

  return (
    <div
      ref={chartContainerRef}
      style={{ width: '100%', height: 400, borderRadius: 8, overflow: 'hidden' }}
    />
  );
};

export default TradingChart;
```

### 7.2 시그널 마커 추가

> 상세 구현: `docs/CHART_SIGNAL_MARKERS_GUIDE.md`

```jsx
// 거래 내역을 마커로 표시
const markers = trades.map(t => ({
  time: t.created_at / 1000,
  position: t.side === 'long' ? 'belowBar' : 'aboveBar',
  color: t.side === 'long' ? '#00d26a' : '#ff4757',
  shape: t.side === 'long' ? 'arrowUp' : 'arrowDown',
  text: `${t.side === 'long' ? 'L' : 'S'} ${t.entry_price}`,
}));

candleSeriesRef.current?.setMarkers(markers);
```

---

## 8. 환경 변수

```bash
# .env.production
VITE_API_URL=https://your-domain.com/api
VITE_WS_URL=wss://your-domain.com/ws

# .env.development
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

---

## 9. 빌드 및 배포

```bash
# 개발 서버
npm run dev

# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

---

## 10. 참조 문서

| 문서 | 위치 | 설명 |
|------|------|------|
| 배포 전 점검 | `docs/PRE_DEPLOYMENT_AUDIT.md` | ⭐ 전체 점검 리포트 |
| 차트 마커 가이드 | `docs/CHART_SIGNAL_MARKERS_GUIDE.md` | 차트 시그널 |
| 보안 작업 목록 | `docs/SECURITY_PRIORITY_TASKS.md` | 보안 작업 |
| 다중 봇 설계 | `docs/MULTI_BOT_01_OVERVIEW.md` | 다중 봇 시스템 |
