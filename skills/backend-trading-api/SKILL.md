# Backend Trading API Skill

> AI 자동매매 플랫폼 백엔드 개발을 위한 완벽 가이드

## Description

이 스킬은 다음 상황에서 사용합니다:

- FastAPI 기반 거래 API 엔드포인트 추가/수정
- Bitget 등 거래소 API 연동 코드 작성
- 트레이딩 전략 구현 (RSI, MACD, 볼린저밴드 등)
- 백테스팅 엔진 개발
- 주문 실행 및 위험 관리 로직 구현
- **다중 봇 시스템 개발**
- **보안 기능 구현**

**트리거 키워드**: "API 엔드포인트", "거래소 연동", "전략 구현", "백테스트", "주문 실행", "봇 개발", "다중 봇", "보안", "인증"

---

## 📌 최신 업데이트 (2025-12-12)

### ✅ 완료된 작업

- **테스트 완료**: Unit/Integration 테스트 72개 통과 (2개 스킵)
- **보안 강화 완료**: 모든 CRITICAL/HIGH 작업 완료
  - JWT Secret 검증 강화 (프로덕션 필수)
  - Refresh Token 구현 (`utils/jwt_auth.py`)
  - 로그인 Brute-force 방지 (`services/login_security.py`)
  - 주문 금액 서버 측 검증 (`api/order.py`)
  - 포지션 소유권 검증 (`api/order.py`)
  - CORS 환경별 설정 (`main.py`)
- **DeepSeek AI V3.2** 업데이트 (`services/deepseek_service.py`)
- **그리드 봇 시장 가격** 실시간 연동 (`api/grid_bot.py`)
- **텔레그램 봇 DB 연동** 완료 (`services/telegram/bot_handler.py`)

### 📎 참조 문서

- 보안 우선순위 작업 목록 → `docs/SECURITY_PRIORITY_TASKS.md`
- 배포 전 점검 리포트 → `docs/PRE_DEPLOYMENT_AUDIT.md`
- 기존 보안 감사 → `docs/CODE_REVIEW_AND_SECURITY_AUDIT.md`

---

## 1. 프로젝트 구조

```
backend/src/
├── api/                  # FastAPI 라우터 (31개)
│   ├── auth.py          # 인증 (로그인, 회원가입, refresh token)
│   ├── two_factor.py    # 2FA (TOTP)
│   ├── oauth.py         # 소셜 로그인 (Google, Kakao)
│   ├── account.py       # 계정 (잔고, API키, 리스크설정)
│   ├── bot.py           # 단일 봇 (레거시) - 멀티 디바이스 동기화
│   ├── bot_instances.py # ⭐ 다중 봇 API
│   ├── grid_bot.py      # ⭐ 그리드 봇 API (Bitget 실시간 연동)
│   ├── order.py         # ⭐ 주문 실행/청산 (서버 검증 강화)
│   ├── strategy.py      # 전략 CRUD
│   ├── backtest.py      # 백테스트 실행
│   ├── chart.py         # 차트 데이터
│   ├── annotations.py   # 차트 어노테이션
│   ├── telegram.py      # 텔레그램 알림
│   ├── health.py        # 헬스 체크
│   ├── api_status.py    # API 연결 상태 (DeepSeek V3.2 등)
│   └── admin_*.py       # 관리자 API들
├── services/             # 비즈니스 로직 (35개+)
│   ├── bot_runner.py         # 봇 실행 엔진 (2000+ 줄)
│   ├── allocation_manager.py # ⭐ 잔고 할당 관리
│   ├── bot_isolation_manager.py # 봇 격리 관리
│   ├── bot_recovery_manager.py  # 봇 복구 관리
│   ├── grid_bot_runner.py    # 그리드 봇 로직
│   ├── bitget_rest.py        # Bitget REST API
│   ├── bitget_ws.py          # Bitget WebSocket
│   ├── strategy_engine.py    # 전략 신호 생성
│   ├── totp_service.py       # TOTP 2FA 서비스
│   ├── login_security.py     # ⭐ 로그인 보안 (Brute-force 방지)
│   ├── deepseek_service.py   # ⭐ DeepSeek AI V3.2 서비스
│   ├── exchange_service.py   # 거래소 클라이언트 관리
│   └── telegram/             # 텔레그램 서비스
│       ├── notifier.py       # 알림 전송
│       └── bot_handler.py    # ⭐ 봇 핸들러 (DB 연동)
├── database/             # SQLAlchemy 모델
│   ├── models.py        # User, Trade, BotInstance 등 (700+ 줄)
│   └── db.py            # 데이터베이스 연결
├── schemas/              # Pydantic 스키마
│   ├── auth_schema.py   # 인증 스키마
│   └── bot_instance_schema.py  # 봇 인스턴스 스키마
├── middleware/           # 미들웨어
│   ├── rate_limit_improved.py  # Rate Limiting (JWT 기반)
│   ├── admin_ip_whitelist.py   # 관리자 IP 제한
│   ├── error_handler.py        # 전역 에러 핸들러
│   └── request_context.py      # 요청 컨텍스트
├── utils/                # 유틸리티
│   ├── jwt_auth.py      # ⭐ JWT 인증 (Refresh Token 포함)
│   ├── crypto_secrets.py # API 키 암호화 (Fernet)
│   ├── validators.py    # 입력 검증 (비밀번호 정책 등)
│   ├── exceptions.py    # 커스텀 예외
│   ├── cache_manager.py # 캐시 관리 (Redis/메모리)
│   └── structured_logging.py   # 구조화된 로깅
├── strategies/           # 전략 구현
│   ├── proven_aggressive_strategy.py  # 공격적 전략
│   ├── proven_balanced_strategy.py    # 균형 전략
│   ├── proven_conservative_strategy.py # 보수적 전략
│   └── ai_role_division_strategy.py   # AI 역할 분담
└── workers/              # 비동기 작업자
    └── manager.py       # BotManager

backend/tests/            # 테스트 (72 passed)
├── unit/
│   ├── test_auth_api.py       # 14 passed ✅
│   ├── test_bot_api.py        # 6 passed, 1 skipped
│   ├── test_annotations_api.py # 13 passed
│   ├── test_crypto_secrets.py  # 6 passed
│   ├── test_exchange_service.py # 6 passed, 1 skipped
│   └── test_jwt_utils.py       # 11 passed
├── integration/
│   ├── test_health_endpoints.py # 6 passed
│   └── test_trading_workflow.py # 7 passed
└── conftest.py           # 테스트 픽스처
```

