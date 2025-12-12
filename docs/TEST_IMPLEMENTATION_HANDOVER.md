# 테스트 구현 작업 인수인계

## 작업 일시

2025-12-12

## 작업 개요

백엔드 API에 대한 Unit 테스트 및 Integration 테스트를 구현했습니다.

## 완료된 작업

### 1. 테스트 환경 설정 (conftest.py)

**파일**: `backend/tests/conftest.py`

주요 변경사항:

- `ASGITransport`를 사용하여 httpx AsyncClient 설정
- 테스트용 FastAPI 앱 생성 (lifespan 없이 수동으로 state 설정)
- `BotManager` mock 설정 (runner.is_running, start_bot, stop_bot 등)
- 예외 핸들러 등록 (`register_exception_handlers`)
- DB 세션 오버라이드 설정

```python
# 핵심 변경 부분
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, AsyncMock

app = FastAPI()

# BotManager mock 설정
mock_runner = MagicMock()
mock_runner.is_running = MagicMock(return_value=False)
app.state.bot_manager = MagicMock()
app.state.bot_manager.runner = mock_runner

transport = ASGITransport(app=app, raise_app_exceptions=False)
async with AsyncClient(transport=transport, base_url="http://test") as client:
    yield client
```

### 2. Auth API 테스트 (14개 테스트)

**파일**: `backend/tests/unit/test_auth_api.py`

테스트 클래스:

- `TestAuthRegister`: 회원가입 테스트 (5개)
  - 성공, 중복 이메일, 비밀번호 불일치, 약한 비밀번호, 잘못된 이메일
- `TestAuthLogin`: 로그인 테스트 (4개)
  - 성공, 잘못된 비밀번호, 존재하지 않는 사용자, 누락된 필드
- `TestAuthUsers`: 사용자 목록 조회 테스트 (3개) - 관리자 전용
  - 관리자 접근 성공, 일반 사용자 접근 거부, 인증 없음 거부
- `TestAuthChangePassword`: 비밀번호 변경 테스트 (2개)
  - 성공, 현재 비밀번호 틀림

### 3. Bot API 테스트 (7개 테스트, 1개 스킵)

**파일**: `backend/tests/unit/test_bot_api.py`

테스트 클래스:

- `TestBotStatus`: 봇 상태 조회 테스트 (2개)
  - 초기 상태 (정지됨), 인증 없이 조회 실패
- `TestBotStartStop`: 봇 시작/정지 테스트 (4개)
  - API 키 없이 시작 실패, 인증 없이 시작 실패, 인증 없이 정지 실패, 실행 중 아닐 때 정지
- `TestBotStartWithMock`: Mock 테스트 (1개 - 스킵됨)
  - 복잡한 mocking 필요하여 스킵

### 4. Annotations API 테스트 (13개 테스트)

**파일**: `backend/tests/unit/test_annotations_api.py`

테스트 클래스:

- `TestAnnotationsCRUD`: CRUD 테스트 (6개)
  - 생성, price_level 생성, 심볼별 조회, 빈 결과 조회, 수정, 삭제
- `TestAnnotationsToggle`: 토글 테스트 (2개)
  - 표시/숨김 토글, 잠금/해제 토글
- `TestAnnotationsAlerts`: 알림 테스트 (2개)
  - 알림 리셋, 비-price_level 알림 리셋 실패
- `TestAnnotationsAuth`: 인증 테스트 (3개)
  - 인증 없이 조회 실패, 인증 없이 생성 실패, 사용자 간 격리

### 5. Integration 테스트 (7개 테스트)

**파일**: `backend/tests/integration/test_trading_workflow.py`

테스트 클래스:

- `TestUserRegistrationToTradingWorkflow`: 전체 워크플로우 테스트 (2개)
  - 사용자 설정 전체 흐름 (회원가입 → 전략 생성 → 차트 → 어노테이션 → 봇 상태)
  - 다중 사용자 격리 테스트
- `TestAnnotationWorkflow`: 어노테이션 워크플로우 (2개)
  - 어노테이션 라이프사이클 (생성 → 수정 → 토글 → 삭제)
  - 심볼별 다중 어노테이션 관리
- `TestStrategyManagement`: 전략 관리 테스트 (1개)
  - 전략 CRUD 작업
- `TestAPIPerformance`: 성능 테스트 (2개)
  - 배치 생성 성능, 동시 요청 처리

### 6. pytest.ini 업데이트

**파일**: `backend/pytest.ini`

추가된 마커:

```ini
markers =
    unit: Unit tests (단위 테스트)
    integration: Integration tests (통합 테스트)
    slow: Slow tests (느린 테스트)
    auth: Authentication tests (인증 테스트)
    api: API endpoint tests (API 테스트)
    database: Database tests (DB 테스트)
    performance: Performance tests (성능 테스트)
```

## 발견된 API 엔드포인트 차이점

테스트 작성 중 실제 API와 다른 점을 발견하여 수정했습니다:

| 예상 엔드포인트 | 실제 엔드포인트 |
|---------------|---------------|
| `/auth/me` | 존재하지 않음 (사용자 정보 조회 없음) |
| `/strategy` (POST) | `/strategy/create` |
| `/strategy` (GET) | `/strategy/list` |
| `/strategy/{id}` (PUT) | `/strategy/update/{id}` (POST) |
| `alert_direction: "up"` | `alert_direction: "above"` 또는 `"below"` |

