# 프론트엔드 디버깅 리스트 📋

**프로젝트:** auto-dashboard Frontend
**날짜:** 2025-12-12
**분석 결과:** 백엔드 API와 프론트엔드 코드 비교 분석

---

## 🔴 Critical (즉시 수정 필요)

### 1. `/auth/me` 엔드포인트 미구현

- **파일:** `frontend/src/api/auth.js:32`
- **문제:** `getCurrentUser()` 함수가 `/auth/me` 엔드포인트를 호출하지만, 백엔드에 해당 엔드포인트가 없음
- **영향:** 사용자 정보 조회 실패, 설정 페이지 오류 가능
- **해결책:**
  - 백엔드에 `/auth/me` 엔드포인트 추가, 또는
  - 프론트엔드에서 해당 함수 제거/수정 (JWT 토큰에서 정보 추출)

```javascript
// 현재 코드 (문제)
getCurrentUser: async () => {
  const response = await apiClient.get('/auth/me');
  return response.data;
},
```

### 2. API 키 저장 시 `exchange` 필드 누락

- **파일:** `frontend/src/api/account.js:25-31`
- **문제:** `saveApiKeys()`에서 `exchange` 필드가 누락되어 있음
- **백엔드 요구사항:** `exchange`, `api_key`, `secret_key`, `passphrase` 모두 필수
- **해결책:** `exchange` 파라미터 추가

```javascript
// 현재 코드 (문제)
saveApiKeys: async (apiKey, secretKey, passphrase = '') => {
  const response = await apiClient.post('/account/save_keys', {
    api_key: apiKey,
    secret_key: secretKey,
    passphrase: passphrase
    // ❌ exchange 필드 누락!
  });
}

// 수정 필요
saveApiKeys: async (exchange, apiKey, secretKey, passphrase = '') => {
  const response = await apiClient.post('/account/save_keys', {
    exchange: exchange,       // ✅ 추가
    api_key: apiKey,
    secret_key: secretKey,
    passphrase: passphrase
  });
}
```

---

## 🟠 High (빠른 시일 내 수정)

### 3. 주문 API `side` 값 불일치 가능성

- **파일:** `frontend/src/api/order.js:5-14`
- **문제:** 프론트엔드에서 `side` 값으로 무엇을 전달하는지 확인 필요
- **백엔드 요구사항:** `side`는 `"long"` 또는 `"short"` (not `"buy"`/`"sell"`)
- **확인 필요:** Trading 페이지에서 전달하는 `side` 값 검증

### 4. 주문 API `qty` vs `amount` 필드명 불일치

- **파일:** `frontend/src/api/order.js:5-14`
- **현재:** 프론트엔드는 `qty` 사용
- **백엔드:** `amount` 필드 사용 가능성 있음 (확인 필요)
- **확인 필요:** 백엔드 OrderRequest 스키마 검증

### 5. WebSocket 연결 상태 관리

- **파일:** `frontend/src/context/WebSocketContext.jsx`
- **확인 필요:**
  - WebSocket 재연결 로직
  - 연결 끊김 시 사용자 알림
  - 토큰 만료 시 WebSocket 재인증

### 6. 401 에러 시 Refresh Token 미사용

- **파일:** `frontend/src/api/client.js:33-42`
- **현재 동작:** 401 에러 시 즉시 로그아웃 및 로그인 페이지 리다이렉트
- **개선 필요:** 401 발생 시 먼저 Refresh Token으로 재인증 시도

```javascript
// 현재 코드 (개선 필요)
if (error.response?.status === 401) {
  localStorage.removeItem('token');
  window.location.href = '/login';  // 바로 로그아웃
}

// 개선 코드
if (error.response?.status === 401) {
  // 먼저 refresh token으로 재시도
  const refreshToken = localStorage.getItem('refreshToken');
  if (refreshToken) {
    try {
      const newToken = await authAPI.refreshToken(refreshToken);
      // 새 토큰으로 원래 요청 재시도
    } catch {
      // refresh도 실패하면 로그아웃
    }
  }
}
```

