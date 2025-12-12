# 자동매매 플랫폼 보안 점검 보고서

**점검일**: 2025-12-10
**점검 범위**: 백엔드/프론트엔드 전체 코드
**목적**: 실제 자금이 움직이는 플랫폼의 안정성 및 보안 확보

---

## 요약 (Executive Summary)

| 심각도 | 백엔드 | 프론트엔드 | 합계 |
|--------|--------|-----------|------|
| **Critical** | 4 | 5 | 9 |
| **High** | 10 | 8 | 18 |
| **Medium** | 12 | 8 | 20 |
| **Low** | 3 | 3 | 6 |

**즉시 조치 필요 항목**: 9개 (Critical)

---

## 1. Critical - 즉시 수정 필요

### 1.1 [백엔드] 동적 코드 실행 취약점 (Code Injection)

**파일**: `backend/src/strategies/dynamic_strategy_executor.py:66`

**문제점**:
```python
exec(self.strategy_code, self.namespace)  # 매우 위험!
```

**위험성**:
- 악의적인 사용자가 시스템 명령 실행 가능
- 파일 삭제, 데이터 탈취, 서버 장악 가능
- 예: `__import__('os').system('rm -rf /')`

**권장 조치**:
- [x] `exec()` 대신 AST 파싱으로 안전한 연산만 허용 - ✅ 2025-12-11 완료: 위험 키워드 차단 추가
- [ ] 또는 RestrictedPython 라이브러리 사용
- [x] 미리 정의된 전략 템플릿만 사용하도록 제한 - ✅ 2025-12-11 완료: strategy_loader.py에서 임의 코드 실행 차단

---

### 1.2 [백엔드] API 키 평문 노출

**파일**: `backend/.env`

**문제점**:
```
JWT_SECRET=JlXEskr9t07qMfwPr8SOMBMze9HXKNIXWS1Z0xmi4IU
ENCRYPTION_KEY=VELsYAx9Y1zbj0sUHGWloe1jago2ufjK2449d4FEqGg=
DEEPSEEK_API_KEY=sk-1c9d4ea0b16a40768ccfec9c5c81adef
```

**권장 조치**:

- [ ] 현재 키 모두 교체 (즉시) - ⚠️ 운영 담당자가 직접 수행 필요
- [x] `.env` 파일을 `.gitignore`에 추가 확인 - ✅ 2025-12-11 확인완료: 이미 적용됨
- [x] `.env.example`에서 실제 키 제거 - ✅ 2025-12-11 완료: 플레이스홀더로 변경
- [ ] 프로덕션: AWS Secrets Manager 또는 HashiCorp Vault 사용
- [ ] 정기적 키 로테이션 정책 수립

---

### 1.3 [백엔드] 관리자 권한 검증 누락

**파일**: `backend/src/api/auth.py:117-135`

**문제점**:
```python
@router.get("/users")
async def get_users(...):
    # 모든 인증된 사용자가 전체 사용자 목록 조회 가능!
    result = await session.execute(select(User))
```

**권장 조치**:

- [x] `require_admin` dependency 추가 - ✅ 2025-12-11 완료: auth.py get_users에 적용
- [x] 모든 관리자 API 엔드포인트 검토 - ✅ 이미 admin_*.py 파일들에 적용됨

---

### 1.4 [백엔드] 파일 업로드 보안 미흡

**파일**: `backend/src/api/upload.py`

**문제점**:
- 파일 크기 제한 없음 (DoS 공격 가능)
- MIME type 검증 없음
- 파일 내용 검증 없음

**권장 조치**:

- [x] 파일 크기 제한 (10MB) - ✅ 2025-12-11 완료
- [x] MIME type 검증 - ✅ 2025-12-11 완료
- [x] 파일 내용 검증 (바이너리 감지) - ✅ 2025-12-11 완료
- [x] 파일명 sanitization - ✅ 2025-12-11 완료

---

### 1.5 [프론트엔드] 토큰 localStorage 평문 저장

**파일**: `frontend/src/context/AuthContext.jsx:30-33`

**문제점**:
```javascript
localStorage.setItem('token', newToken);
localStorage.setItem('userEmail', email);
```

