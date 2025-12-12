# 🤖 다중 봇 시스템 구현 계획서 (1/3)

# 📋 프로젝트 개요 및 작업 체크리스트

---

## 📌 문서 정보

| 항목 | 내용 |
|------|------|
| 작성일 | 2025-12-10 |
| 수정일 | 2025-12-12 |
| 버전 | 1.2 |
| 프로젝트 | auto-dashboard |
| 관련 문서 | `02_DATABASE_DESIGN.md`, `03_IMPLEMENTATION_DETAIL.md` |
| **차트 구현** | `CHART_SIGNAL_MARKERS_GUIDE.md` - 시그널 마커, 거래 오버레이 구현 가이드 |
| **보안 감사** | `CODE_REVIEW_AND_SECURITY_AUDIT.md` - 코드 검토 및 보안 감사 보고서 |
| **개발 가이드 (SKILL)** | `skills/backend-trading-api/SKILL.md` - 백엔드 API 개발 |
|  | `skills/frontend-trading-dashboard/SKILL.md` - 프론트엔드 대시보드 개발 |

---

## 🎯 프로젝트 목표

### 현재 시스템 구조

```
┌─────────────────────────────────────────┐
│              사용자 A                    │
│  ┌─────────────────────────────────┐    │
│  │         1개 봇 실행              │    │
│  │    전략: 보수적 EMA              │    │
│  │    잔고: 전체 (100%)            │    │
│  └─────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

### 목표 시스템 구조

```
┌─────────────────────────────────────────────────────────────┐
│                        사용자 A                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │  AI 봇 #1    │  │  AI 봇 #2    │  │   그리드 봇 #1    │   │
│  │  보수적 전략  │  │  공격적 전략  │  │   BTC 레인지     │   │
│  │  잔고: 30%   │  │  잔고: 20%   │  │   잔고: 50%      │   │
│  │  BTC 전용    │  │  ETH 전용    │  │   $90k~$100k    │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

---

## 👥 다중 사용자 고려사항

### 동시 사용 시나리오

- **예상 동시 사용자**: 100~1000명
- **사용자당 평균 봇 수**: 3개
- **총 동시 봇 수**: 300~3000개

### 리소스 관리

| 항목 | 제한 | 이유 |
|------|------|------|
| 사용자당 최대 봇 수 | 10개 | 서버 리소스 |
| 총 잔고 할당 | 100% | 잔고 충돌 방지 |
| 봇당 최대 레버리지 | 20x | 리스크 관리 |
| 그리드 봇 최대 그리드 수 | 100개 | API Rate Limit |

---

## ✅ 작업 체크리스트

### Phase 1: 데이터베이스 설계 (담당자: Claude) ✅ 완료

| 순번 | 작업 | 상태 | 담당자 | 시작일 | 완료일 |
|------|------|------|--------|--------|--------|
| 1.1 | [✅] `bot_instances` 테이블 스키마 설계 | 완료 | Claude | 12/11 | 12/11 |
| 1.2 | [✅] `grid_bot_configs` 테이블 스키마 설계 | 완료 | Claude | 12/11 | 12/11 |
| 1.3 | [✅] `grid_orders` 테이블 스키마 설계 | 완료 | Claude | 12/11 | 12/11 |
| 1.4 | [✅] SQLAlchemy 모델 작성 | 완료 | Claude | 12/11 | 12/11 |
| 1.5 | [✅] Alembic 마이그레이션 파일 생성 | 완료 | Claude | 12/11 | 12/11 |
| 1.6 | [✅] 개발 DB에 마이그레이션 실행 | 완료 | Claude | 12/11 | 12/11 |
| 1.7 | [ ] 테스트 데이터 시딩 스크립트 작성 | 대기 | | | |

**구현 파일:**

- `backend/src/database/models.py` - BotInstance, GridBotConfig, GridOrder, TradeSource, BotType 추가
- `backend/alembic/versions/c1d2e3f4g5h6_add_multi_bot_system_tables.py` - 마이그레이션

