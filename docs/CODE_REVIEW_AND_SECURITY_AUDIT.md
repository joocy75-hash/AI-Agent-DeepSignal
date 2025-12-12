# 🔒 코드 검토 및 보안 감사 보고서

## 📌 문서 정보

| 항목 | 내용 |
|------|------|
| 작성일 | 2025-12-12 |
| 검토 대상 | auto-dashboard 전체 (백엔드 + 프론트엔드) |
| 검토 목적 | 금융 거래 플랫폼 보안 감사 및 개선점 도출 |
| 예상 동시 사용자 | 100~1000명 |
| 특수 고려사항 | **실제 금전 거래 발생**, 다중 사용자, 다중 봇 |

---

## 🚨 심각도 등급

| 등급 | 의미 | 조치 기한 |
|------|------|----------|
| 🔴 **CRITICAL** | 즉시 해결 필요, 보안 취약점 또는 금전 손실 가능 | 즉시 |
| 🟠 **HIGH** | 빠른 해결 필요, 심각한 버그 또는 데이터 손실 가능 | 1주일 이내 |
| 🟡 **MEDIUM** | 개선 권장, 성능 또는 사용자 경험 영향 | 2주일 이내 |
| 🟢 **LOW** | 개선 권장, 코드 품질 또는 유지보수성 | 차후 개선 |
| ✅ **GOOD** | 잘 구현됨 (참고용) | - |

---

## ✅ 잘 구현된 부분 (GOOD)

### 1. 인증 및 권한 관리

- ✅ JWT 기반 인증 (`jwt_auth.py`)
- ✅ 비밀번호 bcrypt 해싱 (`passlib.context`)
- ✅ 2FA TOTP 지원 (`totp_service.py`)
- ✅ API 키 AES 암호화 (`crypto_secrets.py` - Fernet)
- ✅ 관리자 권한 체크 (`require_admin`)
- ✅ 사용자별 데이터 격리 (모든 API에서 `user_id` 확인)

### 2. Rate Limiting

- ✅ IP 기반 + 사용자별 Rate Limiting (`rate_limit_improved.py`)
- ✅ 엔드포인트별 세분화된 설정
- ✅ API 키 조회 Rate Limit (시간당 3회)
- ✅ Rate Limit 헤더 추가

### 3. 다중 봇 동시성 관리

- ✅ `AllocationManager` - 잔고 할당 관리 및 락
- ✅ `BotIsolationManager` - 봇 간 포지션 충돌 방지
- ✅ `BotRecoveryManager` - 에러 복구 및 재시도

### 4. 에러 핸들링

- ✅ 전역 예외 핸들러 (`error_handler.py`)
- ✅ 구조화된 로깅 (`structured_logging.py`)
- ✅ Bitget API 에러 분류 (`bitget_exceptions.py`)

### 5. 프론트엔드 보안

- ✅ HTTPS 경고 (프로덕션에서 HTTP 사용 시)
- ✅ 401 응답 시 자동 로그아웃
- ✅ API 타임아웃 설정 (15초)

---

## 🔴 CRITICAL - 즉시 해결 필요

### 1. JWT Secret 기본값 취약점 ⚠️

**파일**: `backend/src/config.py`

```python
jwt_secret: str = os.getenv("JWT_SECRET", "change_me")  # ❌ 위험
```

**문제점**:

- `change_me`라는 예측 가능한 기본값 사용
- 환경 변수 미설정 시 토큰 위조 가능

**해결책**:

```python
jwt_secret: str = os.getenv("JWT_SECRET", "")

# main.py에서
if not settings.jwt_secret:
    raise RuntimeError("JWT_SECRET environment variable is required!")
```

---

### 2. 주문 금액 검증 부재 ⚠️

**파일**: `backend/src/api/order.py`

**문제점**:

- 주문 시 최대 금액 검증 없음
- 사용자 잔고 초과 주문 가능성
- 잔고 할당 대비 주문 크기 검증 필요

**해결책**:

```python
async def submit_order(...):
    # 1. 사용자 잔고 확인
    balance = await client.fetch_balance()
    available = float(balance.get("free", 0))
    
    # 2. 주문 크기 검증
    order_value = price * size
    if order_value > available * 0.95:  # 95% 제한
        raise HTTPException(400, "주문 금액이 사용 가능 잔고를 초과합니다")
    
    # 3. 일일 손실 한도 확인
    daily_loss = await get_daily_loss(session, user_id)
    if daily_loss > risk_settings.daily_loss_limit:
        raise HTTPException(400, "일일 손실 한도 초과")
```

---

### 3. 포지션 청산 시 소유권 미검증 ⚠️

**파일**: `backend/src/api/order.py` - `close_position()`

**문제점**:

- `position_id`만으로 청산 요청 처리
- 다른 사용자의 포지션 청산 가능성 (IDOR 취약점)

**해결책**:

