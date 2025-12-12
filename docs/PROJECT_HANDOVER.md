# 🚀 프로젝트 인수인계 문서

## 📌 문서 정보

| 항목 | 내용 |
|------|------|
| 작성일 | 2025-12-12 |
| 프로젝트 | auto-dashboard (AI 자동매매 플랫폼) |
| 상태 | **개발 완료 - 테스트/배포 대기** |

---

## 📋 목차

1. [프로젝트 개요](#1-프로젝트-개요)
2. [현재 상태 요약](#2-현재-상태-요약)
3. [핵심 기능](#3-핵심-기능)
4. [프로젝트 구조](#4-프로젝트-구조)
5. [개발 환경 설정](#5-개발-환경-설정)
6. [남은 작업 (TODO)](#6-남은-작업-todo)
7. [주요 문서 안내](#7-주요-문서-안내)
8. [주의사항](#8-주의사항)

---

## 1. 프로젝트 개요

### 1.1 시스템 구성

```
┌─────────────────────────────────────────────────────────────┐
│                    AI 자동매매 플랫폼                         │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React + Vite)                                    │
│  └─ 대시보드, 거래 UI, 봇 관리, 백테스트, 설정               │
├─────────────────────────────────────────────────────────────┤
│  Backend (FastAPI + SQLite)                                 │
│  └─ REST API, WebSocket, 봇 런타임, 거래소 연동             │
├─────────────────────────────────────────────────────────────┤
│  External Services                                          │
│  └─ Bitget API (선물 거래), Telegram Bot (알림)             │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 기술 스택

| 구분 | 기술 |
|------|------|
| **Frontend** | React 18, Vite, Ant Design, Lightweight Charts, Recharts |
| **Backend** | FastAPI, SQLAlchemy (async), Alembic, Pydantic |
| **Database** | SQLite (aiosqlite) |
| **인증** | JWT + 2FA (TOTP) |
| **거래소** | Bitget Futures API (ccxt) |
| **실시간** | WebSocket (양방향 통신) |

---

## 2. 현재 상태 요약

### ✅ 완료된 기능

| 카테고리 | 기능 | 상태 |
|----------|------|------|
| **인증** | 로그인/회원가입, JWT, 2FA | ✅ 완료 |
| **대시보드** | 포트폴리오, 실시간 차트, 포지션 | ✅ 완료 |
| **봇 시스템** | 단일 봇 실행/중지 | ✅ 완료 |
| **다중 봇** | 사용자당 최대 10개 봇 동시 실행 | ✅ 완료 |
| **그리드 봇** | 그리드 트레이딩, 시각화, WebSocket 연동 | ✅ 완료 |
| **백테스트** | 전략 테스트, 결과 시각화 | ✅ 완료 |
| **관리자** | 사용자 관리, 시스템 로그 | ✅ 완료 |
| **보안** | Rate Limit, API 키 암호화, 권한 체크 | ✅ 완료 |

### ❌ 남은 작업 (Phase 5)

| 작업 | 우선순위 | 상태 |
|------|----------|------|
| 단위 테스트 작성 | High | 대기 |
| 통합 테스트 작성 | High | 대기 |
| 부하 테스트 | Medium | 대기 |
| 프로덕션 배포 | High | 대기 |
| console.log 정리 | Low | 대기 |

---

## 3. 핵심 기능

### 3.1 다중 봇 시스템

```
사용자 A
├── AI 봇 #1 (보수적 전략, 잔고 30%)
├── AI 봇 #2 (공격적 전략, 잔고 20%)
└── 그리드 봇 #1 (BTC $90k~$100k, 잔고 50%)
```

**핵심 파일:**
- `backend/src/api/bot_instances.py` - 봇 CRUD API
- `backend/src/api/grid_bot.py` - 그리드 봇 전용 API
- `backend/src/services/bot_runner.py` - 봇 실행 로직
- `backend/src/services/grid_bot_runner.py` - 그리드 봇 전용 로직
- `backend/src/services/allocation_manager.py` - 잔고 할당 관리

### 3.2 그리드 봇

- **등차(Arithmetic)** / **등비(Geometric)** 모드 지원
- 가격 범위 설정 (lower_price ~ upper_price)
- 최대 100개 그리드 지원
- 체결 시 자동 반대 주문 설정
- WebSocket 실시간 알림

**핵심 파일:**
- `frontend/src/components/grid/GridVisualizer.jsx` - 그리드 시각화
- `frontend/src/components/grid/GridBotCard.jsx` - 그리드 봇 카드 (WebSocket 구독)
- `frontend/src/components/grid/CreateGridBotModal.jsx` - 3단계 생성 위저드

### 3.3 WebSocket 채널

| 채널 | 이벤트 | 용도 |
|------|--------|------|
| `bot_log` | `bot_log` | 봇 실행 로그 |
| `position` | `position_update` | 포지션 변경 |
| `balance` | `balance_update` | 잔고 변경 |
| `grid_order` | `grid_order_update` | 그리드 주문 체결 |
| `grid_order` | `grid_cycle_complete` | 그리드 사이클 완료 |
| `price` | `price_update` | 실시간 가격 |

---

## 4. 프로젝트 구조

```
auto-dashboard/
├── backend/
│   ├── src/
│   │   ├── api/                  # REST API 엔드포인트
│   │   │   ├── bot_instances.py  # 다중 봇 API
│   │   │   ├── grid_bot.py       # 그리드 봇 API
│   │   │   ├── auth.py           # 인증 API
│   │   │   └── ...
│   │   ├── services/             # 비즈니스 로직
│   │   │   ├── bot_runner.py     # 봇 런타임
│   │   │   ├── grid_bot_runner.py
│   │   │   ├── allocation_manager.py
│   │   │   └── ...
│   │   ├── database/             # DB 모델
│   │   ├── websockets/           # WebSocket 서버
│   │   └── main.py               # FastAPI 앱
│   ├── alembic/                  # DB 마이그레이션
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── pages/                # 페이지 컴포넌트
│   │   │   ├── Dashboard.jsx
│   │   │   ├── BotManagement.jsx
│   │   │   └── ...
│   │   ├── components/           # 재사용 컴포넌트
│   │   │   ├── bot/              # 봇 관련
│   │   │   ├── grid/             # 그리드 봇 전용
│   │   │   └── ...
│   │   ├── api/                  # API 클라이언트
│   │   ├── context/              # React Context
│   │   └── App.jsx
│   └── package.json
│
├── docs/                         # 문서
│   ├── PROJECT_HANDOVER.md       # 이 문서
│   ├── MULTI_BOT_01_OVERVIEW.md  # 다중 봇 개요
│   ├── MULTI_BOT_02_DATABASE.md  # DB 설계
│   ├── MULTI_BOT_03_IMPLEMENTATION.md  # 구현 상세
│   ├── SECURITY_AUDIT_REPORT.md  # 보안 감사
│   └── ...
│
└── skills/                       # 개발 가이드 (SKILL)
    ├── backend-trading-api/
    └── frontend-trading-dashboard/
```

---

## 5. 개발 환경 설정

### 5.1 백엔드

```bash
cd backend

# 가상환경 생성 (권장)
python3 -m venv venv
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
export DATABASE_URL="sqlite+aiosqlite:///./trading.db"
export ENCRYPTION_KEY="your-encryption-key"  # Fernet.generate_key()
export JWT_SECRET="your-jwt-secret"

# DB 마이그레이션
alembic upgrade head

# 서버 실행
uvicorn src.main:app --reload --port 8000
```

### 5.2 프론트엔드

```bash
cd frontend

# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build
```

### 5.3 환경 변수

**백엔드 (.env)**
```env
DATABASE_URL=sqlite+aiosqlite:///./trading.db
ENCRYPTION_KEY=your-fernet-key
JWT_SECRET=your-jwt-secret
TELEGRAM_BOT_TOKEN=your-telegram-token  # 선택
```

**프론트엔드 (.env)**
```env
VITE_API_URL=http://localhost:8000
```

---

## 6. 남은 작업 (TODO)

### 🔴 High Priority

| 작업 | 설명 | 예상 시간 |
|------|------|----------|
| **단위 테스트** | `AllocationManager`, `GridBotRunner` 테스트 | 2일 |
| **통합 테스트** | 다중 봇 동시 실행 시나리오 | 2일 |
| **API 키 교체** | 프로덕션 JWT_SECRET, ENCRYPTION_KEY 재생성 | 1시간 |
| **CORS 환경변수화** | `main.py`의 하드코딩된 IP 제거 | 1시간 |

### 🟠 Medium Priority

| 작업 | 설명 | 예상 시간 |
|------|------|----------|
| **부하 테스트** | 100+ 동시 사용자, 300+ 봇 시나리오 | 1일 |
| **JWT 만료 단축** | 24시간 → 15분 + Refresh Token | 1일 |
| **로그인 실패 잠금** | 5회 실패 시 15분 잠금 | 0.5일 |

### 🟢 Low Priority

| 작업 | 설명 | 예상 시간 |
|------|------|----------|
| **console.log 정리** | 프로덕션 빌드 전 제거 (약 62개) | 0.5일 |
| **테스트 데이터 시딩** | 개발용 더미 데이터 스크립트 | 0.5일 |

---

## 7. 주요 문서 안내

### 현재 유효한 문서 (docs/)

| 문서 | 용도 |
|------|------|
| `PROJECT_HANDOVER.md` | **이 문서** - 프로젝트 인수인계 |
| `MULTI_BOT_01_OVERVIEW.md` | 다중 봇 시스템 개요 및 체크리스트 |
| `MULTI_BOT_02_DATABASE.md` | DB 테이블 설계 |
| `MULTI_BOT_03_IMPLEMENTATION.md` | API 및 서비스 구현 상세 |
| `SECURITY_AUDIT_REPORT.md` | 보안 감사 결과 |
| `CODE_REVIEW_AND_SECURITY_AUDIT.md` | 코드 리뷰 및 보안 개선 사항 |
| `CHART_SIGNAL_MARKERS_GUIDE.md` | 차트 시그널 마커 구현 가이드 |
| `GRID_BOT_REMAINING_TASKS.md` | 그리드 봇 작업 완료 현황 |
| `BACKEND_ARCHITECTURE.md` | 백엔드 아키텍처 |
| `FRONTEND_ARCHITECTURE.md` | 프론트엔드 아키텍처 |

### 개발 가이드 (skills/)

| 문서 | 용도 |
|------|------|
| `skills/backend-trading-api/SKILL.md` | 백엔드 API 개발 가이드 |
| `skills/frontend-trading-dashboard/SKILL.md` | 프론트엔드 개발 가이드 |

### 아카이브된 문서 (docs/archived/, docs/archive/)

과거 작업 기록 및 완료된 핸드오버 문서. 참고용으로만 사용.

---

## 8. 주의사항

### 8.1 보안

1. **API 키 관리**: 프로덕션 배포 전 반드시 새 키 생성
   ```bash
   # JWT_SECRET
   openssl rand -base64 32

   # ENCRYPTION_KEY
   python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

2. **동적 코드 실행 비활성화**: 사용자 커스텀 전략 코드 실행이 보안상 비활성화됨
   - 파일: `backend/src/services/strategy_loader.py`

3. **테스트 계정**: 프로덕션에서 테스트 계정 정보 미표시
   - 파일: `frontend/src/pages/Login.jsx` (DEV 환경에서만 표시)

### 8.2 거래소 연동

1. **Rate Limit**: Bitget API 분당 요청 제한 주의
2. **테스트넷 사용**: 실거래 전 테스트넷에서 충분히 테스트
3. **에러 복구**: `BotRecoveryManager`가 자동 복구 처리

### 8.3 다중 봇

1. **잔고 할당**: 총 할당이 100%를 초과할 수 없음
2. **봇 격리**: `BotIsolationManager`가 포지션 충돌 방지
3. **서버 재시작**: `BotManager.bootstrap()`에서 실행 중이던 봇 자동 복구

---

## 📞 연락처

질문이나 이슈가 있으면:
1. 이 문서의 관련 섹션 확인
2. `skills/` 폴더의 개발 가이드 참조
3. `docs/` 폴더의 상세 문서 참조

---

**마지막 업데이트**: 2025-12-12