### Phase 2: 백엔드 API (담당자: Claude) ✅ 완료

| 순번 | 작업 | 상태 | 담당자 | 시작일 | 완료일 |
|------|------|------|--------|--------|--------|
| 2.1 | [✅] `api/bot_instances.py` 파일 생성 | 완료 | Claude | 12/11 | 12/11 |
| 2.2 | [✅] 봇 CRUD API 구현 | 완료 | Claude | 12/11 | 12/11 |
| 2.3 | [✅] 봇 시작/중지 API 구현 | 완료 | Claude | 12/11 | 12/11 |
| 2.4 | [✅] 잔고 할당 검증 로직 | 완료 | Claude | 12/11 | 12/11 |
| 2.5 | [✅] `api/grid_bot.py` 파일 생성 | 완료 | Claude | 12/12 | 12/12 |
| 2.6 | [✅] 그리드 봇 설정 API 구현 | 완료 | Claude | 12/12 | 12/12 |
| 2.7 | [✅] API 스키마 (Pydantic) 작성 | 완료 | Claude | 12/11 | 12/11 |

**구현 파일:**

- `backend/src/api/bot_instances.py` - 전체 CRUD + 시작/중지/통계 API
- `backend/src/api/grid_bot.py` - **[NEW]** 그리드 봇 전용 API (config, orders, start/stop, stats, preview, market)
- `backend/src/schemas/bot_instance_schema.py` - Pydantic 스키마 (GridBotConfigCreate, GridBotConfigResponse 등)
- `backend/src/services/allocation_manager.py` - 잔고 할당 관리자
- `backend/src/main.py` - 라우터 등록