## 다음 작업자를 위한 가이드

### 전체 테스트 실행 명령어

```bash
cd /Users/mr.joo/Desktop/auto-dashboard/backend

# 전체 테스트 실행
python -m pytest tests/ -v --no-cov

# Unit 테스트만 실행
python -m pytest tests/unit/ -v --no-cov

# Integration 테스트만 실행
python -m pytest tests/integration/ -v --no-cov

# 특정 마커로 실행
python -m pytest -m "unit and api" -v --no-cov
python -m pytest -m "integration" -v --no-cov
python -m pytest -m "performance" -v --no-cov

# 커버리지 포함 실행
python -m pytest tests/ -v --cov=src --cov-report=html
```

### 예상 결과

개별 테스트 실행 결과:

- `test_auth_api.py`: 14 passed
- `test_bot_api.py`: 6 passed, 1 skipped
- `test_annotations_api.py`: 13 passed
- `test_trading_workflow.py`: 7 passed

**총 예상**: 40 passed, 1 skipped

### 추가 개선 사항 (선택적)

1. **스킵된 테스트 구현**: `TestBotStartWithMock.test_start_bot_with_mocked_exchange`
   - 복잡한 bot_manager mocking 필요

2. **추가 테스트 권장**:
   - Chart API 테스트 (`/chart/candles`)
   - Account API 테스트 (`/account/save_keys`)
   - Trades API 테스트 (`/trades`)
   - Positions API 테스트 (`/positions`)

3. **E2E 테스트 추가**:
   - 실제 거래소 API mock을 사용한 전체 봇 실행 테스트

## 파일 목록

```
backend/tests/
├── conftest.py                          # 테스트 설정 및 픽스처
├── unit/
│   ├── test_auth_api.py                 # Auth API 단위 테스트
│   ├── test_bot_api.py                  # Bot API 단위 테스트
│   └── test_annotations_api.py          # Annotations API 단위 테스트
└── integration/
    └── test_trading_workflow.py         # 통합 테스트
```

## TestSprite 테스트 (10개 테스트)

### 위치

`testsprite_tests/` 폴더

### 테스트 목록

| ID | 파일명 | 설명 |
|----|--------|------|
| TC001 | `TC001_health_check_endpoint_returns_system_status.py` | 헬스 체크 엔드포인트 테스트 |
| TC002 | `TC002_user_registration_with_valid_data.py` | 사용자 회원가입 테스트 |
| TC003 | `TC003_user_login_returns_jwt_tokens.py` | 로그인 및 JWT 토큰 반환 테스트 |
| TC004 | `TC004_refresh_access_token_with_valid_refresh_token.py` | Refresh Token 갱신 테스트 |
| TC005 | `TC005_setup_two_factor_authentication_returns_qr_and_secret.py` | 2FA 설정 테스트 |
| TC006 | `TC006_verify_two_factor_authentication_code.py` | 2FA 코드 검증 테스트 (pyotp 필요) |
| TC007 | `TC007_save_exchange_api_keys_successfully.py` | 거래소 API 키 저장 테스트 |
| TC008 | `TC008_start_trading_bot_with_valid_parameters.py` | 봇 시작 테스트 |
| TC009 | `TC009_submit_new_trading_order.py` | 주문 제출 테스트 |
| TC010 | `TC010_get_candle_data_for_symbol.py` | 캔들 데이터 조회 테스트 |

### 실행 방법

```bash
cd /Users/mr.joo/Desktop/auto-dashboard

# 개별 테스트 실행
python testsprite_tests/TC001_health_check_endpoint_returns_system_status.py
python testsprite_tests/TC002_user_registration_with_valid_data.py

# 모든 테스트 실행 (pytest 사용)
python -m pytest testsprite_tests/ -v

# TC006 실행 시 pyotp 필요
pip install pyotp
```

### 필수 조건

- 백엔드 서버가 `http://localhost:8000`에서 실행 중이어야 함
- TC006 테스트는 `pyotp` 패키지 필요
- 대부분의 테스트는 새 사용자를 생성하므로 중복 실행 가능

### 수정 내역 (2025-12-12)

| 테스트 | 수정 사항 |
|--------|----------|
| TC002 | 필드명 변경 (`username` → `name`, `phone` 추가), 응답 코드 `201` → `200` |
| TC003 | 하드코딩된 자격 증명 제거, 테스트용 사용자 자동 생성 |
| TC004 | 회원가입 스키마 수정, refresh_token을 body로 전송 |
| TC005 | 엔드포인트 `/2fa/setup` → `/auth/2fa/setup` |
| TC006 | 엔드포인트 `/2fa/verify` → `/auth/2fa/verify`, pyotp 사용 |
| TC007 | 엔드포인트 `/account/keys` → `/account/save_keys` |
| TC008 | 인증 플로우 개선, API 키 미설정 시 에러 처리 |
| TC009 | side 값 `buy` → `long`, 인증 플로우 추가 |
| TC010 | 인증 헤더 추가, 필드명 `time` → `timestamp` |

---

## 관련 문서

- [CHART_SIGNAL_MARKERS_GUIDE.md](./CHART_SIGNAL_MARKERS_GUIDE.md) - 차트 시그널 마커 가이드
- [PROJECT_HANDOVER.md](./PROJECT_HANDOVER.md) - 프로젝트 전체 인수인계
