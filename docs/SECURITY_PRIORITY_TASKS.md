# 시스템 문제점 및 우선순위 작업 목록

> 생성일: 2025-12-12
> 전체 시스템 (백엔드, 프론트엔드, 관리자 페이지) 분석 후 도출

---

## 📊 시스템 현황 요약

| 영역 | 파일 수 | 테스트 | 주요 상태 |
|------|--------|--------|----------|
| **백엔드 API** | 31개 라우터 | 72 passed | ✅ 핵심 기능 완료 |
| **백엔드 서비스** | 30개 | 부분적 | ⚠️ TODO 항목 존재 |
| **프론트엔드 페이지** | 14개 | 없음 | ✅ UI 완료, 테스트 필요 |
| **관리자 페이지** | 3개 | 없음 | ⚠️ 기본 기능만 구현 |
| **데이터베이스 모델** | 15개+ | 없음 | ✅ 스키마 안정 |

---

## 🔴 우선순위 1: CRITICAL (즉시 조치 필요)

### 1.1 JWT Secret 하드코딩 제거

**위치**: `backend/src/config.py:99`

```python
jwt_secret: str = os.getenv("JWT_SECRET", "change_me")  # ❌ 위험!
```

**문제**: 기본값 `"change_me"`가 설정되어 있어 환경변수 미설정 시 예측 가능한 시크릿 사용
**해결**:

```python
jwt_secret: str = os.getenv("JWT_SECRET") or ""
# main.py에서 시작 시 검증 추가
if not settings.jwt_secret or settings.jwt_secret == "change_me":
    raise RuntimeError("JWT_SECRET must be set in production!")
```

**예상 시간**: 30분

---

### 1.2 주문 금액 서버 측 검증 강화

**위치**: `backend/src/api/order.py`
**문제**: 클라이언트가 전송한 금액을 그대로 사용할 경우 과도한 주문 위험
**해결**:

```python
# 사용자 잔고 대비 최대 주문 금액 검증
async def validate_order_amount(session, user_id, amount, leverage):
    # 1. 사용자 잔고 조회
    # 2. 리스크 설정 조회 (max_leverage 등)
    # 3. 최대 허용 금액 계산
    # 4. amount가 허용 범위 내인지 검증
    pass
```

**예상 시간**: 2시간

---

### 1.3 포지션 청산 시 소유권 검증

**위치**: `backend/src/api/order.py` - `close_position` 엔드포인트
**문제**: 다른 사용자의 포지션을 청산할 수 있는 취약점 가능
**해결**:

```python
# Position 조회 시 user_id 필터 필수
position = await session.execute(
    select(Position).where(
        Position.id == position_id,
        Position.user_id == user_id  # ⚠️ 필수 검증
    )
)
```

**예상 시간**: 1시간

---

## 🟠 우선순위 2: HIGH (1주일 내 조치)

### 2.1 그리드 봇 시장 가격 API - 목업 데이터 사용 중

**위치**: `backend/src/api/grid_bot.py:520-528`

```python
# TODO: 실제 거래소 API 연동
# 현재는 목업 데이터 반환
mock_prices = {
    "BTCUSDT": {"price": 97500, ...},
    ...
}
```

**문제**: 그리드 봇 설정 시 실제 가격이 아닌 하드코딩된 가격 사용
**해결**: Bitget REST API `get_ticker()` 연동

```python
async def get_market_price(symbol: str, user_id: int = Depends(get_current_user_id)):
    client = await get_user_exchange_client(session, user_id)
    ticker = await client.get_ticker(symbol)
    return {
        "symbol": symbol,
        "price": float(ticker.get("lastPr", 0)),
        "high_24h": float(ticker.get("high24h", 0)),
        "low_24h": float(ticker.get("low24h", 0)),
        ...
    }
```

**예상 시간**: 1시간

---

### 2.2 텔레그램 봇 핸들러 - 목업 데이터 사용 중

**위치**: `backend/src/services/telegram/bot_handler.py:192, 208, 222, 238`

```python
# TODO: 실제 데이터 연동
```

