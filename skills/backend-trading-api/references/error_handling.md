# 에러 핸들링 참조

## 커스텀 예외 클래스 (utils/exceptions.py)

### 인증 관련 (4xx)

```python
class AuthenticationError(AppException):
    """인증 실패 (401)"""
    # message="Authentication failed", status_code=401

class InvalidTokenError(AuthenticationError):
    """잘못된 토큰 (401)"""

class PermissionDeniedError(AppException):
    """권한 없음 (403)"""

class AdminRequiredError(PermissionDeniedError):
    """관리자 권한 필요 (403)"""
```

### 리소스 관련 (4xx)

```python
class ResourceNotFoundError(AppException):
    """리소스를 찾을 수 없음 (404)"""
    # 사용: raise ResourceNotFoundError("Strategy", strategy_id)

class UserNotFoundError(ResourceNotFoundError):
    """사용자를 찾을 수 없음 (404)"""

class StrategyNotFoundError(ResourceNotFoundError):
    """전략을 찾을 수 없음 (404)"""

class ApiKeyNotFoundError(ResourceNotFoundError):
    """API 키를 찾을 수 없음 (404)"""
```

### 검증 관련 (4xx)

```python
class ValidationError(AppException):
    """입력 검증 실패 (400)"""
    # 사용: raise ValidationError("Invalid symbol", field="symbol")

class InvalidParameterError(ValidationError):
    """잘못된 파라미터 (400)"""

class DuplicateResourceError(AppException):
    """중복된 리소스 (409)"""
    # 사용: raise DuplicateResourceError("User", "email", "test@test.com")
```

### Rate Limiting 관련 (429)

```python
class RateLimitExceededError(AppException):
    """Rate Limit 초과 (429)"""
    # 사용: raise RateLimitExceededError("Too many requests", limit=10, window="minute")

class ResourceLimitExceededError(AppException):
    """리소스 제한 초과 (429)"""
    # 사용: raise ResourceLimitExceededError("Active bots", limit=5, current=6)
```

### 비즈니스 로직 관련

```python
class BotNotRunningError(AppException):
    """봇이 실행 중이 아님 (400)"""

class BotAlreadyRunningError(AppException):
    """봇이 이미 실행 중 (400)"""

class ExchangeAPIError(AppException):
    """거래소 API 에러 (502)"""
    # 사용: raise ExchangeAPIError("Bitget", str(original_error))

class EncryptionError(AppException):
    """암호화/복호화 에러 (500)"""

class DatabaseError(AppException):
    """데이터베이스 에러 (500)"""
```

### 보안 관련 (403)

```python
class SecurityError(AppException):
    """보안 위반 (403)"""

class PathTraversalError(SecurityError):
    """Path Traversal 시도 (403)"""
```

---

## 전역 에러 핸들러 (middleware/error_handler.py)

### 자동 처리되는 예외

```python
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.error_code,
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request.state.request_id,
            },
        },
    )
```

### 응답 형식

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid symbol format",
        "details": {
            "field": "symbol",
            "reason": "Symbol must end with USDT"
        },
        "timestamp": "2025-12-02T10:00:00.000000",
        "request_id": "abc123"
    }
}
```

---

## 구조화된 로깅 (utils/structured_logging.py)

### Logger 사용

```python
from ..utils.structured_logging import get_logger

logger = get_logger(__name__)

# 정보 로그
logger.info(
    "event_type",           # 이벤트 타입 (snake_case)
    "Human readable message",
    user_id=1,
    extra_field="value"
)

# 경고 로그
logger.warning(
    "validation_failed",
    "Invalid input received",
    field="symbol",
    value="invalid"
)

