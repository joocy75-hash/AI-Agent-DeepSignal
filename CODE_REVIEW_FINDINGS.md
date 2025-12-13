# 🔍 코드 리뷰 결과 및 수정 가이드

**검토 날짜:** 2025-12-14
**검토 범위:** 전체 코드베이스 (24개 파일, 1,525줄 변경)
**검토 도구:** code-reviewer agent

---

## 📊 요약

| 심각도 | 개수 | 상태 |
|--------|------|------|
| Critical (90-100% 확신) | 3개 | ⚠️ 즉시 수정 필요 |
| Important (80-89% 확신) | 3개 | 📌 우선 수정 권장 |
| **총계** | **6개** | |

---

## ⚠️ Critical Issues (즉시 수정 필요)

### 1. JSON 파일 손상 [Confidence: 100%]

**파일:** `testsprite_tests/testsprite_frontend_test_plan.json:1`

**문제:**
```json
❌ 잘못된 형식
22[
  {
    "id": "TC001",
    ...
```

**영향:**
- 테스트 자동화 파싱 실패
- CI/CD 파이프라인 중단 가능

**수정 방법:**
```json
✅ 올바른 형식
[
  {
    "id": "TC001",
    ...
```

**수정 명령:**
```bash
# 첫 줄의 "22" 제거
sed -i '' '1s/^22//' testsprite_tests/testsprite_frontend_test_plan.json
```

**체크리스트:**
- [ ] JSON 파일에서 "22" 제거
- [ ] JSON 유효성 검증: `jq . testsprite_tests/testsprite_frontend_test_plan.json`
- [ ] Git commit 및 push

---

### 2. 보안: 하드코딩된 관리자 계정 [Confidence: 95%]

**파일:** `backend/scripts/init_admin.py:48-52`

**문제:**
```python
❌ 보안 취약점
hashed_password = JWTAuth.get_password_hash("admin123")
admin_user = User(
    email="admin@admin.com",
    password_hash=hashed_password,
    role="admin"
)
```

**영향:**
- 프로덕션 환경에서 약한 비밀번호 노출
- 무단 접근 위험
- 보안 감사 실패 가능

**수정 방법:**

**Step 1:** `backend/scripts/init_admin.py` 수정
```python
import os
import secrets

# 환경변수에서 읽기 (없으면 강력한 랜덤 비밀번호 생성)
admin_email = os.environ.get("ADMIN_EMAIL", "admin@admin.com")
admin_password = os.environ.get("ADMIN_INITIAL_PASSWORD")

if not admin_password:
    # 랜덤 비밀번호 생성 (22자)
    admin_password = secrets.token_urlsafe(16)
    print(f"⚠️  Generated random admin password: {admin_password}")
    print(f"⚠️  Please save this password and change it immediately!")

hashed_password = JWTAuth.get_password_hash(admin_password)
admin_user = User(
    email=admin_email,
    password_hash=hashed_password,
    role="admin"
)
```

**Step 2:** `.env` 파일에 추가
```bash
# Admin 초기 설정 (프로덕션에서는 반드시 변경)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_INITIAL_PASSWORD=YourStrongPassword123!@#
```

**Step 3:** Docker 배포 시 환경변수 설정
```bash
docker run -e ADMIN_EMAIL=admin@example.com \
           -e ADMIN_INITIAL_PASSWORD=SecurePass123! \
           your-image
```

**체크리스트:**
- [ ] `init_admin.py` 수정 (환경변수 사용)
- [ ] `.env.example` 업데이트
- [ ] 배포 문서에 환경변수 설명 추가
- [ ] 프로덕션 환경에 강력한 비밀번호 설정
- [ ] 첫 로그인 후 비밀번호 변경 강제 로직 추가 (선택)
- [ ] Git commit 및 push

---

### 3. 마이그레이션 실패 시 컨테이너 시작 불가 [Confidence: 90%]

**파일:** `backend/Dockerfile:63`

**문제:**
```dockerfile
❌ 단일 실패 지점
CMD alembic upgrade head && python scripts/init_admin.py && uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1
```

