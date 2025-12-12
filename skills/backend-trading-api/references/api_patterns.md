# API 엔드포인트 패턴

## 현재 프로젝트의 API 구조

### 인증 엔드포인트 (api/auth.py)

```python
POST   /auth/register        # 회원가입
POST   /auth/login           # 로그인 (2FA 지원)
POST   /auth/change-password # 비밀번호 변경

# 2FA
POST   /2fa/enable           # 2FA 활성화 (QR 코드 생성)
POST   /2fa/verify           # 2FA 검증
POST   /2fa/disable          # 2FA 비활성화
```

### 봇 제어 엔드포인트 (api/bot.py)

```python
POST   /bot/start            # 봇 시작 (리소스 제한 체크)
POST   /bot/stop             # 봇 중지 + 포지션 청산
GET    /bot/status           # 봇 상태 조회 (캐시됨, 30초 TTL)
```

### 시장 데이터 엔드포인트

```python
GET    /chart/candles        # OHLCV 캔들 데이터 (캐시)
GET    /market/tickers       # 티커 목록
GET    /market/24h-stats     # 24시간 통계
```

### 거래 관련 엔드포인트

```python
GET    /account/balance      # 잔고 조회
GET    /account/positions    # 포지션 조회
POST   /account/save_keys    # API 키 저장 (암호화)
GET    /order/list           # 주문 목록
```

### 백테스트 엔드포인트

```python
POST   /backtest/run         # 백테스트 실행 (Rate Limit: 시간당 10회)
GET    /backtest/result/{id} # 결과 조회
GET    /backtest/history     # 백테스트 히스토리
```

### 관리자 엔드포인트

```python
GET    /admin/users          # 사용자 목록 (RBAC)
POST   /admin/users/{id}/suspend  # 사용자 정지
GET    /admin/bots           # 모든 봇 상태
POST   /admin/bots/{id}/stop # 봇 강제 정지
GET    /admin/analytics/users # 사용자별 분석
```

---

## 엔드포인트 작성 템플릿

### 1. 기본 CRUD 엔드포인트

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.db import get_session
from ..database.models import MyModel
from ..schemas.my_schema import CreateRequest, UpdateRequest, ItemResponse, ListResponse
from ..utils.jwt_auth import get_current_user_id
from ..utils.structured_logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/items", tags=["items"])


@router.post("", response_model=ItemResponse)
async def create_item(
    payload: CreateRequest,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """아이템 생성"""
    item = MyModel(
        user_id=user_id,
        name=payload.name,
        value=payload.value,
    )
    session.add(item)
    await session.commit()
    await session.refresh(item)

    logger.info("item_created", f"Item created: {item.id}", user_id=user_id)
    return ItemResponse(id=item.id, name=item.name, value=item.value)


@router.get("", response_model=ListResponse)
async def list_items(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """아이템 목록 조회"""
    offset = (page - 1) * limit

    result = await session.execute(
        select(MyModel)
        .where(MyModel.user_id == user_id)
        .order_by(MyModel.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    items = result.scalars().all()

    return ListResponse(items=[...], page=page, limit=limit)


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """아이템 상세 조회"""
    result = await session.execute(
        select(MyModel).where(
            MyModel.id == item_id,
            MyModel.user_id == user_id
        )
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return ItemResponse(...)


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    payload: UpdateRequest,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """아이템 수정"""
    result = await session.execute(
        select(MyModel).where(
            MyModel.id == item_id,
            MyModel.user_id == user_id
        )
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # 업데이트
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    await session.commit()
    await session.refresh(item)

    return ItemResponse(...)


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """아이템 삭제"""
    result = await session.execute(
        select(MyModel).where(
            MyModel.id == item_id,
            MyModel.user_id == user_id
        )
    )
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    await session.delete(item)
    await session.commit()

    return {"success": True, "message": "Item deleted"}
```

### 2. 관리자 전용 엔드포인트

```python
from ..utils.auth_dependencies import require_admin

@router.get("/admin/overview")
async def admin_overview(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(require_admin),  # 관리자 권한 필요
):
    """관리자 대시보드 개요"""
    # 관리자 전용 로직
    pass
```

### 3. Rate Limiting 적용

```python
from ..middleware.rate_limit_improved import RateLimiter

rate_limiter = RateLimiter()

@router.post("/expensive-operation")
async def expensive_operation(
    request: Request,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """비용이 높은 작업 (Rate Limit 적용)"""

    # Rate Limit 체크
    await rate_limiter.check_user_limit(
        user_id=user_id,
        action="expensive_operation",
        limit=10,
        window="hour"
    )

    # 작업 수행
    pass
```

### 4. 캐싱 적용

```python
from ..utils.cache_manager import cache_manager, make_cache_key

@router.get("/cached-data")
async def get_cached_data(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """캐시된 데이터 조회"""

    # 캐시 확인
    cache_key = make_cache_key("cached_data", user_id)
    cached = await cache_manager.get(cache_key)

    if cached is not None:
        return cached

    # 데이터 조회
    data = await fetch_expensive_data(session, user_id)

    # 캐시 저장 (60초 TTL)
    await cache_manager.set(cache_key, data, ttl=60)

    return data
```

---

## 응답 형식 표준

### 성공 응답

```json
{
    "success": true,
    "data": {
        "id": 1,
        "name": "Item 1"
    }
}
```

### 에러 응답 (middleware/error_handler.py에서 자동 처리)

```json
{
    "success": false,
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input",
        "details": {
            "field": "symbol",
            "reason": "Symbol must end with USDT"
        },
        "timestamp": "2025-12-02T10:00:00",
        "request_id": "abc123"
    }
}
```
