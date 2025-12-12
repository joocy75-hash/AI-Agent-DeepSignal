# Grid Bot 재설계 작업 계획서

## 📌 문서 정보
- **작성일**: 2025-12-12
- **버전**: v1.0
- **작성자**: AI Assistant
- **목적**: Bitget Futures Grid Bot UI/UX를 100% 참고하여 플랫폼 관리자가 생성한 봇을 일반 사용자가 바로 사용할 수 있는 시스템으로 재설계

---

## 1. 현재 구현 분석 및 문제점

### 1.1 현재 구현 방식
```
현재: 사용자가 직접 모든 파라미터 설정
┌─────────────────────────────────────────────────┐
│  사용자 → 봇 이름 입력                            │
│        → 코인 선택 (BTCUSDT, ETHUSDT 등)        │
│        → 가격 범위 설정 (lower_price, upper_price)│
│        → 그리드 개수 설정 (2-100)               │
│        → 투자 금액 입력                          │
│        → 레버리지 설정                           │
│        → 봇 시작                                │
└─────────────────────────────────────────────────┘
```

### 1.2 문제점
| 문제 | 설명 |
|------|------|
| 전문 지식 필요 | 사용자가 가격 범위, 그리드 개수 등을 직접 설정해야 함 |
| 백테스트 없음 | 어떤 설정이 수익성 있는지 사전 검증 불가 |
| 진입 장벽 높음 | 초보자가 쉽게 사용하기 어려움 |
| 신뢰도 지표 부재 | ROI, 사용자 수 등 검증된 데이터 없음 |

---

## 2. Bitget 참고 UI/UX 분석

### 2.1 Bitget Futures Grid Bot 핵심 특징

#### 이미지 1 - 봇 목록 화면
```
┌─────────────────────────────────────────────────┐
│  Futures grid ▼                                  │
├─────────────────────────────────────────────────┤
│  SOLUSDT ▼   138.498  +5.78%                    │
│                                                  │
│  ┌─────────┐  ┌─────────┐                       │
│  │   AI    │  │ Manual  │  ← AI 탭 (관리자 템플릿) │
│  └─────────┘  └─────────┘    Manual 탭 (직접 생성) │
├─────────────────────────────────────────────────┤
│  SOLUSDT                              ┌─────┐   │
│  [Futures grid] [Short] [5X]          │ Use │   │
│                                       └─────┘   │
│  30D backtested ROI          📈 (차트)          │
│  1,662.45% (녹색)                               │
│                                                  │
│  Recommended investment period: 7-30 days       │
│  Min. investment: 384.20853923 USDT    👥 193   │
├─────────────────────────────────────────────────┤
│  [동일 형태의 다른 봇 카드들...]                   │
└─────────────────────────────────────────────────┘
```