**영향:**
- DB 연결 일시적 문제로 전체 서비스 중단
- 마이그레이션 충돌 시 컨테이너 재시작 필요
- 운영 환경 다운타임 발생

**수정 방법:**

**Option 1: 재시도 로직 추가 (권장)**
```dockerfile
CMD sh -c '\
  echo "Starting database migration..." && \
  for i in 1 2 3 4 5; do \
    echo "Migration attempt $i/5..." && \
    alembic upgrade head && break || \
    (echo "Migration failed, retrying in 5 seconds..." && sleep 5); \
  done && \
  echo "Initializing admin user..." && \
  python scripts/init_admin.py && \
  echo "Starting application..." && \
  uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1'
```

**Option 2: 헬스체크 활용**
```dockerfile
# Dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s \
  CMD curl -f http://localhost:8000/health || exit 1

CMD sh -c '\
  alembic upgrade head || echo "⚠️  Migration failed but continuing..." && \
  python scripts/init_admin.py && \
  uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 1'
```

**Option 3: Init Container 패턴 (Kubernetes)**
```yaml
# kubernetes/init-migration.yaml
apiVersion: v1
kind: Pod
spec:
  initContainers:
  - name: migration
    image: your-app:latest
    command: ["alembic", "upgrade", "head"]
  containers:
  - name: app
    image: your-app:latest
    command: ["uvicorn", "src.main:app", "--host", "0.0.0.0"]
```

**체크리스트:**
- [ ] Dockerfile CMD 수정 (재시도 로직 추가)
- [ ] 헬스체크 엔드포인트 확인: `GET /health`
- [ ] 로컬에서 테스트 (DB 중지 후 컨테이너 시작)
- [ ] 마이그레이션 로그 확인
- [ ] Git commit 및 push
- [ ] 프로덕션 배포 전 스테이징 테스트

---

## 📌 Important Issues (우선 수정 권장)

### 4. AI API 비용 제어 부족 [Confidence: 85%]

**파일:** `backend/src/services/strategy_loader.py:96-97`

**문제:**
```python
# API 비용 절약: N번에 1번만 AI 호출 (기본 5번마다)
self.ai_call_interval = params.get("ai_call_interval", 5)
```

**영향:**
- DeepSeek API 호출 무제한으로 비용 폭증 가능
- 사용자별 사용량 추적 불가
- 예상치 못한 청구 금액

**수정 방법:**

**Step 1:** Rate Limiting 추가 (`backend/src/middleware/rate_limit_improved.py`)
```python
# 기존 코드에 추가
class RateLimitConfig:
    # DeepSeek API 제한
    USER_DEEPSEEK_PER_MINUTE = 10 if IS_DEVELOPMENT else 2
    USER_DEEPSEEK_PER_HOUR = 100 if IS_DEVELOPMENT else 20
    USER_DEEPSEEK_PER_DAY = 1000 if IS_DEVELOPMENT else 100

# Rate limiter 인스턴스 추가
deepseek_limiter_minute = RateLimiter("deepseek_minute", RateLimitConfig.USER_DEEPSEEK_PER_MINUTE, RateLimitConfig.WINDOW_MINUTE)
deepseek_limiter_hour = RateLimiter("deepseek_hour", RateLimitConfig.USER_DEEPSEEK_PER_HOUR, RateLimitConfig.WINDOW_HOUR)
deepseek_limiter_day = RateLimiter("deepseek_day", RateLimitConfig.USER_DEEPSEEK_PER_DAY, RateLimitConfig.WINDOW_DAY)
```

**Step 2:** API 호출 전 Rate Limit 체크
```python
# backend/src/services/deepseek_service.py
def _make_request(self, messages, temperature=0.7, max_tokens=2000, user_id=None):
    if user_id:
        from src.middleware.rate_limit_improved import deepseek_limiter_minute, deepseek_limiter_hour
        deepseek_limiter_minute.check(user_id)
        deepseek_limiter_hour.check(user_id)

    # 기존 코드...
```