**Grid Bot API 엔드포인트:**

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/grid-bot/{bot_id}/config` | GET | 그리드 설정 조회 |
| `/grid-bot/{bot_id}/config` | POST | 그리드 설정 생성/수정 |
| `/grid-bot/{bot_id}/orders` | GET | 그리드 주문 목록 조회 |
| `/grid-bot/{bot_id}/start` | POST | 그리드 봇 시작 (주문 배치) |
| `/grid-bot/{bot_id}/stop` | POST | 그리드 봇 중지 (주문 취소) |
| `/grid-bot/{bot_id}/stats` | GET | 통계 조회 |
| `/grid-bot/preview` | POST | 그리드 미리보기 (주문 없이 계산만) |
| `/grid-bot/market/{symbol}` | GET | 시장 가격 조회 (24h high/low 포함) |

### Phase 3: 봇 런타임 (담당자: Claude) ✅ 완료

| 순번 | 작업 | 상태 | 담당자 | 시작일 | 완료일 |
|------|------|------|--------|--------|--------|
| 3.1 | [✅] `BotRunner` 리팩토링 (다중 봇 지원) | 완료 | Claude | 12/11 | 12/11 |
| 3.2 | [✅] `AllocationManager` 클래스 구현 | 완료 | Claude | 12/11 | 12/11 |
| 3.3 | [✅] `BotManager` 다중 봇 지원 수정 | 완료 | Claude | 12/11 | 12/11 |
| 3.4 | [✅] `GridBotRunner` 클래스 구현 | 완료 | Claude | 12/11 | 12/11 |
| 3.5 | [✅] `GridBotRunner` ↔ `BotRunner` 통합 | 완료 | Claude | 12/11 | 12/11 |
| 3.6 | [✅] 봇 인스턴스별 격리 로직 강화 | 완료 | Claude | 12/11 | 12/11 |
| 3.7 | [✅] 에러 핸들링 및 복구 로직 | 완료 | Claude | 12/11 | 12/11 |
| 3.8 | [✅] 텔레그램 알림 연동 (봇별) | 완료 | Claude | 12/11 | 12/11 |

**구현 파일:**

- `backend/src/services/bot_runner.py` - `_run_instance_loop`, `start_instance`, `stop_instance` 등 다중 봇 메서드 추가
- `backend/src/services/grid_bot_runner.py` - **[NEW]** 그리드 봇 실행 로직 (등차/등비 그리드, 주문 관리, 사이클 반복)
- `backend/src/services/bot_isolation_manager.py` - **[NEW]** 봇 격리 관리자 (포지션 충돌 방지)
- `backend/src/services/bot_recovery_manager.py` - **[NEW]** 봇 복구 관리자 (에러 처리 및 자동 복구)
- `backend/src/workers/manager.py` - `BotManager` 다중 봇 지원 (`bootstrap_bot_instances`, `start_bot_instance` 등)
- `backend/src/services/allocation_manager.py` - 잔고 할당 관리자

**GridBotRunner 주요 기능:**

- `calculate_grid_prices()`: 등차(ARITHMETIC) / 등비(GEOMETRIC) 그리드 가격 계산
- `_setup_initial_orders()`: 현재 가격 아래 매수 주문 설정
- `_check_and_update_orders()`: 체결 모니터링 및 매도 주문 설정
- `_restart_grid_cycle()`: 매도 체결 후 사이클 재시작
- BotType.GRID인 경우 BotRunner에서 자동 위임

**BotIsolationManager 주요 기능:**

- `can_open_position()`: 포지션 진입 전 충돌 체크
- `register_position()`: 봇별 포지션 등록 (메모리 캐시 + DB)
- `close_position()`: 포지션 청산 시 캐시 정리
- `sync_from_db()`: 서버 시작 시 DB에서 포지션 동기화
- 사용자-심볼별 락으로 동시 진입 방지

**BotRecoveryManager 주요 기능:**

- `classify_error()`: 예외를 에러 유형으로 분류 (API_KEY_INVALID, RATE_LIMIT, NETWORK_ERROR 등)
- `record_error()`: 에러 기록 및 재시도 여부 결정
- `get_retry_delay()`: 지수 백오프를 사용한 재시도 대기 시간 계산
- `schedule_recovery()`: 지연된 봇 복구 예약
- `check_and_recover_bots()`: 주기적 봇 상태 점검 및 자동 복구

**다음 작업 우선순위:**

1. ~~프론트엔드 - 봇 관리 UI~~ ✅ 완료 (2025-12-12)
2. 그리드 봇 설정 API (`api/grid_bot.py`)
3. 그리드 봇 프론트엔드 UI (그리드 설정 UI, 시각화 차트)
4. 테스트 및 배포

### Phase 4: 프론트엔드 (담당자: Claude) ✅ 완료

| 순번 | 작업 | 상태 | 담당자 | 시작일 | 완료일 |
|------|------|------|--------|--------|--------|
| 4.1 | [✅] 봇 목록 페이지 UI | 완료 | Claude | 12/12 | 12/12 |
| 4.2 | [✅] 봇 생성 모달 | 완료 | Claude | 12/12 | 12/12 |
| 4.3 | [✅] 잔고 할당 시각화 바 | 완료 | Claude | 12/12 | 12/12 |
| 4.4 | [✅] 그리드 봇 설정 UI | 완료 | Claude | 12/12 | 12/12 |
| 4.5 | [✅] 그리드 시각화 차트 | 완료 | Claude | 12/12 | 12/12 |
| 4.6 | [✅] 봇별 통계 대시보드 | 완료 | Claude | 12/12 | 12/12 |
| 4.7 | [✅] API 연동 (`src/api/botInstances.js`) | 완료 | Claude | 12/12 | 12/12 |

**구현 파일:**

- `frontend/src/api/botInstances.js` - 봇 인스턴스 API 클라이언트
- `frontend/src/api/gridBot.js` - **[NEW]** 그리드 봇 전용 API 클라이언트
- `frontend/src/pages/BotManagement.jsx` - 봇 관리 메인 페이지 (탭 기반: 전체/AI 추세/그리드)
- `frontend/src/components/bot/AllocationBar.jsx` - 잔고 할당 시각화 바
- `frontend/src/components/bot/BotCard.jsx` - 개별 봇 카드 컴포넌트
- `frontend/src/components/bot/AddBotCard.jsx` - 새 봇 추가 카드 + 생성 모달
- `frontend/src/components/bot/BotStatsModal.jsx` - 봇 상세 통계 모달
- `frontend/src/components/bot/EditBotModal.jsx` - 봇 설정 편집 모달
- `frontend/src/components/grid/GridVisualizer.jsx` - **[NEW]** 그리드 시각화 차트
- `frontend/src/components/grid/CreateGridBotModal.jsx` - **[NEW]** 3단계 그리드 봇 생성 위저드
- `frontend/src/components/grid/GridBotCard.jsx` - **[NEW]** 그리드 봇 전용 카드 (미니 시각화 포함)
- `frontend/src/App.jsx` - `/bots` 라우트 추가
- `frontend/src/components/layout/MainLayout.jsx` - 사이드바에 "봇 관리" 메뉴 추가

**API 클라이언트 기능 (botInstances.js):**

- `list()` - 봇 목록 조회
- `create(data)` - 새 봇 생성
- `get(botId)` - 봇 상세 조회
- `update(botId, data)` - 봇 설정 수정
- `delete(botId)` - 봇 삭제
- `start(botId)` / `stop(botId)` - 개별 봇 시작/중지
- `startAll()` / `stopAll()` - 전체 봇 시작/중지
- `getStats(botId)` - 봇별 통계 조회
- `getSummary()` - 전체 통계 요약

**BotManagement.jsx 주요 기능:**

- 통계 요약 카드 (총 봇, 실행 중, 총 PNL, 평균 승률)
- AllocationBar 잔고 할당 시각화 (봇별 색상 구분)
- BotCard 그리드 레이아웃 (카드별 상태, PNL, 승률, 액션 버튼)
- 전체 시작/중지 버튼
- 봇 생성/수정/삭제/통계 모달

**BotCard.jsx 주요 기능:**

- 봇 상태 표시 (실행 중: 녹색 글로우, 중지됨: 회색)
- PNL, 승률, 총 거래 수, 레버리지 표시
- 시작/중지, 편집, 통계 보기, 삭제 액션 버튼
- 비트겟 스타일 다크 테마 UI

**AddBotCard.jsx 주요 기능:**

- 봇 타입 선택 (AI 추세, 그리드)
- 봇 이름, 설명, 심볼 설정
- 전략 선택 (AI 봇 전용)
- 잔고 할당 슬라이더 (0~100%)
- 레버리지, 최대 포지션, 손절/익절 설정
- 텔레그램 알림 토글

**GridVisualizer.jsx 주요 기능:**

- 세로 가격 축 (상단=고가, 하단=저가)
- 그리드 라인별 상태 표시 (pending, buy_placed, buy_filled, sell_placed, sell_filled)
- 현재가 마커 애니메이션 (황금색 라인)
- 체결된 주문에 펄스 효과
- Compact 모드 (카드용 미니 시각화)
- 등차(Arithmetic) / 등비(Geometric) 모드 지원

**CreateGridBotModal.jsx 주요 기능:**

- 3단계 위저드: 기본 설정 → 그리드 설정 → 확인
- 24h 고가/저가 기반 가격 범위 추천
- 실시간 그리드 미리보기 (GridVisualizer 연동)
- 예상 그리드당 수익률 계산
- 총 투자금, 그리드 개수 설정

**GridBotCard.jsx 주요 기능:**

- 민트/청록색 그라디언트 테마 (AI 봇과 시각적 구분)
- 미니 그리드 시각화 내장
- 실현 수익 애니메이션 카운터
- 매수/매도 체결 현황
- 그리드 활성도 진행률 표시

**다음 작업 우선순위:**

1. ✅ 그리드 봇 설정 UI 완료
2. ✅ 그리드 시각화 차트 완료
3. 테스트 및 배포 (Phase 5)

### Phase 5: 테스트 및 배포 (담당자: _______)

| 순번 | 작업 | 상태 | 담당자 | 시작일 | 완료일 |
|------|------|------|--------|--------|--------|
| 5.1 | [ ] 단위 테스트 작성 | 대기 | | | |
| 5.2 | [ ] 통합 테스트 작성 | 대기 | | | |
| 5.3 | [ ] 부하 테스트 (다중 사용자) | 대기 | | | |
| 5.4 | [ ] 스테이징 환경 배포 | 대기 | | | |
| 5.5 | [ ] QA 테스트 | 대기 | | | |
| 5.6 | [ ] 프로덕션 배포 | 대기 | | | |

---

## 📁 파일 구조 변경 계획

```
backend/src/
├── api/
│   ├── bot_instances.py      # [NEW] ✅ 다중 봇 API
│   └── grid_bot.py           # [NEW] 그리드 봇 API (대기)
├── services/
│   ├── bot_runner.py         # [MODIFY] ✅ 다중 봇 지원
│   ├── grid_bot_runner.py    # [NEW] ✅ 그리드 봇 로직
│   ├── allocation_manager.py # [NEW] ✅ 잔고 할당 관리
│   ├── bot_isolation_manager.py  # [NEW] ✅ 봇 격리 관리자
│   └── bot_recovery_manager.py   # [NEW] ✅ 봇 복구 관리자
├── schemas/
│   └── bot_instance_schema.py    # [NEW] ✅ (GridBotConfig 스키마 포함)
├── workers/
│   └── manager.py            # [MODIFY] ✅ 다중 봇 지원
└── database/
    └── models.py             # [MODIFY] ✅ 새 테이블 추가