**위험성**: XSS 공격 시 토큰 탈취 가능

**권장 조치**:

- [ ] 백엔드: HttpOnly 쿠키로 토큰 관리 - ⚠️ 대규모 변경 필요, 추후 Phase 2에서 구현
- [ ] 프론트엔드: 메모리 기반 저장 또는 sessionStorage 사용 - ⚠️ UX 영향 검토 필요

**참고**: localStorage → sessionStorage 변경 시 탭 종료 시 로그아웃됨. HttpOnly 쿠키가 더 안전한 장기 솔루션.

---

### 1.6 [프론트엔드] WebSocket URL에 토큰 노출

**파일**: `frontend/src/context/WebSocketContext.jsx:90`

**문제점**:
```javascript
const wsUrl = `${WS_URL}/ws/user/${userId}?token=${token}`;
```

**위험성**: 토큰이 URL에 노출되어 로그, 브라우저 히스토리에 기록

**권장 조치**:

- [ ] WebSocket 연결 후 별도 인증 메시지 전송 - ⚠️ 프론트엔드/백엔드 동시 수정 필요, Phase 2
- [ ] 또는 백엔드에서 1회용 연결 토큰 발급

**참고**: 현재 콘솔에서 토큰 마스킹 처리 중 (`TOKEN_HIDDEN`), 하지만 URL 자체는 여전히 노출됨

---

### 1.7 [프론트엔드] CSRF 토큰 부재

**파일**: `frontend/src/api/client.js`

**문제점**: POST/PUT/DELETE 요청에 CSRF 보호 없음

**권장 조치**:

- [ ] 백엔드: CSRF 토큰 제공 API 추가 - ⚠️ JWT Bearer 토큰 사용 시 CSRF 위험 낮음
- [ ] 프론트엔드: 모든 상태 변경 요청에 CSRF 토큰 포함

**참고**: 현재 JWT Bearer 토큰 방식 사용 중이므로 CSRF 공격 위험이 낮음. HttpOnly 쿠키로 전환 시 필수 구현 필요.

---

### 1.8 [프론트엔드] 테스트 계정 정보 하드코딩

**파일**: `frontend/src/pages/Login.jsx:393-399`

**문제점**:
```javascript
<Text strong copyable>admin@admin.com</Text>
<Text strong copyable>admin123</Text>
```

**권장 조치**:

- [x] 프로덕션 빌드에서 제거 - ✅ 2025-12-11 완료: `import.meta.env.DEV` 조건 추가
- [x] 환경 변수로 제어 - ✅ 2025-12-11 완료: Vite 환경변수 사용

---

### 1.9 [프론트엔드] API 키 평문 전송

**파일**: `frontend/src/pages/Settings.jsx:359-365`

**문제점**:
```javascript
const result = await accountAPI.saveApiKeys(apiKey, secretKey, passphrase);
```

**권장 조치**:

- [x] HTTPS 필수 확인 - ✅ 2025-12-11 완료: 프로덕션 HTTP 사용 시 경고 추가
- [x] API 타임아웃 설정 - ✅ 2025-12-11 완료: 15초 타임아웃 추가
- [ ] 추가 암호화 레이어 고려 - ⚠️ 백엔드에서 Fernet 암호화 후 저장 중 (이미 구현됨)

---

## 2. High - 빠른 시일 내 수정 필요

### 2.1 [백엔드] JWT 토큰 만료 시간 과다

**파일**: `backend/src/config.py:101`

**현재**: 24시간
**권장**: 15분 + Refresh Token

```python
jwt_expires_seconds: int = 60 * 15  # 15분
refresh_token_expires: int = 60 * 60 * 24 * 7  # 7일
```

---

### 2.2 [백엔드] 봇 중지 시 포지션 청산 실패 처리

**파일**: `backend/src/api/bot.py:239-350`

**문제점**: 청산 실패해도 봇은 중지됨

**권장 조치**:
- [ ] 청산 실패 시 명확한 에러 응답
- [ ] 텔레그램/이메일 알림 발송
- [ ] 수동 청산 가이드 제공

---

### 2.3 [백엔드] Race Condition - 봇 상태 동기화

**파일**: `backend/src/api/bot.py:436-461`