---

## 2. 보안 기능 현황

### 2.1 ✅ 완료된 보안 기능 (CRITICAL + HIGH)

| 기능 | 파일 | 상태 | 완료일 |
|------|------|------|--------|
| JWT 인증 + Refresh Token | `utils/jwt_auth.py` | ✅ 완료 | 2025-12-12 |
| JWT Secret 프로덕션 필수화 | `config.py`, `main.py` | ✅ 완료 | 2025-12-12 |
| API 키 암호화 (Fernet) | `utils/crypto_secrets.py` | ✅ 완료 | 기존 |
| 비밀번호 해싱 (bcrypt) | `utils/jwt_auth.py` | ✅ 완료 | 기존 |
| 비밀번호 정책 강화 | `utils/validators.py` | ✅ 완료 | 기존 |
| 2FA (TOTP) | `api/two_factor.py`, `services/totp_service.py` | ✅ 완료 | 기존 |
| Rate Limiting (IP + 사용자) | `middleware/rate_limit_improved.py` | ✅ 완료 | 기존 |
| 관리자 IP 화이트리스트 | `middleware/admin_ip_whitelist.py` | ✅ 완료 | 기존 |
| RBAC (관리자/사용자) | `utils/auth_dependencies.py` | ✅ 완료 | 기존 |
| 입력 검증 (Pydantic) | `schemas/*.py` | ✅ 완료 | 기존 |
| SQL Injection 방지 | SQLAlchemy ORM 사용 | ✅ 완료 | 기존 |
| 에러 메시지 필터링 | `middleware/error_handler.py` | ✅ 완료 | 기존 |
| 로그인 Brute-force 방지 | `services/login_security.py` | ✅ 완료 | 2025-12-12 |
| 주문 금액 서버 검증 | `api/order.py` | ✅ 완료 | 2025-12-12 |
| 포지션 소유권 검증 | `api/order.py` | ✅ 완료 | 기존 확인 |
| CORS 환경별 설정 | `main.py` | ✅ 완료 | 2025-12-12 |
| HTTPS 리다이렉션 | `nginx/nginx.conf` | ✅ 완료 | 기존 |

### 2.2 🟡 MEDIUM 우선순위 (향후 작업)

| 작업 | 상태 |
|------|------|
| 감사 로그 (Audit Log) | ⬜ TODO |
| 민감한 작업 2FA 강제 | ⬜ TODO |
| WebSocket 상태 브로드캐스트 | ⬜ TODO |

---

## 3. 핵심 API 엔드포인트

### 3.1 인증 API (`/auth`)