**Step 3:** 사용량 추적 테이블 추가
```sql
-- alembic migration
CREATE TABLE ai_api_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    api_provider VARCHAR(50) NOT NULL,  -- 'deepseek', 'openai', etc.
    endpoint VARCHAR(100) NOT NULL,
    tokens_used INTEGER,
    estimated_cost DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_usage_user_date ON ai_api_usage(user_id, created_at);
```

**Step 4:** UI에 비용 경고 추가
```javascript
// frontend: AI 전략 생성 전 경고
if (userDailyApiCalls > 50) {
  showWarning("AI API 일일 사용량이 많습니다. 추가 비용이 발생할 수 있습니다.");
}
```

**체크리스트:**
- [ ] Rate limiting 설정 추가
- [ ] `deepseek_service.py`에 rate limit 체크 추가
- [ ] AI 사용량 추적 테이블 마이그레이션 생성
- [ ] 사용량 로깅 구현
- [ ] Admin 대시보드에 AI 사용량 모니터링 추가
- [ ] UI에 비용 경고 메시지 추가
- [ ] 문서 업데이트 (API 제한 안내)
- [ ] Git commit 및 push

---

### 5. 봇 자동 재시작 무한 루프 가능성 [Confidence: 82%]

**파일:** `backend/src/api/bot.py:449-451`

**문제:**
```python
except Exception as e:
    logger.error(f"Failed to auto-restart bot for user {user_id}: {e}")
    # 재시작 실패 시 DB를 False로 업데이트하지 않음 (다음 요청에서 재시도)
    is_actually_running = False
```

**영향:**
- 재시작 실패 시 매 API 요청마다 재시도 (무한 루프)
- 시스템 리소스 낭비
- 로그 파일 폭증

**수정 방법:**

**Step 1:** 재시도 추적 필드 추가
```python
# backend/src/database/models.py
class BotStatus(Base):
    __tablename__ = "bot_status"

    # 기존 필드...
    restart_attempts = Column(Integer, default=0)
    last_restart_attempt = Column(DateTime, nullable=True)
    max_restart_attempts = 3  # 최대 재시도 횟수
```

**Step 2:** 마이그레이션 생성
```bash
cd backend
DATABASE_URL="sqlite+aiosqlite:///./trading.db" \
ENCRYPTION_KEY="Dz9w_blEMa-tMD5hqK6V7yiaYecQBdsTaO0PJR3ESn8=" \
alembic revision -m "add_bot_restart_tracking"
```

**Step 3:** `bot.py` 수정
```python
# backend/src/api/bot.py
from datetime import datetime, timedelta

# 봇 상태 조회 시 재시작 로직
if status.is_running and not is_actually_running:
    # 최근 재시도 시간 확인 (5분 이내 재시도 방지)
    if status.last_restart_attempt:
        time_since_last = datetime.utcnow() - status.last_restart_attempt
        if time_since_last < timedelta(minutes=5):
            logger.warning(f"Skipping restart for user {user_id}: too soon since last attempt")
            is_actually_running = False
        else:
            # 재시도 횟수 체크
            if status.restart_attempts >= 3:
                logger.error(f"Max restart attempts reached for user {user_id}")
                status.is_running = False
                status.restart_attempts = 0
                await session.commit()
            else:
                # 재시작 시도
                try:
                    logger.info(f"Auto-restarting bot for user {user_id} (attempt {status.restart_attempts + 1}/3)")

                    # 재시도 정보 업데이트
                    status.restart_attempts += 1
                    status.last_restart_attempt = datetime.utcnow()
                    await session.commit()

                    # 실제 재시작
                    await _start_bot_internal(user_id, status.strategy_id, session)
                    is_actually_running = True

                    # 성공 시 카운터 리셋
                    status.restart_attempts = 0
                    await session.commit()

                except Exception as e:
                    logger.error(f"Failed to auto-restart bot for user {user_id}: {e}")
                    is_actually_running = False
                    # DB는 이미 업데이트됨 (restart_attempts 증가)
```