**문제**: `/status`, `/balance`, `/positions`, `/stats` 명령이 실제 데이터 미연동
**해결**: 각 핸들러에서 실제 DB/거래소 API 조회
**예상 시간**: 3시간

---

### 2.3 Refresh Token 구현

**위치**: `backend/src/utils/jwt_auth.py`, `backend/src/api/auth.py`
**현재 상태**: Access Token만 사용 (24시간 만료)
**문제**: 토큰 탈취 시 24시간 동안 악용 가능
**해결**:

```python
# Access Token: 15분 (짧게)
# Refresh Token: 7일 (쿠키에 httpOnly로 저장)
def create_tokens(user_data):
    access_token = create_token(user_data, expires=timedelta(minutes=15))
    refresh_token = create_token(user_data, expires=timedelta(days=7))
    return access_token, refresh_token
```

**예상 시간**: 4시간

---

### 2.4 비밀번호 정책 강화

**위치**: `backend/src/schemas/auth_schema.py`
**현재 상태**: 기본적인 길이 검증만 존재
**해결**:

```python
@field_validator('password')
@classmethod
def validate_password(cls, v):
    if len(v) < 8:
        raise ValueError('최소 8자 이상')
    if not re.search(r'[A-Z]', v):
        raise ValueError('대문자 포함 필요')
    if not re.search(r'[a-z]', v):
        raise ValueError('소문자 포함 필요')
    if not re.search(r'\d', v):
        raise ValueError('숫자 포함 필요')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
        raise ValueError('특수문자 포함 필요')
    return v
```

**예상 시간**: 1시간

---

### 2.5 로그인 실패 횟수 제한 (Brute Force 방지)

**위치**: `backend/src/api/auth.py`
**현재 상태**: 무제한 로그인 시도 가능
**해결**:

```python
# Redis 기반 로그인 실패 추적
LOGIN_FAIL_LIMIT = 5
LOGIN_LOCKOUT_MINUTES = 15

async def check_login_attempts(redis, email):
    key = f"login_fail:{email}"
    attempts = await redis.get(key) or 0
    if int(attempts) >= LOGIN_FAIL_LIMIT:
        raise HTTPException(429, f"계정이 잠금되었습니다")
```

**예상 시간**: 2시간

---

### 2.6 HTTPS 강제 (프로덕션)

**위치**: `backend/src/main.py`, `nginx/nginx.conf`
**현재 상태**: HTTP 허용
**해결**: Nginx에서 HTTP → HTTPS 리다이렉트 (이미 구성됨, 검증 필요)
**예상 시간**: 1시간

---

### 2.7 CORS 설정 강화

**위치**: `backend/src/main.py:130-146`
**현재 상태**: IP 주소 직접 하드코딩

```python
allowed_origins = [
    "http://localhost:3000",
    "http://158.247.245.197:3000",  # ❌ 하드코딩
    ...
]
```

**해결**: 프로덕션에서는 환경변수로만 CORS 설정
**예상 시간**: 30분

---

## 🟡 우선순위 3: MEDIUM (1개월 내 조치)

### 3.1 관리자 사용자 상세 - 잔고 조회 미구현

**위치**: `backend/src/api/admin_users.py:260`

```python
"total_balance": 0.0,  # TODO: 실제 잔고 조회 구현
```

**문제**: 관리자가 사용자 상세 정보에서 잔고를 볼 수 없음
**해결**: 거래소 API 연동하여 실제 잔고 조회
**예상 시간**: 2시간

---

### 3.2 관리자 강제 로그아웃 - 토큰 블랙리스트 미구현

**위치**: `backend/src/api/admin_users.py:608`

```python
# TODO: 향후 Redis 기반 토큰 블랙리스트 구현 시 개선
```

**문제**: 관리자가 사용자를 강제 로그아웃해도 토큰이 만료 전까지 유효
**해결**: Redis 기반 토큰 블랙리스트 구현
**예상 시간**: 3시간

---

### 3.3 민감한 작업에 2FA 강제

**위치**: `backend/src/api/account.py`, `backend/src/api/order.py`
**추가 대상**:

- API 키 저장/수정
- 대량 주문 (잔고의 50% 이상)
- 비밀번호 변경
**예상 시간**: 3시간

---

### 3.4 감사 로그 (Audit Log) 구현

**새 파일**: `backend/src/services/audit_service.py`
**추적 대상**:

- 로그인/로그아웃
- API 키 조회/변경
- 주문 실행/청산
- 봇 시작/중지
- 관리자 작업

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50))  # LOGIN, LOGOUT, ORDER_PLACED
    ip_address = Column(String(50))
    user_agent = Column(String(255))
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
```

**예상 시간**: 4시간

---

### 3.5 그리드 봇 테스트 추가

**새 파일**: `backend/tests/unit/test_grid_bot.py`
**테스트 대상**:

- 그리드 가격 계산 (등차/등비)
- 그리드 봇 생성/수정/삭제
- 봇 시작/정지
- 그리드 주문 상태 관리
**예상 시간**: 4시간

---

### 3.6 봇 인스턴스 테스트 추가

**새 파일**: `backend/tests/unit/test_bot_instances.py`
**테스트 대상**:

- 다중 봇 생성
- 할당률 검증
- 봇 격리 확인
**예상 시간**: 3시간

---

### 3.7 차트 데이터 사용자별 설정 미구현

**위치**: `backend/src/services/chart_data_service.py:138`

```python
# TODO: Make this user-specific based on their active trading pairs
```

**문제**: 차트 데이터 구독이 사용자 설정과 무관하게 고정됨
**예상 시간**: 2시간

---

## 🟢 우선순위 4: LOW (장기 개선)

### 4.1 Content Security Policy (CSP) 헤더

**위치**: Nginx 또는 백엔드 미들웨어

```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline';" always;
```

**예상 시간**: 30분

---

### 4.2 API 버저닝

**현재 상태**: `/auth/login`
**개선**: `/api/v1/auth/login`
**예상 시간**: 2시간

---

### 4.3 Rate Limiting JWT 파싱 미구현

**위치**: `backend/src/middleware/rate_limit.py:134`

```python
# TODO: JWT 토큰 파싱 구현
```

**참고**: `rate_limit_improved.py`에서는 구현됨 - 중복 파일 정리 필요
**예상 시간**: 1시간

---

### 4.4 Dependency 보안 스캔

```bash
# Python
pip-audit