```python
async def close_position(..., user_id: int = Depends(get_current_user_id)):
    # 포지션 소유권 확인 필수
    position = await session.get(Position, payload.position_id)
    if not position or position.user_id != user_id:
        raise HTTPException(404, "포지션을 찾을 수 없습니다")
```

---

### 4. API 키 복호화 로그 누출 위험 ⚠️

**파일**: `backend/src/api/account.py`

**문제점**:

- API 키 조회 시 전체 키를 반환
- 네트워크 탈취 시 API 키 유출

**해결책**:

```python
# 마스킹 처리
return {
    "api_key": key[:8] + "****" + key[-4:],
    "api_key_full": decrypt_secret(key.encrypted_api_key),  # 필요 시만
    # ...
}
```

---

## 🟠 HIGH - 빠른 해결 필요

### 5. 트랜잭션 격리 수준 미설정

**파일**: 전체 DB 작업

**문제점**:

- 동시 주문 시 Race Condition 가능
- 잔고 불일치 발생 가능

**해결책**:

```python
from sqlalchemy import SERIALIZABLE

async with session.begin():
    # SERIALIZABLE 격리 수준 설정
    await session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
    # 중요 트랜잭션 처리
```

---

### 6. 봇 상태 불일치 가능성

**파일**: `backend/src/services/bot_runner.py`

**문제점**:

- 서버 재시작 시 메모리 내 봇 상태와 DB 불일치
- `is_running=True`인 봇이 실제로는 중지 상태

**해결책**:

```python
async def startup_sync():
    """서버 시작 시 봇 상태 동기화"""
    async with get_session() as session:
        # 실행 중인 봇 모두 중지 상태로 리셋
        await session.execute(
            update(BotInstance).where(
                BotInstance.is_running == True
            ).values(is_running=False, last_error="서버 재시작으로 중지됨")
        )
        await session.commit()
```

---

### 7. 민감 정보 로그 출력

**파일**: 여러 파일

**문제점**:

```python
logger.info(f"API keys encrypted successfully")  # API 키 관련 로그
logger.error(f"Error: {e}")  # 예외 전체 출력 (API 키 포함 가능)
```

**해결책**:

```python
# 민감 정보 필터링 로거 사용
class SanitizedLogger:
    SENSITIVE_PATTERNS = ['api_key', 'secret', 'password', 'token']
    
    def sanitize(self, message):
        for pattern in self.SENSITIVE_PATTERNS:
            message = re.sub(
                f'{pattern}[=:][^\\s,]+', 
                f'{pattern}=***REDACTED***', 
                message, 
                flags=re.IGNORECASE
            )
        return message
```

---

### 8. CORS 설정 검증 부재

**파일**: `backend/src/main.py`

**문제점**:

- `CORS_ORIGINS`가 빈 문자열일 때 기본 동작 불명확
- 와일드카드(`*`) 허용 가능성

**해결책**:

```python
# main.py
cors_origins = settings.cors_origins.split(",") if settings.cors_origins else []

# 프로덕션에서 와일드카드 금지
if not settings.debug and "*" in cors_origins:
    raise RuntimeError("Production environment cannot use '*' as CORS origin")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    # ...
)
```

---

## 🟡 MEDIUM - 개선 권장

### 9. 입력 유효성 검사 강화 필요

**파일**: `backend/src/schemas/`

**문제점**:

- 심볼 입력에 대한 화이트리스트 검증 부족
- 숫자 필드의 범위 검증 불완전

**해결책**:

```python
from pydantic import validator

ALLOWED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "ADAUSDT", "XRPUSDT", "DOGEUSDT"]

class OrderSubmit(BaseModel):
    symbol: str
    leverage: int
    size: float
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if v not in ALLOWED_SYMBOLS:
            raise ValueError(f"지원하지 않는 심볼: {v}")
        return v
    
    @validator('leverage')
    def validate_leverage(cls, v):
        if not 1 <= v <= 100:
            raise ValueError("레버리지는 1~100 사이여야 합니다")
        return v
    
    @validator('size')
    def validate_size(cls, v):
        if v <= 0:
            raise ValueError("주문 크기는 0보다 커야 합니다")
        if v > 10000:
            raise ValueError("주문 크기가 너무 큽니다")
        return v
```

---

### 10. 프론트엔드 XSS 취약점 가능성

**파일**: 여러 React 컴포넌트

**문제점**:

- 사용자 입력값 직접 렌더링 시 XSS 가능
- 특히 `봇 이름`, `설명` 필드

**해결책**:

```jsx
// DOMPurify 사용
import DOMPurify from 'dompurify';

<div dangerouslySetInnerHTML={{ 
    __html: DOMPurify.sanitize(bot.description) 
}} />

// 또는 텍스트로만 렌더링 (권장)
<div>{bot.description}</div>
```

---

### 11. 세션 만료 시 포지션 처리 정책 부재