frontend/src/
├── pages/
│   └── BotManagement.jsx     # [NEW] ✅ 봇 관리 페이지 (탭 기반 UI)
├── components/
│   ├── TradingChart.jsx      # [FIX] ✅ export default 추가
│   ├── bot/                  # [NEW] ✅ 봇 컴포넌트 폴더
│   │   ├── AllocationBar.jsx # [NEW] ✅ 잔고 할당 시각화
│   │   ├── BotCard.jsx       # [NEW] ✅ 봇 카드 컴포넌트
│   │   ├── AddBotCard.jsx    # [NEW] ✅ 봇 추가 + 생성 모달
│   │   ├── BotStatsModal.jsx # [NEW] ✅ 봇 통계 모달
│   │   └── EditBotModal.jsx  # [NEW] ✅ 봇 편집 모달
│   └── grid/                 # [NEW] ✅ 그리드 봇 전용 컴포넌트
│       ├── GridVisualizer.jsx    # [NEW] ✅ 그리드 시각화 차트
│       ├── CreateGridBotModal.jsx # [NEW] ✅ 3단계 생성 위저드
│       └── GridBotCard.jsx       # [NEW] ✅ 그리드 봇 카드
├── api/
│   ├── botInstances.js       # [NEW] ✅ 봇 API 클라이언트
│   └── gridBot.js            # [NEW] ✅ 그리드 봇 API 클라이언트
├── App.jsx                   # [MODIFY] ✅ /bots 라우트 추가
└── components/layout/
    └── MainLayout.jsx        # [MODIFY] ✅ "봇 관리" 메뉴 추가
```

---

## 🔄 작업 의존성 다이어그램

```
[1.1~1.7 DB 설계] ────┐
                      ├──▶ [2.1~2.7 API 구현]
[3.1~3.6 런타임] ◀────┘          │
       ▲                        │
       │                        ▼
       └────────────────[4.1~4.7 프론트엔드]
                               │
                               ▼
                        [5.1~5.6 테스트/배포]
```

---

## 📅 일정 요약

| 주차 | 주요 작업 | 병렬 가능 작업 |
|------|----------|---------------|
| 1주차 | DB 설계 (1.1~1.7) | - |
| 2주차 | API 구현 (2.1~2.7) | 런타임 설계 시작 |
| 3주차 | 런타임 구현 (3.1~3.6) | 프론트 UI 작업 |
| 4주차 | 프론트엔드 (4.1~4.7) | 테스트 작성 |
| 5주차 | 테스트/배포 (5.1~5.6) | 문서화 |

---

**다음 문서**: `02_DATABASE_DESIGN.md` (테이블 상세 설계)