# JavaScript
npm audit
```

**예상 시간**: 1시간

---

### 4.5 프론트엔드 E2E 테스트

**도구**: Playwright 또는 Cypress
**대상 페이지**: Login, Dashboard, Trading, Settings
**예상 시간**: 8시간

---

### 4.6 관리자 페이지 기능 확장

**현재 상태**: 기본적인 사용자 관리, 봇 제어만 구현
**필요 기능**:

- 시스템 모니터링 대시보드
- 거래 통계 분석
- 알림 관리
**예상 시간**: 16시간

---

## 📋 구현 체크리스트

### CRITICAL (즉시) ✅ 완료

| 작업 | 파일 | 상태 | 완료일 |
|------|------|------|--------|
| JWT Secret 검증 | `config.py`, `main.py` | ✅ 완료 | 2025-12-12 |
| 주문 금액 서버 검증 | `api/order.py` | ✅ 완료 | 2025-12-12 |
| 포지션 소유권 검증 | `api/order.py` | ✅ 완료 | 기존 구현됨 |

### HIGH (1주일)

| 작업 | 파일 | 상태 | 예상 시간 |
|------|------|------|----------|
| 그리드 봇 시장 가격 연동 | `api/grid_bot.py` | ✅ 완료 | 2025-12-12 |
| 텔레그램 봇 데이터 연동 | `telegram/bot_handler.py` | ✅ 완료 | 2025-12-12 |
| Refresh Token | `utils/jwt_auth.py` | ✅ 완료 | 2025-12-12 |
| 비밀번호 정책 | `utils/validators.py` | ✅ 완료 | 기존 구현됨 |
| 로그인 실패 제한 | `services/login_security.py` | ✅ 완료 | 2025-12-12 |
| HTTPS 강제 | `nginx/nginx.conf` | ✅ 완료 | 기존 구현됨 (도메인 설정 필요) |
| CORS 강화 | `main.py` | ✅ 완료 | 2025-12-12 |

### MEDIUM (1개월)

| 작업 | 파일 | 상태 | 예상 시간 |
|------|------|------|----------|
| 관리자 잔고 조회 | `api/admin_users.py` | ⬜ TODO | 2시간 |
| 토큰 블랙리스트 | `api/admin_users.py` | ⬜ TODO | 3시간 |
| 2FA 강제 | `api/account.py` | ⬜ TODO | 3시간 |
| 감사 로그 | 신규 | ⬜ TODO | 4시간 |
| 그리드 봇 테스트 | `tests/` | ⬜ TODO | 4시간 |
| 봇 인스턴스 테스트 | `tests/` | ⬜ TODO | 3시간 |
| 차트 사용자별 설정 | `chart_data_service.py` | ⬜ TODO | 2시간 |

### LOW (장기)

| 작업 | 상태 | 예상 시간 |
|------|------|----------|
| CSP 헤더 | ⬜ TODO | 30분 |
| API 버저닝 | ⬜ TODO | 2시간 |
| Rate Limit 파일 정리 | ⬜ TODO | 1시간 |
| 보안 스캔 | ⬜ TODO | 1시간 |
| 프론트 E2E 테스트 | ⬜ TODO | 8시간 |
| 관리자 페이지 확장 | ⬜ TODO | 16시간 |

---

## 📊 테스트 현황

### 백엔드 테스트 (18개 파일)

```
tests/unit/
├── test_auth_api.py        ✅ 14 passed
├── test_bot_api.py         ✅ 6 passed, 1 skipped
├── test_annotations_api.py ✅ 13 passed
├── test_crypto_secrets.py  ✅ 6 passed
├── test_exchange_service.py ✅ 6 passed, 1 skipped
├── test_jwt_utils.py       ✅ 11 passed
└── (기타 오래된 테스트...)

tests/integration/
├── test_health_endpoints.py ✅ 6 passed
└── test_trading_workflow.py ✅ 7 passed

총: 72 passed, 2 skipped
```

### 누락된 테스트

| 기능 | API 파일 | 테스트 파일 | 상태 |
|------|---------|------------|------|
| 그리드 봇 | `api/grid_bot.py` | 없음 | ❌ TODO |
| 봇 인스턴스 | `api/bot_instances.py` | 없음 | ❌ TODO |
| 차트 API | `api/chart.py` | 없음 | ❌ TODO |
| 주문 API | `api/order.py` | 없음 | ❌ TODO |
| 텔레그램 API | `api/telegram.py` | 없음 | ❌ TODO |
| 분석 API | `api/analytics.py` | 없음 | ❌ TODO |

---

## 🔧 환경 설정 체크리스트

**`.env.example` 기반 필수 환경변수**:

| 변수 | 설명 | 필수 |
|------|------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL | ✅ |
| `ENCRYPTION_KEY` | Fernet 암호화 키 (32바이트) | ✅ |
| `JWT_SECRET` | JWT 서명 시크릿 | ✅ |
| `REDIS_PASSWORD` | Redis 비밀번호 | ✅ |
| `TELEGRAM_BOT_TOKEN` | 텔레그램 봇 토큰 | ⬜ 선택 |
| `ADMIN_IP_WHITELIST` | 관리자 IP 화이트리스트 | ⬜ 선택 |
| `CORS_ORIGINS` | 허용 CORS 도메인 | ⬜ 프로덕션 필수 |

---

## 참조 문서

- [기존 보안 감사](./CODE_REVIEW_AND_SECURITY_AUDIT.md)
- [테스트 인수인계](./TEST_IMPLEMENTATION_HANDOVER.md)
- [백엔드 SKILL](../skills/backend-trading-api/SKILL.md)
- [프론트엔드 SKILL](../skills/frontend-trading-dashboard/SKILL.md)
- [Nginx 설정](../nginx/nginx.conf)