```python
POST /auth/register      # 회원가입
POST /auth/login         # 로그인 (access_token + refresh_token 반환)
POST /auth/refresh       # ⭐ Refresh Token으로 Access Token 갱신
POST /auth/change-password # 비밀번호 변경
GET  /auth/users         # 사용자 목록 (관리자용)
```

**로그인 응답 예시**:

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### 3.2 봇 API (`/bot`)

```python
POST /bot/start          # 봇 시작 (포지션 동기화)
POST /bot/stop           # 봇 중지 + 포지션 자동 청산
GET  /bot/status         # 봇 상태 조회 (DB-Runtime 자동 동기화)
```

**멀티 디바이스 동기화 로직** (`bot.py` 414-427줄):

```python
# 실제 BotManager의 상태 확인 (중요!)
is_actually_running = manager.runner.is_running(user_id)

# 데이터베이스와 실제 상태가 다른 경우 처리
if status and status.is_running != is_actually_running:
    # DB를 실제 상태에 맞게 업데이트 (자동 재시작 하지 않음!)
    status.is_running = is_actually_running
    await session.commit()
```

### 3.3 주문 API (`/order`) - 보안 강화

```python
POST /order/submit       # 주문 제출 (서버 검증)
POST /order/close/{id}   # 포지션 청산 (소유권 검증)
```

**서버 측 검증 항목**:

- 사용자별 `max_leverage` 확인
- 현재 포지션 수 제한 확인
- 사용 가능한 잔고 대비 주문 금액 검증
- 포지션 소유권 검증 (user_id 일치)

---

## 4. JWT 인증 시스템 (업데이트됨)

### 4.1 Access Token + Refresh Token 구조

```python
# utils/jwt_auth.py
class JWTAuth:
    # Access Token: 1시간 유효
    ACCESS_TOKEN_EXPIRES_HOURS = 1
    
    # Refresh Token: 7일 유효
    REFRESH_TOKEN_EXPIRES_DAYS = 7
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """Access Token 생성 (type: 'access')"""
        ...
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Refresh Token 생성 (type: 'refresh')"""
        ...
    
    @staticmethod
    def refresh_access_token(refresh_token: str) -> tuple:
        """Refresh Token으로 새 Access Token 발급"""
        ...
```

### 4.2 로그인 시 두 토큰 모두 반환

```python
# api/auth.py - /auth/login
user_data = {"user_id": user.id, "email": user.email, "role": user.role or "user"}

access_token = JWTAuth.create_access_token(data=user_data)
refresh_token = JWTAuth.create_refresh_token(data=user_data)

return {
    "access_token": access_token,
    "refresh_token": refresh_token,
    "token_type": "bearer"
}
```

### 4.3 Token Refresh 엔드포인트

```python
# api/auth.py - POST /auth/refresh
@router.post("/refresh")
async def refresh_token(payload: RefreshTokenRequest):
    new_access, new_refresh = JWTAuth.refresh_access_token(payload.refresh_token)
    
    response = {"access_token": new_access, "token_type": "bearer"}
    if new_refresh:  # 만료 임박 시에만 새 refresh token 발급
        response["refresh_token"] = new_refresh
    
    return response
```

---

## 5. 로그인 보안 (Brute-force 방지)

### 5.1 LoginSecurityService

```python
# services/login_security.py
class LoginSecurityService:
    # 설정: 개발(5회/1분) vs 프로덕션(10회/15분)
    MAX_ATTEMPTS_DEV = 5
    MAX_ATTEMPTS_PROD = 10
    LOCKOUT_MINUTES_DEV = 1
    LOCKOUT_MINUTES_PROD = 15
    
    async def check_login_allowed(self, email: str) -> tuple[bool, str]:
        """로그인 허용 여부 확인"""
        ...
    
    async def record_failed_attempt(self, email: str):
        """실패 기록"""
        ...
    
    async def record_successful_login(self, email: str):
        """성공 시 기록 초기화"""
        ...
```

### 5.2 로그인 API에서 사용

```python
# api/auth.py
login_security = LoginSecurityService()

# Step 1: 로그인 허용 여부 확인
is_allowed, error_message = await login_security.check_login_allowed(payload.email)
if not is_allowed:
    raise AuthenticationError(error_message)

# Step 2: 인증 실패 시 기록
if not valid_password:
    await login_security.record_failed_attempt(payload.email)
    raise AuthenticationError("Invalid email or password")

# Step 3: 성공 시 초기화
await login_security.record_successful_login(payload.email)
```

---

## 6. 거래소 API 연동

### 6.1 Bitget REST API

