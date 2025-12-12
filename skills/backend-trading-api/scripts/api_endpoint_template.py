"""
API 엔드포인트 템플릿

사용법:
1. 이 파일을 backend/src/api/ 디렉토리에 복사
2. {RESOURCE_NAME} 을 실제 리소스명으로 변경
3. main.py에 라우터 등록
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

from ..database.db import get_session
from ..database.models import Base  # TODO: 실제 모델로 교체
from ..utils.jwt_auth import get_current_user_id
from ..utils.structured_logging import get_logger
from ..utils.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    PermissionDeniedError,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/{resource_name}", tags=["{resource_name}"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Pydantic 스키마
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class CreateRequest(BaseModel):
    """생성 요청 스키마"""

    name: str = Field(..., min_length=1, max_length=100, description="리소스명")
    value: float = Field(..., gt=0, description="값")
    description: Optional[str] = Field(None, max_length=500, description="설명")


class UpdateRequest(BaseModel):
    """수정 요청 스키마"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    value: Optional[float] = Field(None, gt=0)
    description: Optional[str] = Field(None, max_length=500)


class ItemResponse(BaseModel):
    """단일 아이템 응답"""

    id: int
    name: str
    value: float
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ListResponse(BaseModel):
    """목록 응답"""

    items: List[ItemResponse]
    total: int
    page: int
    limit: int
    pages: int


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# CRUD 엔드포인트
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post("", response_model=ItemResponse)
async def create_item(
    payload: CreateRequest,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    리소스 생성

    - **name**: 리소스명 (필수)
    - **value**: 값 (필수, 0보다 커야 함)
    - **description**: 설명 (선택)
    """
    logger.info(
        "create_item_requested",
        f"Creating item for user {user_id}",
        user_id=user_id,
        name=payload.name,
    )

    # TODO: 실제 모델로 교체
    # item = MyModel(
    #     user_id=user_id,
    #     name=payload.name,
    #     value=payload.value,
    #     description=payload.description,
    # )
    # session.add(item)
    # await session.commit()
    # await session.refresh(item)

    # logger.info("item_created", f"Item created: {item.id}", user_id=user_id, item_id=item.id)

    # return ItemResponse.model_validate(item)

    raise NotImplementedError("TODO: Implement create logic")


@router.get("", response_model=ListResponse)
async def list_items(
    page: int = Query(1, ge=1, description="페이지 번호"),
    limit: int = Query(20, ge=1, le=100, description="페이지당 아이템 수"),
    search: Optional[str] = Query(None, description="검색어"),
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    리소스 목록 조회

    - **page**: 페이지 번호 (기본값: 1)
    - **limit**: 페이지당 아이템 수 (기본값: 20, 최대: 100)
    - **search**: 검색어 (선택)
    """
    offset = (page - 1) * limit

    # 기본 쿼리
    # query = select(MyModel).where(MyModel.user_id == user_id)

    # 검색 필터
    # if search:
    #     query = query.where(MyModel.name.ilike(f"%{search}%"))

    # 전체 개수 조회
    # count_result = await session.execute(
    #     select(func.count(MyModel.id)).where(MyModel.user_id == user_id)
    # )
    # total = count_result.scalar() or 0

    # 페이지네이션
    # result = await session.execute(
    #     query.order_by(MyModel.created_at.desc()).offset(offset).limit(limit)
    # )
    # items = result.scalars().all()

    # pages = (total + limit - 1) // limit

    # return ListResponse(
    #     items=[ItemResponse.model_validate(item) for item in items],
    #     total=total,
    #     page=page,
    #     limit=limit,
    #     pages=pages,
    # )

    raise NotImplementedError("TODO: Implement list logic")


@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    리소스 상세 조회

    - **item_id**: 리소스 ID
    """
    # result = await session.execute(
    #     select(MyModel).where(MyModel.id == item_id)
    # )
    # item = result.scalars().first()

    # if not item:
    #     raise ResourceNotFoundError("Item", item_id)

    # # 권한 확인
    # if item.user_id != user_id:
    #     raise PermissionDeniedError("Not authorized to access this resource")

    # return ItemResponse.model_validate(item)

    raise NotImplementedError("TODO: Implement get logic")


@router.put("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: int,
    payload: UpdateRequest,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    리소스 수정

    - **item_id**: 리소스 ID
    - 수정할 필드만 전송 (부분 업데이트 지원)
    """
    logger.info(
        "update_item_requested",
        f"Updating item {item_id}",
        user_id=user_id,
        item_id=item_id,
    )

    # result = await session.execute(
    #     select(MyModel).where(MyModel.id == item_id)
    # )
    # item = result.scalars().first()

    # if not item:
    #     raise ResourceNotFoundError("Item", item_id)

    # if item.user_id != user_id:
    #     raise PermissionDeniedError("Not authorized to modify this resource")

    # # 부분 업데이트
    # update_data = payload.model_dump(exclude_unset=True)
    # for field, value in update_data.items():
    #     setattr(item, field, value)

    # await session.commit()
    # await session.refresh(item)

    # logger.info("item_updated", f"Item updated: {item.id}", user_id=user_id, item_id=item.id)

    # return ItemResponse.model_validate(item)

    raise NotImplementedError("TODO: Implement update logic")


@router.delete("/{item_id}")
async def delete_item(
    item_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    리소스 삭제

    - **item_id**: 리소스 ID
    """
    logger.info(
        "delete_item_requested",
        f"Deleting item {item_id}",
        user_id=user_id,
        item_id=item_id,
    )

    # result = await session.execute(
    #     select(MyModel).where(MyModel.id == item_id)
    # )
    # item = result.scalars().first()

    # if not item:
    #     raise ResourceNotFoundError("Item", item_id)

    # if item.user_id != user_id:
    #     raise PermissionDeniedError("Not authorized to delete this resource")

    # await session.delete(item)
    # await session.commit()

    # logger.info("item_deleted", f"Item deleted: {item_id}", user_id=user_id, item_id=item_id)

    # return {"success": True, "message": f"Item {item_id} deleted"}

    raise NotImplementedError("TODO: Implement delete logic")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 추가 엔드포인트 (필요에 따라)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@router.post("/{item_id}/activate")
async def activate_item(
    item_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    리소스 활성화
    """
    # TODO: 활성화 로직
    raise NotImplementedError("TODO: Implement activation logic")


@router.post("/{item_id}/deactivate")
async def deactivate_item(
    item_id: int,
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """
    리소스 비활성화
    """
    # TODO: 비활성화 로직
    raise NotImplementedError("TODO: Implement deactivation logic")