**Step 4:** 재시도 카운터 리셋 API 추가
```python
@router.post("/bot/reset-restart-counter")
async def reset_restart_counter(
    session: AsyncSession = Depends(get_session),
    user_id: int = Depends(get_current_user_id),
):
    """봇 재시작 카운터 초기화 (문제 해결 후 수동 리셋)"""
    status = await session.execute(
        select(BotStatus).where(BotStatus.user_id == user_id)
    )
    status = status.scalars().first()

    if status:
        status.restart_attempts = 0
        status.last_restart_attempt = None
        await session.commit()
        return {"success": True, "message": "재시작 카운터가 초기화되었습니다."}

    return {"success": False, "message": "봇 상태를 찾을 수 없습니다."}
```

**체크리스트:**
- [ ] `BotStatus` 모델에 필드 추가
- [ ] Alembic 마이그레이션 생성 및 실행
- [ ] `bot.py` 재시작 로직 수정
- [ ] 재시도 카운터 리셋 API 추가
- [ ] Frontend에 "재시작 재시도" 버튼 추가
- [ ] 로그 모니터링으로 무한 루프 검증
- [ ] 문서 업데이트
- [ ] Git commit 및 push

---

### 6. Frontend API 라우팅 불일치 [Confidence: 80%]

**파일:** `frontend/src/context/StrategyContext.jsx:78, 92`

**문제:**
```javascript
❌ /api/v1 prefix 누락
const response = await apiClient.patch(`/strategy/${strategyId}/toggle`);
const response = await apiClient.delete(`/ai/strategies/${strategyId}`);
```

**nginx 설정:**
```nginx
# frontend/nginx.conf
location /api/v1/ {
    proxy_pass http://backend:8000/api/v1/;
}
```

**영향:**
- 404 Not Found 오류
- 전략 활성화/비활성화 실패
- AI 전략 삭제 실패

**수정 방법:**

**Step 1:** `StrategyContext.jsx` 수정
```javascript
// frontend/src/context/StrategyContext.jsx

// toggleStrategy 함수 수정 (line 78)
const toggleStrategy = async (strategyId) => {
  try {
    setLoading(true);
    const response = await apiClient.patch(
      `/api/v1/strategy/${strategyId}/toggle`  // ✅ prefix 추가
    );

    if (response.data.success) {
      await fetchStrategies();
    }
    return response.data;
  } catch (error) {
    console.error('Toggle strategy error:', error);
    throw error;
  } finally {
    setLoading(false);
  }
};

// deleteStrategy 함수 수정 (line 92)
const deleteStrategy = async (strategyId) => {
  try {
    setLoading(true);
    const response = await apiClient.delete(
      `/api/v1/ai/strategies/${strategyId}`  // ✅ prefix 추가
    );

    if (response.data.success) {
      await fetchStrategies();
    }
    return response.data;
  } catch (error) {
    console.error('Delete strategy error:', error);
    throw error;
  } finally {
    setLoading(false);
  }
};
```

**Step 2:** 전체 API 엔드포인트 검증
```bash
# 모든 API 호출에서 /api/v1 prefix 검색
cd frontend
grep -r "apiClient\." src/ | grep -v "/api/v1" | grep -E "(get|post|put|patch|delete)\("
```

**Step 3:** API Client 기본 URL 확인
```javascript
// frontend/src/api/apiClient.js 확인
const apiClient = axios.create({
  baseURL: '/api/v1',  // ✅ 이미 설정되어 있다면 상대 경로만 사용
  timeout: 30000,
});

// 이 경우 호출 시:
apiClient.patch(`/strategy/${strategyId}/toggle`);  // ✅ OK
```

**체크리스트:**
- [ ] `StrategyContext.jsx`의 API 경로 수정
- [ ] 전체 frontend 코드에서 API prefix 누락 검색
- [ ] `apiClient.js` baseURL 설정 확인
- [ ] 브라우저 개발자 도구에서 네트워크 요청 확인
- [ ] 전략 토글 기능 테스트
- [ ] AI 전략 삭제 기능 테스트
- [ ] Git commit 및 push

---

## ✅ 전체 수정 체크리스트

