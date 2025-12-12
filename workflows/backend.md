---
description: 백엔드 API 개발 - 새 엔드포인트 추가 절차
---

# 🔧 백엔드 API 개발 워크플로우

## 📋 사전 준비

### 1. SKILL 파일 읽기

// turbo

- `skills/backend-trading-api/SKILL.md` 읽기

### 2. 기존 API 구조 파악

- `backend/src/api/` 디렉토리 확인
- 유사한 엔드포인트 참조

## 🛠️ 개발 단계

### Step 1: Pydantic 스키마 정의

```
위치: backend/src/schemas/
파일: {feature}_schema.py
```

```python
from pydantic import BaseModel, Field, field_validator

class RequestSchema(BaseModel):
    field: str = Field(..., min_length=1)
    
    @field_validator('field')
    @classmethod
    def validate_field(cls, v):
        # 검증 로직
        return v
```

### Step 2: API 라우터 생성

```
위치: backend/src/api/
파일: {feature}.py
```

```python
from fastapi import APIRouter, Depends
from ..utils.jwt_auth import get_current_user_id

router = APIRouter(prefix="/{feature}", tags=["{Feature}"])

@router.post("/action")
async def action_endpoint(
    payload: RequestSchema,
    user_id: int = Depends(get_current_user_id),
):
    pass
```

### Step 3: 라우터 등록

```
위치: backend/src/main.py
```

```python
from .api.{feature} import router as {feature}_router
app.include_router({feature}_router)
```

### Step 4: 서비스 로직 구현 (필요시)

```
위치: backend/src/services/
파일: {feature}_service.py
```

### Step 5: 테스트

```bash
# 서버 재시작
python -m uvicorn src.main:app --reload --port 8000

# API 테스트
curl -X POST http://localhost:8000/{feature}/action \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}'
```

## ✅ 완료 체크리스트

- [ ] Pydantic 스키마 정의
- [ ] 입력 검증 로직 추가
- [ ] API 라우터 생성
- [ ] `get_current_user_id` 의존성 추가
- [ ] 라우터 등록 (main.py)
- [ ] 에러 핸들링 추가
- [ ] 로깅 추가
- [ ] API 테스트 완료