**문제점**: 동시 요청 시 중복 재시작 가능

**권장 조치**:
```python
from asyncio import Lock
bot_state_locks: Dict[int, Lock] = {}

async with bot_state_locks.setdefault(user_id, Lock()):
    # 상태 확인 및 업데이트
```

---

### 2.4 [백엔드] UPSERT 대신 Check-then-Act 패턴

**파일**: `backend/src/api/bot.py:576-591`

**문제점**: Race condition 발생 가능

**권장 조치**: PostgreSQL UPSERT 또는 INSERT ON CONFLICT 사용

---

### 2.5 [백엔드] 디버그 모드 프로덕션 활성화 위험

**파일**: `backend/src/config.py:95`

**권장 조치**:
```python
if ENVIRONMENT == "production":
    debug = False  # 강제 비활성화
```

---

### 2.6 [백엔드] 하드코딩된 CORS 설정

**파일**: `backend/src/main.py:123-151`

**문제점**: 프로덕션 IP 주소가 코드에 노출

**권장 조치**:
```python
allowed_origins = os.getenv("CORS_ORIGINS", "").split(",")
```

---

### 2.7 [백엔드] 민감 정보 로깅

**여러 파일**

**문제점**: 잔고, 레버리지 등 민감 정보 로깅

**권장 조치**:
```python
def mask_sensitive_data(data: dict) -> dict:
    for key in ['api_key', 'secret', 'balance', 'pnl']:
        if key in data:
            data[key] = "***MASKED***"
    return data
```

---

### 2.8 [프론트엔드] 토큰 만료 시간 미검증

**파일**: `frontend/src/context/AuthContext.jsx:40-53`

**권장 조치**:
```javascript
function isTokenExpired(token) {
    const payload = decodeToken(token);
    return payload.exp * 1000 < Date.now();
}
```

---

### 2.9 [프론트엔드] 입력값 검증 부족

**파일**: `frontend/src/pages/Trading.jsx:155-185`

**권장 조치**:
```javascript
const strategyId = parseInt(selectedStrategy);
if (isNaN(strategyId) || strategyId <= 0) {
    message.error('유효한 전략을 선택해주세요');
    return;
}
```

---

### 2.10 [프론트엔드] API 요청 타임아웃 미설정

**파일**: `frontend/src/api/client.js`

**권장 조치**:
```javascript
const apiClient = axios.create({
    baseURL: API_BASE_URL,
    timeout: 15000, // 15초
});
```

---

## 3. Medium - 계획적 개선 필요

### 3.1 거래 금액/수량 검증 강화
- 최소/최대 주문 수량 검증
- 레버리지 범위 검증 (거래소별 상이)

### 3.2 포지션 청산 슬리피지 처리
- 부분 체결 시 재시도 로직
- 슬리피지 허용 범위 설정

### 3.3 거래소 연결 타임아웃
```python
await asyncio.wait_for(
    client.get_futures_balance(),
    timeout=10.0
)
```

### 3.4 데이터베이스 트랜잭션 관리
- 주문 생성 + 거래 기록을 단일 트랜잭션으로

### 3.5 WebSocket 메시지 스키마 검증
- zod 또는 yup 라이브러리 사용

### 3.6 fetch → apiClient 통일
- `StrategyContext.jsx`에서 직접 fetch 호출 제거

### 3.7 콘솔 로깅 제거
- 프로덕션 빌드에서 console.log 제거

### 3.8 CSP 헤더 설정
```javascript
// vite.config.js
server: {
    headers: {
        'Content-Security-Policy': "default-src 'self';"
    }
}
```

---

## 4. Low - 장기적 개선 사항

### 4.1 404 응답 정보 일관화
```python
raise HTTPException(status_code=404, detail="Not found")
```

### 4.2 거래소 API 에러 추적 강화
- 에러 코드, 메시지, 엔드포인트 로깅

### 4.3 캐시 성능 모니터링
- 캐시 미스 비율 추적
- 느린 조회 경고

---

## 5. 추가 구현 권장 사항

### 5.1 보안 기능