### Phase 1: Critical Issues (즉시)
- [ ] **Issue #1:** JSON 파일 손상 수정
- [ ] **Issue #2:** Admin 계정 환경변수화
- [ ] **Issue #3:** Dockerfile 재시도 로직 추가

### Phase 2: Important Issues (1주일 내)
- [ ] **Issue #4:** AI API Rate Limiting 구현
- [ ] **Issue #5:** 봇 재시작 제한 구현
- [ ] **Issue #6:** Frontend API 라우팅 수정

### Phase 3: 검증 및 배포
- [ ] 로컬 환경 테스트
- [ ] 스테이징 환경 배포 및 테스트
- [ ] 프로덕션 배포
- [ ] 모니터링 설정 확인

---

## 📝 수정 후 검증 방법

### 1. JSON 파일 검증
```bash
jq . testsprite_tests/testsprite_frontend_test_plan.json
# 오류 없이 JSON 출력되면 성공
```

### 2. Admin 계정 보안 검증
```bash
# .env 파일 확인
cat backend/.env | grep ADMIN

# 랜덤 비밀번호 생성 확인
docker logs <container_id> | grep "Generated random admin password"
```

### 3. 마이그레이션 재시도 검증
```bash
# DB 서비스 중지 후 컨테이너 시작
docker-compose stop db
docker-compose up backend

# 로그에서 재시도 확인
# "Migration attempt 1/5..."
# "Migration attempt 2/5..."
```

### 4. API Rate Limiting 검증
```bash
# 분당 10회 요청 (제한 확인)
for i in {1..15}; do
  curl -X POST http://localhost:8000/api/v1/ai/strategies/generate \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"count": 3}'
  echo "Request $i"
done
# 11번째 요청부터 429 Too Many Requests 응답 예상
```

### 5. 봇 재시작 제한 검증
```bash
# 봇 시작 후 프로세스 강제 종료 (3회 반복)
# 4번째 시도에서는 자동 재시작 안 됨을 확인
```

### 6. Frontend API 라우팅 검증
```bash
# 브라우저 개발자 도구 > Network 탭
# 전략 토글 클릭 시 요청 URL 확인:
# ✅ PATCH /api/v1/strategy/1/toggle
# ❌ PATCH /strategy/1/toggle (404)
```

---

## 📚 참고 문서

- [Alembic Migration Guide](https://alembic.sqlalchemy.org/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Rate Limiting Strategies](https://redis.io/docs/manual/patterns/rate-limiter/)
- [DeepSeek API Documentation](https://www.deepseek.com/docs/api-reference)

---

## 🔗 관련 파일

```
/Users/mr.joo/Desktop/auto-dashboard/
├── backend/
│   ├── Dockerfile                              # Issue #3
│   ├── scripts/init_admin.py                   # Issue #2
│   ├── src/
│   │   ├── api/
│   │   │   └── bot.py                          # Issue #5
│   │   ├── services/
│   │   │   ├── deepseek_service.py            # Issue #4
│   │   │   └── strategy_loader.py             # Issue #4
│   │   └── middleware/
│   │       └── rate_limit_improved.py         # Issue #4 (수정 필요)
│   └── .env.example                            # Issue #2 (업데이트 필요)
├── frontend/
│   ├── nginx.conf                              # Issue #6 참조
│   └── src/
│       └── context/StrategyContext.jsx        # Issue #6
└── testsprite_tests/
    └── testsprite_frontend_test_plan.json     # Issue #1
```

---

## 💡 추가 권장사항

1. **CI/CD 파이프라인 추가**
   - JSON 유효성 검증
   - Security scanning (hardcoded secrets)
   - Migration dry-run 테스트

2. **모니터링 강화**
   - AI API 사용량 대시보드
   - 봇 재시작 알림 (Slack, Email)
   - 마이그레이션 실패 알림

3. **문서화**
   - 환경변수 설정 가이드
   - API Rate Limit 정책 문서
   - 장애 복구 매뉴얼

---

**작성자:** Code Review Agent
**마지막 업데이트:** 2025-12-14
**다음 리뷰 예정:** 수정 완료 후