**파일**: 시스템 전체

**문제점**:

- 사용자 세션 만료 시 열린 포지션 방치
- 봇 중지 시 열린 포지션 자동 청산 여부 불명확

**해결책**:

```python
# 설정에 추가
class RiskSettings:
    close_on_session_expire: bool = False
    close_on_bot_stop: bool = True
    max_position_hold_time: int = 24 * 60 * 60  # 24시간

# 봇 중지 시
async def stop_bot_instance(...):
    if risk_settings.close_on_bot_stop:
        await close_all_positions(user_id, bot_id)
```

---

### 12. 메모리 기반 Rate Limit 저장소

**파일**: `backend/src/middleware/rate_limit_improved.py`

**문제점**:

- 서버 재시작 시 Rate Limit 초기화
- 다중 서버 구성 시 Rate Limit 공유 불가

**해결책**:

```python
# Redis 기반 Rate Limit 저장소
import redis.asyncio as redis

class RedisRateLimitStore:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    async def check_and_record(self, key: str, limit: int, window: int):
        current = await self.redis.incr(key)
        if current == 1:
            await self.redis.expire(key, window)
        
        if current > limit:
            return False, 0, await self.redis.ttl(key)
        return True, limit - current, await self.redis.ttl(key)
```

---

## 🟢 LOW - 차후 개선

### 13. 테스트 커버리지 부족

**현재 상태**: 테스트 파일 미확인

**권장사항**:

- 최소 80% 테스트 커버리지 목표
- 특히 중요 경로:
  - 인증/권한
  - 주문 실행
  - 잔고 할당
  - 봇 시작/중지

---

### 14. API 버전 관리 없음

**현재 상태**: `/api/v1` 없이 직접 경로 사용

**권장사항**:

```python
router = APIRouter(prefix="/api/v1")
```

---

### 15. 감사 로그 미구현

**권장사항**:

```python
class AuditLog:
    user_id: int
    action: str  # "LOGIN", "ORDER", "API_KEY_VIEW", etc.
    ip_address: str
    user_agent: str
    details: dict
    created_at: datetime
```

---

### 16. 모니터링 및 알림 부재

**권장사항**:

- Prometheus 메트릭 수집
- Grafana 대시보드
- 슬랙/텔레그램 알림 (에러, 큰 손실 등)

---

## 📋 개선 우선순위

| 순위 | 이슈 | 심각도 | 예상 작업 시간 |
|------|------|--------|---------------|
| 1 | JWT Secret 기본값 | 🔴 CRITICAL | 30분 |
| 2 | 주문 금액 검증 | 🔴 CRITICAL | 2시간 |
| 3 | 포지션 청산 소유권 검증 | 🔴 CRITICAL | 1시간 |
| 4 | API 키 마스킹 | 🔴 CRITICAL | 1시간 |
| 5 | 트랜잭션 격리 수준 | 🟠 HIGH | 3시간 |
| 6 | 봇 상태 동기화 | 🟠 HIGH | 2시간 |
| 7 | 민감 정보 로그 필터링 | 🟠 HIGH | 4시간 |
| 8 | CORS 설정 검증 | 🟠 HIGH | 1시간 |
| 9 | 입력 유효성 검사 강화 | 🟡 MEDIUM | 4시간 |
| 10 | XSS 방지 | 🟡 MEDIUM | 2시간 |

---

## 🔧 즉시 적용 가능한 핫픽스

### 1. JWT Secret 검증 추가

```python
# config.py
jwt_secret: str = os.getenv("JWT_SECRET", "")

# main.py 시작 부분
if not settings.jwt_secret or settings.jwt_secret == "change_me":
    raise RuntimeError("❌ JWT_SECRET must be set and not 'change_me'")
```

### 2. 포지션 소유권 검증

```python
# order.py - close_position()
# 기존 코드 후에 추가
position = await session.execute(
    select(Position).where(
        Position.id == payload.position_id,
        Position.user_id == user_id  # ✅ 소유권 확인
    )
)
if not position.scalar_one_or_none():
    raise HTTPException(404, "포지션을 찾을 수 없습니다")
```

---

## 📊 결론

### 현재 보안 수준: **B+ (양호)**

**강점**:

- 인증/권한 시스템 잘 구현
- API 키 암호화 적용
- Rate Limiting 적용
- 다중 봇 격리 메커니즘 존재

**취약점**:

- 일부 CRITICAL 이슈 존재 (JWT Secret, 주문 검증)
- 입력 유효성 검사 불완전
- 감사 로그 미구현

**권장사항**:

1. CRITICAL 이슈 즉시 해결 (배포 전)
2. HIGH 이슈 1주일 내 해결
3. 테스트 커버리지 확대
4. 정기적 보안 감사 실시

---

**작성자**: Claude (AI Assistant)  
**검토일**: 2025-12-12  
**다음 검토 예정**: 2025-12-26
