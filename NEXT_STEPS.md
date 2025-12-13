# 🚀 다음 작업자를 위한 가이드

**시작 전 필독:** `CODE_REVIEW_FINDINGS.md` 파일을 먼저 읽어주세요.

---

## ⚡ 빠른 시작 체크리스트

### 즉시 수정 필요 (Critical - 30분 소요)

```bash
# 1️⃣ JSON 파일 수정 (1분)
cd /Users/mr.joo/Desktop/auto-dashboard
sed -i '' '1s/^22//' testsprite_tests/testsprite_frontend_test_plan.json
jq . testsprite_tests/testsprite_frontend_test_plan.json  # 검증

# 2️⃣ Admin 환경변수화 (15분)
# - backend/scripts/init_admin.py 수정
# - backend/.env 업데이트
# - 상세 내용: CODE_REVIEW_FINDINGS.md #2 참조

# 3️⃣ Dockerfile 재시도 로직 (10분)
# - backend/Dockerfile 수정
# - 상세 내용: CODE_REVIEW_FINDINGS.md #3 참조

# ✅ 커밋
git add .
git commit -m "fix: Critical issues - JSON corruption, admin security, docker retry"
git push
```

---

## 📋 우선순위별 작업 순서

| 순위 | 작업 | 예상 시간 | 중요도 |
|------|------|-----------|--------|
| 1 | JSON 파일 수정 | 1분 | 🔴 Critical |
| 2 | Admin 계정 보안 | 15분 | 🔴 Critical |
| 3 | Dockerfile 재시도 로직 | 10분 | 🔴 Critical |
| 4 | Frontend API 라우팅 수정 | 10분 | 🟡 Important |
| 5 | AI API Rate Limiting | 2시간 | 🟡 Important |
| 6 | 봇 재시작 제한 | 1.5시간 | 🟡 Important |

---

## 📂 수정해야 할 파일 목록

### Critical Issues
- [ ] `testsprite_tests/testsprite_frontend_test_plan.json` (Issue #1)
- [ ] `backend/scripts/init_admin.py` (Issue #2)
- [ ] `backend/.env.example` (Issue #2)
- [ ] `backend/Dockerfile` (Issue #3)

### Important Issues
- [ ] `frontend/src/context/StrategyContext.jsx` (Issue #6)
- [ ] `backend/src/middleware/rate_limit_improved.py` (Issue #4)
- [ ] `backend/src/services/deepseek_service.py` (Issue #4)
- [ ] `backend/src/database/models.py` (Issue #5)
- [ ] `backend/src/api/bot.py` (Issue #5)

---

## 🔧 수정 템플릿

### Issue #1: JSON 파일 수정
```bash
# 한 줄 명령어로 수정
sed -i '' '1s/^22//' testsprite_tests/testsprite_frontend_test_plan.json
```

### Issue #2: Admin 보안 (init_admin.py)
```python
# 파일 시작 부분에 추가
import os
import secrets

# get_or_create_admin() 함수 내부 수정
admin_email = os.environ.get("ADMIN_EMAIL", "admin@admin.com")
admin_password = os.environ.get("ADMIN_INITIAL_PASSWORD")

if not admin_password:
    admin_password = secrets.token_urlsafe(16)
    print(f"⚠️  Generated admin password: {admin_password}")

hashed_password = JWTAuth.get_password_hash(admin_password)
```

### Issue #3: Dockerfile 재시도
```dockerfile
CMD sh -c '\
  for i in 1 2 3; do \
    alembic upgrade head && break || sleep 5; \
  done && \
  python scripts/init_admin.py && \
  uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1'
```

### Issue #6: Frontend API 경로
```javascript
// StrategyContext.jsx
const toggleStrategy = async (strategyId) => {
  const response = await apiClient.patch(`/api/v1/strategy/${strategyId}/toggle`);
  // ...
};

const deleteStrategy = async (strategyId) => {
  const response = await apiClient.delete(`/api/v1/ai/strategies/${strategyId}`);
  // ...
};
```

---

## 🧪 테스트 명령어

### 전체 수정 후 테스트
```bash
# 1. JSON 검증
jq . testsprite_tests/testsprite_frontend_test_plan.json

# 2. 백엔드 빌드 테스트
cd backend
docker build -t trading-backend .

# 3. 마이그레이션 테스트 (DB 없을 때)
docker run --rm trading-backend alembic upgrade head
# 재시도 로그 확인

# 4. Frontend 빌드
cd frontend
npm run build

# 5. 전체 시스템 시작
cd ..
docker-compose up -d

# 6. 로그 확인
docker-compose logs -f backend
```

### API 테스트
```bash
# Admin 로그인
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@admin.com", "password": "YOUR_PASSWORD"}' \
  | jq -r '.access_token')

# 전략 토글 (Frontend API 수정 검증)
curl -X PATCH http://localhost:8000/api/v1/strategy/1/toggle \
  -H "Authorization: Bearer $TOKEN"

# AI 전략 생성 (Rate Limit 테스트 - Issue #4 수정 후)
curl -X POST http://localhost:8000/api/v1/ai/strategies/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"count": 3}'
```

---

## 📖 상세 문서 위치

- **전체 코드 리뷰 결과:** `CODE_REVIEW_FINDINGS.md`
- **수정 방법 상세:** `CODE_REVIEW_FINDINGS.md` 각 Issue 섹션
- **검증 방법:** `CODE_REVIEW_FINDINGS.md` > "수정 후 검증 방법"

---

## 💬 도움이 필요하면

1. `CODE_REVIEW_FINDINGS.md` 파일의 해당 Issue 섹션 참조
2. 각 Issue에 상세한 수정 방법 포함
3. "체크리스트" 항목 하나씩 진행

---

## 🎯 작업 완료 확인

### Phase 1 완료 조건 (Critical)
- [ ] JSON 파일 유효성 검증 통과
- [ ] Admin 계정이 환경변수로 설정됨
- [ ] Docker 컨테이너가 DB 없이도 재시도 후 시작
- [ ] Git에 커밋 및 푸시

### Phase 2 완료 조건 (Important)
- [ ] Frontend 전략 토글/삭제 동작
- [ ] AI API Rate Limit 테스트 통과 (429 응답 확인)
- [ ] 봇 재시작이 3회 후 중단됨
- [ ] Git에 커밋 및 푸시

### Phase 3 완료 조건 (배포)
- [ ] 로컬 테스트 통과
- [ ] 스테이징 배포 성공
- [ ] 프로덕션 배포 성공
- [ ] 모니터링 정상

---

**작성일:** 2025-12-14
**예상 총 작업 시간:** 5-6시간
**우선순위 작업 시간:** 30분

좋은 작업 되세요! 🚀