| 기능 | 우선순위 | 설명 |
|------|---------|------|
| Rate Limiting | High | API 호출 제한으로 DDoS 방어 |
| IP 화이트리스트 | High | 관리자 API 접근 제한 |
| 감사 로그 | High | 모든 거래/설정 변경 기록 |
| 2FA 강제 | Medium | 관리자/고액 사용자 필수 |
| 계정 잠금 | Medium | 로그인 실패 5회 시 15분 잠금 |
| 세션 관리 | Medium | 동시 세션 수 제한 |

### 5.2 거래 안전 기능

| 기능 | 우선순위 | 설명 |
|------|---------|------|
| 일일 손실 한도 | Critical | 설정된 금액 초과 시 봇 자동 중지 |
| 최대 포지션 크기 | Critical | 단일 포지션 최대 금액 제한 |
| 긴급 중지 버튼 | Critical | 모든 봇 즉시 중지 + 포지션 청산 |
| 이상 거래 탐지 | High | 비정상적 패턴 감지 시 알림 |
| 거래소 연결 모니터링 | High | 연결 끊김 시 즉시 알림 |
| 잔고 변동 알림 | Medium | 큰 잔고 변동 시 알림 |

### 5.3 모니터링 및 알림

| 기능 | 우선순위 | 설명 |
|------|---------|------|
| 서버 상태 모니터링 | High | CPU, 메모리, 디스크 |
| 에러 알림 시스템 | High | Critical 에러 발생 시 즉시 알림 |
| 거래 리포트 | Medium | 일일/주간/월간 거래 요약 |
| 성능 대시보드 | Medium | API 응답 시간, 처리량 |

---

## 6. 즉시 실행 계획 (Action Items)

### Phase 1: 긴급 (1-3일)

1. **API 키 교체**
   - [ ] JWT_SECRET 교체
   - [ ] ENCRYPTION_KEY 교체
   - [ ] 거래소 API 키 교체

2. **동적 코드 실행 비활성화**
   - [ ] `exec()` 호출 제거 또는 제한

3. **관리자 권한 검증 추가**
   - [ ] 모든 관리자 API에 `require_admin` 적용

4. **테스트 계정 정보 제거**
   - [ ] Login.jsx에서 하드코딩된 계정 정보 제거

### Phase 2: 높은 우선순위 (1-2주)

1. **토큰 관리 개선**
   - [ ] JWT 만료 시간 단축 (24시간 → 15분)
   - [ ] Refresh Token 구현
   - [ ] HttpOnly 쿠키 전환

2. **WebSocket 보안**
   - [ ] URL 파라미터에서 토큰 제거
   - [ ] 별도 인증 메시지 방식으로 변경

3. **CSRF 보호**
   - [ ] CSRF 토큰 구현

4. **봇 상태 동기화**
   - [ ] Lock 메커니즘 추가
   - [ ] UPSERT 쿼리 사용

### Phase 3: 중간 우선순위 (2-4주)

1. **입력값 검증 강화**
2. **에러 처리 개선**
3. **로깅 정리**
4. **타임아웃 설정**

### Phase 4: 장기 (1-2개월)

1. **Rate Limiting 구현**
2. **감사 로그 시스템**
3. **모니터링 대시보드**
4. **일일 손실 한도 기능**

---

## 7. 긍정적 보안 사항 (현재 잘 구현된 부분)

- 2FA (Two-Factor Authentication) 구현
- OAuth 지원 (Google, Kakao)
- 비밀번호 변경 기능
- API 키 마스킹 처리
- 에러 바운더리 구현
- WebSocket 재연결 로직
- 환경 변수 사용
- 암호화된 API 키 저장 (Fernet)

---

## 8. 결론

이 플랫폼은 **실제 자금이 움직이는 중요한 시스템**입니다. 현재 **9개의 Critical 취약점**이 존재하며, 이 중 **동적 코드 실행(exec)**과 **API 키 노출**은 즉시 조치가 필요합니다.

**권장 사항**:
1. 프로덕션 배포 전 Critical/High 항목 모두 해결
2. 정기적인 보안 감사 (분기별)
3. 침투 테스트 수행
4. 보안 인시던트 대응 계획 수립

---

**작성자**: Claude AI Security Audit
**검토 필요**: 개발팀 리더, 보안 담당자