#### 이미지 2 - 봇 상세 및 투자 확인 화면
```
┌─────────────────────────────────────────────────┐
│  ← SOLUSDT                                       │
│                                                  │
│  [Futures grid] [Short] [5x]                    │
│                                                  │
│  30D backtested ROI    Funds in use(USDT)       │
│  +1,616.46%            17469.26                 │
│                                                  │
│  Users                 30D max drawdown          │
│  160                   95.57%                    │
├─────────────────────────────────────────────────┤
│  Bot details                                     │
│  Grid bots execute trades automatically based   │
│  on preset price levels, profiting from buying  │
│  low and selling high during market fluctuations│
├─────────────────────────────────────────────────┤
│  ● Buy  ● Sell         Upper Price    + Sell    │
│  ═══════════════════════════════════════════    │
│  [그리드 시각화]                                 │
├─────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────┐    │
│  │  Confirm investment amount              │    │
│  │                                         │    │
│  │  Margin                                 │    │
│  │  ≥ 578.68070549      USDT    [5x ▼]    │    │
│  │  ○────────────────────○                │    │
│  │                                         │    │
│  │  Available          46.91898606 USDT ⇄ │    │
│  │  Estimated liquidation price    --     │    │
│  │                                         │    │
│  │  Parameters                        ▼   │    │
│  │  Copy to manual creation           >   │    │
│  │                                         │    │
│  │  ┌─────────────────────────────────┐   │    │
│  │  │          Confirm                │   │    │
│  │  └─────────────────────────────────┘   │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### 2.2 핵심 UI 요소 정리

| 요소 | 설명 | 데이터 타입 |
|------|------|-------------|
| 코인 심볼 | SOLUSDT, BTCUSDT 등 | string |
| 봇 타입 | Futures grid | enum |
| 포지션 방향 | Long / Short | enum |
| 레버리지 | 5X, 10X 등 | int |
| 30D ROI | 백테스트 수익률 | decimal % |
| 추천 투자기간 | 7-30 days | string |
| 최소 투자금액 | Min. investment | decimal USDT |
| 사용자 수 | 현재 사용 중인 인원 | int |
| 운용 자금 | Funds in use | decimal USDT |
| 최대 낙폭 | 30D max drawdown | decimal % |
| ROI 차트 | 30일 수익률 미니 차트 | array[decimal] |

---

## 3. 재설계 목표

### 3.1 새로운 구현 방식
```
목표: 관리자가 만든 템플릿을 사용자가 원클릭 사용
┌─────────────────────────────────────────────────┐
│  [관리자]                                        │
│  → 그리드 전략 템플릿 생성                        │
│  → 백테스트 실행 및 결과 저장                     │
│  → 추천 설정값 입력 (가격 범위, 그리드 수 등)      │
│  → 템플릿 공개 설정                              │
├─────────────────────────────────────────────────┤
│  [일반 사용자]                                   │
│  → AI 탭에서 템플릿 목록 확인                     │
│  → ROI, 사용자 수 등 신뢰 지표 확인               │
│  → "Use" 버튼 클릭                              │
│  → 투자 금액 & 레버리지만 설정                    │
│  → 바로 봇 시작!                                │
└─────────────────────────────────────────────────┘
```

### 3.2 핵심 변경 사항
1. **관리자 전용 템플릿 시스템** 추가
2. **백테스트 결과 저장** 및 표시
3. **AI 탭 / Manual 탭** 분리
4. **사용자 통계** (사용자 수, 총 운용 자금) 추가
5. **원클릭 복사** 시스템 구현

---

## 4. 데이터베이스 스키마 설계

### 4.1 새로운 테이블: `GridBotTemplate` (관리자 템플릿)

```python
class GridBotTemplate(Base):
    """관리자가 생성한 그리드봇 템플릿"""
    __tablename__ = "grid_bot_templates"

    id = Column(Integer, primary_key=True)

    # 기본 정보
    symbol = Column(String(20), nullable=False)          # "SOLUSDT"
    direction = Column(Enum(PositionDirection), nullable=False)  # LONG, SHORT
    leverage = Column(Integer, default=5)                # 5, 10, 20 등

    # 그리드 설정 (관리자가 미리 계산)
    lower_price = Column(Numeric(20, 8), nullable=False)
    upper_price = Column(Numeric(20, 8), nullable=False)
    grid_count = Column(Integer, nullable=False)         # 그리드 개수
    grid_mode = Column(Enum(GridMode), default='ARITHMETIC')

    # 투자 제한
    min_investment = Column(Numeric(20, 8), nullable=False)  # 최소 투자금액
    recommended_investment = Column(Numeric(20, 8))          # 권장 투자금액

    # 백테스트 결과
    backtest_roi_30d = Column(Numeric(10, 4))           # 30일 ROI %
    backtest_max_drawdown = Column(Numeric(10, 4))      # 최대 낙폭 %
    backtest_roi_history = Column(JSON)                  # 일별 ROI 배열 (차트용)
    backtest_updated_at = Column(DateTime)               # 백테스트 날짜

    # 추천 정보
    recommended_period = Column(String(50))              # "7-30 days"
    description = Column(Text)                           # 봇 설명

    # 사용 통계
    active_users = Column(Integer, default=0)            # 현재 사용 중인 유저 수
    total_funds_in_use = Column(Numeric(20, 8), default=0)  # 총 운용 자금

    # 상태
    is_active = Column(Boolean, default=True)            # 공개 여부
    is_featured = Column(Boolean, default=False)         # 추천 표시

    # 관리
    created_by = Column(Integer, ForeignKey("users.id")) # 관리자 ID
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # 관계
    instances = relationship("BotInstance", back_populates="template")
```

### 4.2 `BotInstance` 테이블 수정

```python
class BotInstance(Base):
    # 기존 필드들...

    # 추가: 템플릿 참조
    template_id = Column(Integer, ForeignKey("grid_bot_templates.id"), nullable=True)

    # 관계
    template = relationship("GridBotTemplate", back_populates="instances")
```

### 4.3 새로운 Enum

```python
class PositionDirection(str, Enum):
    LONG = "long"
    SHORT = "short"