```python
from ..services.bitget_rest import BitgetRestClient, OrderSide

# 클라이언트 생성
client = BitgetRestClient(api_key, api_secret, passphrase)

# 잔고 조회
balance = await client.fetch_balance()

# 시장가 주문
result = await client.place_market_order(
    symbol="BTCUSDT",
    side=OrderSide.BUY,
    size=0.001,
    margin_coin="USDT",
)

# 포지션 청산 (reduce_only 사용 - 안전)
await client.place_market_order(
    symbol="BTCUSDT",
    side=OrderSide.SELL,
    size=0.001,
    margin_coin="USDT",
    reduce_only=True,  # ⭐ 청산 전용
)

await client.close()
```

### 6.2 그리드 봇 시장 가격 조회 (실시간)

```python
# api/grid_bot.py - GET /grid/market/{symbol}
# Bitget Public API (인증 불필요) 호출

api_url = "https://api.bitget.com/api/v2/mix/market/ticker"
params = {"symbol": symbol, "productType": "USDT-FUTURES"}

async with aiohttp.ClientSession() as session:
    async with session.get(api_url, params=params, timeout=10) as response:
        data = await response.json()
        ticker = data["data"][0]
        
        return {
            "symbol": symbol,
            "price": float(ticker["lastPr"]),
            "high_24h": float(ticker["high24h"]),
            "low_24h": float(ticker["low24h"]),
            "change_24h": float(ticker["change24h"]) * 100,
        }
```

---

## 7. 텔레그램 봇 (DB 연동)

### 7.1 실시간 데이터 조회

```python
# services/telegram/bot_handler.py

async def handle_daily(self, chat_id: int):
    """오늘 거래 현황 (실제 DB 연동)"""
    async with await self._get_db_session() as session:
        data = await self._get_user_trades_today(session)
        
        msg = f"""📊 일일 거래 현황
• 총 거래: {data["count"]}회
• 승/패: {data["wins"]}승 {data["losses"]}패
• 손익: {data["pnl"]:+.2f} USDT"""
        
        await self._send_message(chat_id, msg)
```

### 7.2 지원 명령어

| 명령어 | 설명 | DB 연동 |
|--------|------|---------|
| 📊 오늘 현황 | 오늘 거래 현황 | ✅ Trade 테이블 |
| 💰 수익 | 수익 요약 | ✅ Trade 테이블 |
| 📈 상태 | 봇 상태 | ✅ BotInstance 테이블 |
| 📋 상태표 | 포지션 상태 | ✅ Position 테이블 |
| 📉 성과 | 30일 성과 분석 | ✅ Trade 테이블 |
| 🔢 거래횟수 | 거래 횟수 | ✅ Trade 테이블 |

---

## 8. 환경 변수 (프로덕션 필수)

```bash
# 필수 환경변수
JWT_SECRET=          # ⚠️ 프로덕션에서 필수, 랜덤 32자 이상
ENCRYPTION_KEY=      # API 키 암호화용 Fernet 키
POSTGRES_PASSWORD=   # 데이터베이스 비밀번호
REDIS_PASSWORD=      # Redis 비밀번호

# 선택 환경변수
CORS_ORIGINS=        # 허용 도메인 (쉼표 구분)
ENVIRONMENT=         # production | development
DEEPSEEK_API_KEY=    # DeepSeek AI 전략 생성용
TELEGRAM_BOT_TOKEN=  # 텔레그램 알림용
TELEGRAM_CHAT_ID=    # 텔레그램 채팅 ID
```

---

## 9. 테스트 실행

```bash
cd backend

# 핵심 테스트만 (72 passed)
python -m pytest tests/unit/ tests/integration/ -v --no-cov

# 특정 테스트
python -m pytest tests/unit/test_auth_api.py -v --no-cov

# 커버리지 포함
python -m pytest tests/ -v --cov=src
```

---

## 10. 참조 문서

| 문서 | 위치 | 설명 |
|------|------|------|
| 배포 전 점검 | `docs/PRE_DEPLOYMENT_AUDIT.md` | ⭐ 전체 점검 리포트 |
| 보안 우선순위 | `docs/SECURITY_PRIORITY_TASKS.md` | 보안 작업 목록 |
| 테스트 인수인계 | `docs/TEST_IMPLEMENTATION_HANDOVER.md` | 테스트 현황 |
| 다중 봇 개요 | `docs/MULTI_BOT_01_OVERVIEW.md` | 다중 봇 설계 |
| 차트 마커 가이드 | `docs/CHART_SIGNAL_MARKERS_GUIDE.md` | 차트 시그널 |
| 코드 리뷰 | `docs/CODE_REVIEW_AND_SECURITY_AUDIT.md` | 보안 감사 |