---

## 🟡 Medium (개선 권장)

### 7. 에러 핸들링 일관성 부족

- **위치:** 모든 API 파일들
- **문제:** 일부 API 호출에서 에러 처리가 누락되어 있음
- **확인 필요:**
  - `try-catch` 블록 일관성
  - 사용자 친화적 에러 메시지
  - 네트워크 오류 처리

### 8. 그리드 봇 API 엔드포인트 확인

- **파일:** `frontend/src/api/gridBot.js`
- **확인 필요:**
  - `/grid/list` 엔드포인트 존재 여부
  - `/grid/create` 엔드포인트 존재 여부
  - 봇 제어 엔드포인트 경로 검증

### 9. 봇 인스턴스 API 확인

- **파일:** `frontend/src/api/botInstances.js`
- **확인 필요:**
  - Bot Instances 관련 엔드포인트 존재 여부
  - API 스키마 일치 여부

### 10. 차트 데이터 응답 형식 처리

- **파일:** `frontend/src/api/chart.js`
- **확인 필요:**
  - `/chart/candles/{symbol}` 응답이 `{ candles: [...] }` 형식
  - 차트 컴포넌트에서 올바르게 파싱하는지 확인

---

## 🔵 Low (향후 개선)

### 11. 페이지별 검증 필요

| 페이지 | 파일 | 확인 사항 |
|--------|------|----------|
| Login | `Login.jsx` | 회원가입 폼 필드 (name, phone, password_confirm) |
| Dashboard | `Dashboard.jsx` | 데이터 로딩 상태, 에러 처리 |
| Trading | `Trading.jsx` | 주문 폼 side 값, 수량 필드명 |
| Settings | `Settings.jsx` | API 키 저장 시 exchange 필드 |
| BotManagement | `BotManagement.jsx` | 봇 시작 시 strategy_id 필수 |
| Backtesting | `BacktestingPage.jsx` | 백테스트 API 스키마 |

### 12. 컴포넌트 검증 필요

| 컴포넌트 | 파일 | 확인 사항 |
|----------|------|----------|
| TradingChart | `TradingChart.jsx` | 캔들 데이터 형식 처리 |
| PositionList | `PositionList.jsx` | 포지션 데이터 형식 |
| BalanceCard | `BalanceCard.jsx` | 잔고 API 응답 형식 |
| ConnectionStatus | `ConnectionStatus.jsx` | WebSocket 상태 표시 |

### 13. 환경 변수 검증

- **파일:** `frontend/.env`, `frontend/.env.production`
- **확인 필요:**
  - `VITE_API_URL` 설정
  - 프로덕션 vs 개발 환경 설정

---

## 📝 디버깅 체크리스트

### 즉시 확인 항목

- [ ] `/auth/me` 엔드포인트 동작 확인
- [ ] API 키 저장 시 exchange 필드 추가
- [ ] 주문 API side 값 확인 (long/short)

### 기능 테스트

- [ ] 로그인 → 대시보드 이동
- [ ] 대시보드 데이터 로딩
- [ ] 설정 페이지 → API 키 저장
- [ ] 트레이딩 페이지 → 주문 제출
- [ ] 봇 시작/중지
- [ ] 차트 데이터 표시

### 에러 케이스 테스트

- [ ] 잘못된 자격 증명으로 로그인
- [ ] 토큰 만료 후 API 호출
- [ ] API 키 없이 거래 시도
- [ ] 네트워크 끊김 시 동작

---

## 🛠️ 권장 수정 순서

1. **Critical** - `/auth/me` 및 API 키 저장 수정
2. **High** - 401 에러 핸들링 개선
3. **페이지 테스트** - Settings.jsx에서 API 키 저장 테스트
4. **Trading 테스트** - 주문 side 값 및 필드명 확인
5. **전체 흐름 테스트** - 로그인 → 설정 → 거래 → 봇 시작

---

*이 문서는 백엔드 API와 프론트엔드 코드 비교 분석을 기반으로 작성되었습니다.*