```

---

## 5. API 엔드포인트 설계

### 5.1 관리자 API (Admin Only)

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/admin/grid-templates` | 템플릿 생성 |
| PUT | `/admin/grid-templates/{id}` | 템플릿 수정 |
| DELETE | `/admin/grid-templates/{id}` | 템플릿 삭제 |
| POST | `/admin/grid-templates/{id}/backtest` | 백테스트 실행 |
| PATCH | `/admin/grid-templates/{id}/toggle` | 공개/비공개 전환 |

### 5.2 사용자 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/grid-templates` | 공개 템플릿 목록 조회 |
| GET | `/grid-templates/{id}` | 템플릿 상세 조회 |
| POST | `/grid-templates/{id}/use` | 템플릿으로 봇 생성 |

### 5.3 API 응답 예시

#### GET `/grid-templates` 응답
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "symbol": "SOLUSDT",
      "direction": "short",
      "leverage": 5,
      "backtest_roi_30d": 1662.45,
      "backtest_max_drawdown": 95.57,
      "recommended_period": "7-30 days",
      "min_investment": 384.21,
      "active_users": 193,
      "total_funds_in_use": 17469.26,
      "roi_chart": [100, 105, 112, ...],  // 30일치 데이터
      "is_featured": true
    }
  ]
}
```

#### POST `/grid-templates/{id}/use` 요청
```json
{
  "investment_amount": 500.00,
  "leverage": 5
}
```

---

## 6. 프론트엔드 컴포넌트 설계

### 6.1 컴포넌트 구조

```
frontend/src/components/grid/
├── index.js                    # 기존 (수정)
├── GridVisualizer.jsx          # 기존 유지
├── GridBotCard.jsx             # 기존 (내 봇 카드로 수정)
├── CreateGridBotModal.jsx      # 기존 (Manual 탭용으로 유지)
│
├── templates/                  # 새로 추가
│   ├── index.js
│   ├── TemplateList.jsx       # 템플릿 목록 (AI 탭)
│   ├── TemplateCard.jsx       # 템플릿 카드 (Bitget 스타일)
│   ├── TemplateDetail.jsx     # 템플릿 상세 페이지
│   ├── UseTemplateModal.jsx   # "Use" 클릭 시 투자금액 입력 모달
│   └── MiniRoiChart.jsx       # 30일 ROI 미니 차트
│
├── admin/                      # 관리자 전용
│   ├── index.js
│   ├── TemplateManager.jsx    # 템플릿 관리 페이지
│   ├── CreateTemplateModal.jsx # 템플릿 생성 모달
│   ├── BacktestRunner.jsx     # 백테스트 실행 UI
│   └── TemplateStats.jsx      # 템플릿 통계 대시보드
```

### 6.2 핵심 UI 컴포넌트 상세

#### TemplateCard.jsx (Bitget 스타일)
```jsx
// 목표 레이아웃
┌─────────────────────────────────────────────────┐
│  SOLUSDT                              ┌─────┐   │
│  [Futures grid] [Short] [5X]          │ Use │   │
│                                       └─────┘   │
│  30D backtested ROI          📈 (미니차트)      │
│  1,662.45% (녹색)                               │
│                                                  │
│  Recommended investment period: 7-30 days       │
│  Min. investment: 384.21 USDT          👥 193   │
└─────────────────────────────────────────────────┘
```

#### UseTemplateModal.jsx (투자 확인)
```jsx
// 목표 레이아웃
┌─────────────────────────────────────────────────┐
│  Confirm investment amount                       │
│                                                  │
│  Margin                                         │
│  ┌────────────────────┐  USDT   ┌────────┐     │
│  │ ≥ 578.68           │         │ 5x ▼   │     │
│  └────────────────────┘         └────────┘     │
│                                                  │
│  ○──────────────────────────────○  (슬라이더)   │
│                                                  │
│  Available: 1,000.00 USDT                       │
│  Estimated liquidation price: --                │
│                                                  │
│  ▼ Parameters (접기/펼치기)                      │
│    - Lower Price: 120.00                        │
│    - Upper Price: 150.00                        │
│    - Grid Count: 30                             │
│                                                  │
│  Copy to manual creation  >                     │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │               Confirm                    │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

---

## 7. 백테스트 시스템 설계

### 7.1 백테스트 로직

```python
class GridBacktester:
    """그리드봇 백테스트 엔진"""

    async def run_backtest(
        self,
        symbol: str,
        direction: PositionDirection,
        lower_price: Decimal,
        upper_price: Decimal,
        grid_count: int,
        leverage: int,
        investment: Decimal,
        days: int = 30
    ) -> BacktestResult:
        """
        1. 과거 30일 캔들 데이터 조회 (1분봉 or 5분봉)
        2. 각 캔들마다 가격이 그리드를 통과하는지 확인
        3. 그리드 통과 시 매수/매도 시뮬레이션
        4. 수수료 차감 (0.02% maker, 0.06% taker)
        5. 일별 수익률 계산
        6. 최대 낙폭(MDD) 계산
        7. 결과 반환
        """
        pass
```