# 에러 로그
logger.error(
    "api_error",
    "Bitget API failed",
    error=str(e),
    traceback=traceback.format_exc()
)
```

### 이벤트 타입 컨벤션

| 카테고리 | 이벤트 타입 | 예시 |
|----------|-------------|------|
| 봇 | bot_started, bot_stopped, bot_error | 봇 상태 변경 |
| 거래 | order_placed, order_filled, position_closed | 주문/포지션 이벤트 |
| 인증 | login_success, login_failed, token_expired | 인증 이벤트 |
| API | api_request, api_error, rate_limit_hit | API 호출 |
| 시그널 | signal_generated, signal_executed | 전략 시그널 |

---

## 에러 처리 패턴

### API 엔드포인트

```python
@router.post("/action")
async def action(
    payload: RequestSchema,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    # 1. 입력 검증
    if not validate_input(payload):
        raise ValidationError("Invalid input", field="field_name")

    # 2. 리소스 조회
    result = await session.execute(
        select(MyModel).where(MyModel.id == payload.id)
    )
    item = result.scalars().first()

    if not item:
        raise ResourceNotFoundError("Item", payload.id)

    # 3. 권한 확인
    if item.user_id != user_id:
        raise PermissionDeniedError("Not authorized to access this resource")

    # 4. 비즈니스 로직
    try:
        result = await some_external_call()
    except ExternalAPIError as e:
        logger.error("external_api_error", str(e))
        raise ExchangeAPIError("External", str(e))

    return {"success": True, "data": result}
```

### 서비스 레이어

```python
async def process_order(session: AsyncSession, user_id: int, order_data: dict):
    """주문 처리 서비스"""

    # 에러 발생 시 적절한 예외로 변환
    try:
        result = await bitget_client.place_order(...)
    except BitgetRateLimitError:
        logger.warning("rate_limit_hit", "Bitget rate limit exceeded", user_id=user_id)
        raise RateLimitExceededError("Exchange rate limit exceeded", limit=100, window="minute")
    except BitgetAuthenticationError:
        logger.error("auth_error", "Invalid API credentials", user_id=user_id)
        raise AuthenticationError("Invalid exchange API credentials")
    except BitgetNetworkError as e:
        logger.error("network_error", str(e), user_id=user_id)
        raise ExchangeAPIError("Bitget", f"Network error: {e}")

    return result
```

### try-except 블록

```python
async def safe_operation():
    """안전한 작업 패턴"""

    try:
        # 메인 로직
        result = await risky_operation()

    except ValidationError:
        # 검증 에러는 그대로 전파
        raise

    except ResourceNotFoundError:
        # 리소스 에러는 그대로 전파
        raise

    except Exception as e:
        # 예상치 못한 에러는 로깅 후 일반 에러로 변환
        logger.error(
            "unexpected_error",
            str(e),
            traceback=traceback.format_exc()
        )
        raise AppException(
            message="An unexpected error occurred",
            status_code=500,
            error_code="INTERNAL_ERROR"
        )
```

---

## Bitget 에러 분류 (utils/bitget_exceptions.py)

```python
def classify_bitget_error(error_code: str, error_msg: str) -> BitgetAPIError:
    """Bitget 에러 코드를 적절한 예외로 분류"""

    # Rate Limit
    if error_code in ["40014", "429"]:
        return BitgetRateLimitError(error_msg)

    # 인증 에러
    if error_code in ["40018", "40102", "40103"]:
        return BitgetAuthenticationError(error_msg)

    # 일반 API 에러
    return BitgetAPIError(error_msg, error_code=error_code)
```

---

## 베스트 프랙티스

1. **명확한 예외 사용**
   - 일반 `Exception` 대신 구체적인 예외 클래스 사용
   - 에러 메시지에 충분한 컨텍스트 포함

2. **로깅과 예외 분리**
   - 로깅: 내부 디버깅용 상세 정보
   - 예외: 클라이언트에 전달할 정보만

3. **에러 전파**
   - 복구 불가능한 에러는 빠르게 전파
   - 복구 가능한 에러는 적절히 처리

4. **사용자 친화적 메시지**
   - 기술적 세부사항 노출 금지
   - 해결 방법 힌트 제공 (details에 hint 포함)