### 7.2 BacktestResult 스키마

```python
class BacktestResult(BaseModel):
    total_roi: Decimal          # 총 수익률 %
    max_drawdown: Decimal       # 최대 낙폭 %
    total_trades: int           # 총 거래 수
    win_rate: Decimal           # 승률 %
    avg_profit_per_trade: Decimal
    daily_roi: List[Decimal]    # 일별 수익률 (차트용)

    # 상세 정보
    total_buy_orders: int
    total_sell_orders: int
    avg_holding_time: str       # "2.5 hours"
```

---

## 8. 구현 우선순위 및 작업 분배

### Phase 1: 데이터베이스 및 백엔드 기반 (담당자 A)
**예상 작업량: 중간**

1. GridBotTemplate 모델 생성
2. Alembic 마이그레이션 작성
3. BotInstance에 template_id 추가
4. 관리자 API 엔드포인트 구현
5. 사용자 API 엔드포인트 구현

### Phase 2: 백테스트 시스템 (담당자 B)
**예상 작업량: 높음**

1. 과거 캔들 데이터 수집 로직
2. 그리드 시뮬레이션 엔진
3. 수익률/낙폭 계산 알고리즘
4. 일별 ROI 배열 생성
5. 백테스트 API 연동

### Phase 3: 프론트엔드 UI (담당자 C)
**예상 작업량: 높음**

1. TemplateCard 컴포넌트
2. TemplateList 페이지
3. UseTemplateModal
4. MiniRoiChart
5. 탭 UI (AI / Manual)
6. 반응형 디자인

### Phase 4: 관리자 페이지 (담당자 D)
**예상 작업량: 중간**

1. TemplateManager 페이지
2. CreateTemplateModal
3. BacktestRunner UI
4. 통계 대시보드

### Phase 5: 통합 및 테스트 (전체)
**예상 작업량: 낮음**

1. 전체 플로우 테스트
2. 버그 수정
3. 성능 최적화
4. 배포

---

## 9. 상세 작업 지시서

> 아래 작업 지시서는 별도 파일로 분리됩니다.

- [작업 지시서 A: 백엔드 기반](./GRID_BOT_TASK_A_BACKEND.md)
- [작업 지시서 B: 백테스트 시스템](./GRID_BOT_TASK_B_BACKTEST.md)
- [작업 지시서 C: 프론트엔드 UI](./GRID_BOT_TASK_C_FRONTEND.md)
- [작업 지시서 D: 관리자 페이지](./GRID_BOT_TASK_D_ADMIN.md)

---

## 10. 기술 스택 요약

| 영역 | 기술 |
|------|------|
| Backend | FastAPI, SQLAlchemy, Alembic |
| Database | SQLite (개발) / PostgreSQL (배포) |
| Frontend | React 18, Ant Design, Recharts |
| 실시간 | WebSocket |
| 외부 API | Bitget REST API v2 |

---

## 11. 마일스톤

| 마일스톤 | 완료 조건 |
|----------|-----------|
| M1 | DB 스키마 완성, 마이그레이션 성공 |
| M2 | 관리자가 템플릿 CRUD 가능 |
| M3 | 백테스트 실행 및 결과 저장 |
| M4 | 사용자가 템플릿 목록 조회 가능 |
| M5 | "Use" 버튼으로 봇 생성 가능 |
| M6 | 전체 플로우 통합 테스트 완료 |

---

## 부록: 참고 이미지 설명

### 이미지 1: 봇 목록 화면
- 상단: 코인 선택 드롭다운 (SOLUSDT, 138.498, +5.78%)
- AI / Manual 탭 전환
- 카드 형태의 봇 목록
- 각 카드: 심볼, 타입/방향/레버리지 태그, ROI, 미니 차트, 추천 기간, 최소 투자금, 사용자 수

### 이미지 2: 상세 및 투자 확인
- 상세 정보: ROI, 운용 자금, 사용자 수, 최대 낙폭
- Bot details 설명 텍스트
- 그리드 시각화 (Buy/Sell 표시)
- 하단 시트: 투자금액 입력, 레버리지 선택, 가용 잔액, 파라미터 확장, Confirm 버튼
