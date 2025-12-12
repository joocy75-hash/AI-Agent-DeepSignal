# ⚙️ 다중 봇 시스템 구현 계획서 (3/3)

# 🔧 서비스 로직 및 API 상세 구현

---

## 📌 관련 문서

- 이전: `02_DATABASE_DESIGN.md`
- 개요: `01_OVERVIEW.md`

---

## 🖥️ 백엔드 API 설계

### 1. 봇 인스턴스 API (`api/bot_instances.py`)

```python
router = APIRouter(prefix="/bot-instances", tags=["Bot Instances"])

# ===================== CRUD =====================

@router.post("/create")
async def create_bot_instance(payload: BotInstanceCreate):
    """
    새 봇 인스턴스 생성
    
    Request:
    {
        "name": "BTC 보수적 봇",
        "bot_type": "ai_trend",  // or "grid"
        "strategy_id": 1,        // ai_trend만 필요
        "symbol": "BTCUSDT",
        "allocation_percent": 30.0,
        "max_leverage": 10,
        "max_positions": 3
    }
    
    Response:
    {
        "success": true,
        "bot_id": 1,
        "message": "봇이 생성되었습니다"
    }
    
    Validation:
    - 총 할당 비율이 100%를 초과하면 에러
    - 사용자당 최대 10개 봇 제한
    """
    pass


@router.get("/list")
async def list_bot_instances():
    """
    사용자의 모든 봇 목록 조회
    
    Response:
    {
        "bots": [...],
        "total_allocation": 80.0,
        "available_allocation": 20.0,
        "running_count": 2,
        "total_count": 3
    }
    """
    pass


@router.get("/{bot_id}")
async def get_bot_instance(bot_id: int):
    """봇 상세 정보 조회"""
    pass


@router.patch("/{bot_id}")
async def update_bot_instance(bot_id: int, payload: BotInstanceUpdate):
    """봇 설정 수정 (실행 중이 아닐 때만)"""
    pass


@router.delete("/{bot_id}")
async def delete_bot_instance(bot_id: int):
    """봇 삭제 (실행 중이면 먼저 중지)"""
    pass


# ===================== 실행 제어 =====================

@router.post("/{bot_id}/start")
async def start_bot(bot_id: int):
    """
    특정 봇 시작
    
    Flow:
    1. 봇 존재 및 소유권 확인
    2. 이미 실행 중인지 확인
    3. 할당된 잔고 확인
    4. BotManager에 시작 요청
    5. 상태 업데이트
    6. 텔레그램 알림 발송
    """
    pass


@router.post("/{bot_id}/stop")
async def stop_bot(bot_id: int):
    """특정 봇 중지 및 포지션 청산"""
    pass


@router.post("/start-all")
async def start_all_bots():
    """활성화된 모든 봇 시작"""
    pass


@router.post("/stop-all")
async def stop_all_bots():
    """모든 봇 중지"""
    pass


# ===================== 통계 =====================

@router.get("/{bot_id}/stats")
async def get_bot_stats(bot_id: int):
    """봇별 상세 통계"""
    pass


@router.get("/stats/summary")
async def get_all_bots_summary():
    """전체 봇 통계 요약"""
    pass
```

### 2. 그리드 봇 API (`api/grid_bot.py`)

```python
router = APIRouter(prefix="/grid-bot", tags=["Grid Bot"])

@router.post("/{bot_id}/configure")
async def configure_grid(bot_id: int, payload: GridBotConfig):
    """
    그리드 봇 설정
    
    Request:
    {
        "lower_price": 85000,
        "upper_price": 100000,
        "grid_count": 15,
        "grid_mode": "arithmetic",
        "total_investment": 1000,  // USDT
        "trigger_price": null,     // 즉시 시작
        "stop_upper": 105000,
        "stop_lower": 80000
    }
    
    Validation:
    - upper_price > lower_price
    - grid_count: 2 ~ 100
    - total_investment <= allocated_balance
    """
    pass


@router.get("/{bot_id}/grids")
async def get_grid_status(bot_id: int):
    """
    그리드 상태 조회
    
    Response:
    {
        "config": {...},
        "grids": [
            {"index": 0, "price": 85000, "status": "buy_filled", "profit": 12.5},
            {"index": 1, "price": 86000, "status": "sell_placed", "profit": 0},
            ...
        ],
        "total_profit": 150.25,
        "active_orders": 8
    }
    """
    pass


@router.post("/{bot_id}/reconfigure")
async def reconfigure_grid(bot_id: int, payload: GridBotConfig):
    """그리드 재설정 (기존 주문 취소 후)"""
    pass
```

---

## 🔄 서비스 로직 설계

### 1. AllocationManager (잔고 할당 관리)

**파일**: `services/allocation_manager.py`

```python
class AllocationManager:
    """
    사용자별 잔고 할당 관리
    
    역할:
    - 봇별 할당 잔고 계산
    - 동시 주문 시 잔고 충돌 방지
    - 사용 가능 잔고 조회
    """
    
    def __init__(self):
        self._locks: Dict[int, asyncio.Lock] = {}  # user_id -> Lock
        self._cache: Dict[int, float] = {}         # user_id -> total_balance
        self._cache_time: Dict[int, float] = {}    # user_id -> timestamp
        self.CACHE_TTL = 10  # 10초 캐시
    
    async def get_user_lock(self, user_id: int) -> asyncio.Lock:
        """사용자별 락 반환"""
        if user_id not in self._locks:
            self._locks[user_id] = asyncio.Lock()
        return self._locks[user_id]
    
    async def get_total_balance(self, user_id: int, bitget_client) -> float:
        """
        사용자 총 잔고 조회 (캐싱)
        
        - 10초 동안 캐시
        - API Rate Limit 방지
        """
        now = time.time()
        if user_id in self._cache and (now - self._cache_time.get(user_id, 0)) < self.CACHE_TTL:
            return self._cache[user_id]
        
        balance = await bitget_client.fetch_balance()
        total = float(balance.get("USDT", {}).get("free", 0))
        
        self._cache[user_id] = total
        self._cache_time[user_id] = now
        return total
    
    async def get_allocated_balance(
        self, 
        user_id: int, 
        bot_instance_id: int,
        bitget_client
    ) -> float:
        """
        특정 봇에 할당된 잔고 계산
        
        Formula: 총잔고 * (allocation_percent / 100)
        """
        total = await self.get_total_balance(user_id, bitget_client)
        
        # DB에서 봇의 할당 비율 조회
        async with get_session() as session:
            bot = await session.get(BotInstance, bot_instance_id)
            if not bot:
                return 0
            return total * (float(bot.allocation_percent) / 100)
    
    async def validate_allocation(
        self, 
        user_id: int, 
        new_allocation: float,
        exclude_bot_id: int = None
    ) -> tuple[bool, str]:
        """
        새 할당이 가능한지 검증
        
        Returns: (가능 여부, 메시지)
        """
        async with get_session() as session:
            query = select(func.sum(BotInstance.allocation_percent)).where(
                BotInstance.user_id == user_id,
                BotInstance.is_active == True
            )
            if exclude_bot_id:
                query = query.where(BotInstance.id != exclude_bot_id)
            
            result = await session.execute(query)
            current_total = result.scalar() or 0
            
            if current_total + new_allocation > 100:
                return False, f"할당 초과: 현재 {current_total}% 사용 중, 최대 {100 - current_total}% 가능"
            
            return True, "OK"
    
    async def request_order_amount(
        self,
        user_id: int,
        bot_instance_id: int,
        amount: float,
        bitget_client
    ) -> bool:
        """
        주문 금액 요청 (락 사용)
        
        여러 봇이 동시에 주문할 때 잔고 충돌 방지
        """
        lock = await self.get_user_lock(user_id)
        
        async with lock:
            allocated = await self.get_allocated_balance(user_id, bot_instance_id, bitget_client)
            
            # 현재 사용 중인 금액 계산 (열린 포지션)
            # ... 포지션 조회 로직 ...
            
            available = allocated - used
            
            if amount > available:
                logger.warning(f"Bot {bot_instance_id}: Insufficient balance. "
                             f"Requested: {amount}, Available: {available}")
                return False
            
            return True


# 싱글톤 인스턴스
allocation_manager = AllocationManager()
```

### 2. BotRunner 리팩토링

**파일**: `services/bot_runner.py` 수정

```python
class BotRunner:
    def __init__(self, market_queue: asyncio.Queue):
        self.market_queue = market_queue
        
        # 변경: user_id -> bot_instance_id
        self.tasks: Dict[int, asyncio.Task] = {}  # bot_instance_id -> Task
        
        # 추가: 사용자별 봇 목록 추적
        self.user_bots: Dict[int, Set[int]] = {}  # user_id -> {bot_instance_ids}
        
        # 추가: 잔고 할당 관리자
        self.allocation_manager = allocation_manager
    
    def is_running(self, bot_instance_id: int) -> bool:
        """특정 봇이 실행 중인지 확인"""
        return bot_instance_id in self.tasks and not self.tasks[bot_instance_id].done()
    
    def is_user_running_any(self, user_id: int) -> bool:
        """사용자가 실행 중인 봇이 있는지 확인"""
        return user_id in self.user_bots and len(self.user_bots[user_id]) > 0
    
    async def start_bot_instance(self, session_factory, user_id: int, bot_instance_id: int):
        """특정 봇 인스턴스 시작"""
        if self.is_running(bot_instance_id):
            logger.warning(f"Bot {bot_instance_id} is already running")
            return
        
        task = asyncio.create_task(
            self._run_bot_loop(session_factory, user_id, bot_instance_id)
        )
        self.tasks[bot_instance_id] = task
        
        # 사용자별 봇 목록 업데이트
        if user_id not in self.user_bots:
            self.user_bots[user_id] = set()
        self.user_bots[user_id].add(bot_instance_id)
        
        logger.info(f"Started bot instance {bot_instance_id} for user {user_id}")
    
    def stop_bot_instance(self, user_id: int, bot_instance_id: int):
        """특정 봇 인스턴스 중지"""
        if self.is_running(bot_instance_id):
            self.tasks[bot_instance_id].cancel()
            
            if user_id in self.user_bots:
                self.user_bots[user_id].discard(bot_instance_id)
            
            logger.info(f"Stopped bot instance {bot_instance_id}")
    
    async def _run_bot_loop(self, session_factory, user_id: int, bot_instance_id: int):
        """
        개별 봇 인스턴스 실행 루프
        
        기존 _run_loop에서 분리된 로직
        """
        async with session_factory() as session:
            # 1. 봇 인스턴스 정보 로드
            bot_instance = await session.get(BotInstance, bot_instance_id)
            if not bot_instance:
                logger.error(f"Bot instance {bot_instance_id} not found")
                return
            
            # 2. 봇 타입에 따라 분기
            if bot_instance.bot_type == BotType.GRID:
                # 그리드 봇 러너 사용
                await self._run_grid_bot(session_factory, bot_instance)
            else:
                # AI 추세 봇 러너 사용
                await self._run_ai_bot(session_factory, bot_instance)
    
    async def _run_ai_bot(self, session_factory, bot_instance: BotInstance):
        """
        AI 추세 봇 실행 (기존 로직과 유사)
        
        변경점:
        - 전체 잔고 대신 할당된 잔고만 사용
        - bot_instance_id로 거래 기록
        """
        # ... 기존 로직 + 잔고 할당 로직 ...
        
        # 잔고 계산 시
        allocated_balance = await self.allocation_manager.get_allocated_balance(
            bot_instance.user_id,
            bot_instance.id,
            bitget_client
        )
        
        # 주문 크기 계산
        order_value = allocated_balance * (position_size_percent / 100) * leverage
        
        # 주문 전 잔고 확인
        can_order = await self.allocation_manager.request_order_amount(
            bot_instance.user_id,
            bot_instance.id,
            order_value,
            bitget_client
        )
        
        if not can_order:
            logger.warning(f"Bot {bot_instance.id}: Insufficient allocated balance")
            continue
```

### 3. GridBotRunner (그리드 봇)

**파일**: `services/grid_bot_runner.py` (신규)

```python
class GridBotRunner:
    """
    그리드 봇 실행 로직
    
    특징:
    - 지정가 주문 사용
    - 가격 범위 내 자동 주문 설정
    - 체결 시 반대 주문 자동 설정
    """
    
    def __init__(self, bot_instance: BotInstance, config: GridBotConfig):
        self.bot_instance = bot_instance
        self.config = config
        self.grids: List[GridLevel] = []
        self._running = False
    
    def _create_grids(self) -> List[dict]:
        """
        그리드 레벨 생성
        
        arithmetic: 균등 간격
        geometric: 기하 간격 (% 기준)
        """
        grids = []
        
        if self.config.grid_mode == GridMode.ARITHMETIC:
            step = (float(self.config.upper_price) - float(self.config.lower_price)) / self.config.grid_count
            for i in range(self.config.grid_count + 1):
                price = float(self.config.lower_price) + (i * step)
                grids.append({
                    "index": i,
                    "price": price,
                    "qty": float(self.config.per_grid_amount) / price
                })
        else:
            # geometric 모드
            ratio = (float(self.config.upper_price) / float(self.config.lower_price)) ** (1 / self.config.grid_count)
            for i in range(self.config.grid_count + 1):
                price = float(self.config.lower_price) * (ratio ** i)
                grids.append({
                    "index": i,
                    "price": price,
                    "qty": float(self.config.per_grid_amount) / price
                })
        
        return grids
    
    async def initialize(self, session: AsyncSession, bitget_client):
        """
        그리드 초기화
        
        1. 현재가 확인
        2. 현재가 아래 → 매수 주문
        3. 현재가 위 → 나중에 처리
        """
        # 현재가 조회
        ticker = await bitget_client.get_ticker(self.bot_instance.symbol)
        current_price = float(ticker["last"])
        
        # 그리드 생성
        self.grids = self._create_grids()
        
        # DB에 그리드 저장
        for grid in self.grids:
            grid_order = GridOrder(
                grid_config_id=self.config.id,
                grid_index=grid["index"],
                grid_price=grid["price"],
                status=GridOrderStatus.PENDING
            )
            session.add(grid_order)
        
        await session.commit()
        
        # 현재가 아래 그리드에 매수 주문
        for grid in self.grids:
            if grid["price"] < current_price:
                await self._place_buy_order(grid, bitget_client, session)
    
    async def _place_buy_order(self, grid: dict, bitget_client, session):
        """매수 지정가 주문"""
        try:
            result = await bitget_client.place_limit_order(
                symbol=self.bot_instance.symbol,
                side=OrderSide.BUY,
                size=grid["qty"],
                price=grid["price"]
            )
            
            # DB 업데이트
            grid_order = await session.execute(
                select(GridOrder).where(
                    GridOrder.grid_config_id == self.config.id,
                    GridOrder.grid_index == grid["index"]
                )
            )
            order = grid_order.scalar_one()
            order.buy_order_id = result.get("orderId")
            order.status = GridOrderStatus.BUY_PLACED
            await session.commit()
            
        except Exception as e:
            logger.error(f"Failed to place buy order at grid {grid['index']}: {e}")
    
    async def on_order_filled(self, order_id: str, fill_price: float, session, bitget_client):
        """
        주문 체결 시 처리
        
        매수 체결 → 한 칸 위에 매도 주문
        매도 체결 → 같은 칸에 매수 주문 (사이클 반복)
        """
        # 체결된 주문 찾기
        result = await session.execute(
            select(GridOrder).where(
                or_(
                    GridOrder.buy_order_id == order_id,
                    GridOrder.sell_order_id == order_id
                )
            )
        )
        grid_order = result.scalar_one_or_none()
        
        if not grid_order:
            return
        
        if grid_order.buy_order_id == order_id:
            # 매수 체결 → 매도 주문
            grid_order.status = GridOrderStatus.BUY_FILLED
            grid_order.buy_filled_price = fill_price
            grid_order.buy_filled_at = datetime.utcnow()
            
            # 다음 그리드 (한 칸 위)에 매도 주문
            next_grid_price = self.grids[grid_order.grid_index + 1]["price"] if grid_order.grid_index < len(self.grids) - 1 else None
            
            if next_grid_price:
                sell_result = await bitget_client.place_limit_order(
                    symbol=self.bot_instance.symbol,
                    side=OrderSide.SELL,
                    size=grid_order.buy_filled_qty,
                    price=next_grid_price
                )
                grid_order.sell_order_id = sell_result.get("orderId")
                grid_order.status = GridOrderStatus.SELL_PLACED
        
        elif grid_order.sell_order_id == order_id:
            # 매도 체결 → 수익 계산 + 매수 주문 재설정
            grid_order.status = GridOrderStatus.SELL_FILLED
            grid_order.sell_filled_price = fill_price
            grid_order.sell_filled_at = datetime.utcnow()
            
            # 수익 계산
            profit = (fill_price - float(grid_order.buy_filled_price)) * float(grid_order.buy_filled_qty)
            grid_order.profit = profit
            
            # 총 수익 업데이트
            self.config.realized_profit = float(self.config.realized_profit or 0) + profit
            
            # 같은 그리드에 매수 주문 재설정 (사이클)
            await self._place_buy_order(
                {"index": grid_order.grid_index, "price": float(grid_order.grid_price), "qty": float(grid_order.buy_filled_qty)},
                bitget_client,
                session
            )
        
        await session.commit()
```

---

## 📱 프론트엔드 설계 ✅ 구현 완료 (2025-12-12)

### 1. 새로운 페이지: BotManagement.jsx ✅

**파일**: `frontend/src/pages/BotManagement.jsx` (427 lines)

**주요 기능:**

- 통계 요약 카드 (총 봇, 실행 중, 총 PNL, 평균 승률)
- AllocationBar 잔고 할당 시각화
- BotCard 그리드 레이아웃
- 전체 시작/중지 버튼
- 모달 관리 (통계, 편집)
- 반응형 디자인 (모바일/데스크톱)
- 다크 테마 UI (비트겟 스타일)

```jsx
// 실제 구현된 구조
export default function BotManagement() {
    const [bots, setBots] = useState([]);
    const [totalAllocation, setTotalAllocation] = useState(0);
    const [availableAllocation, setAvailableAllocation] = useState(100);
    const [runningCount, setRunningCount] = useState(0);
    const [summary, setSummary] = useState(null);
    
    // 모달 상태
    const [statsModal, setStatsModal] = useState({ open: false, botId: null });
    const [editModal, setEditModal] = useState({ open: false, bot: null });
    
    return (
        <div style={{ background: '#0d0d14', minHeight: 'calc(100vh - 64px)' }}>
            {/* 헤더: 제목 + 전체 시작/중지 버튼 */}
            
            {/* 통계 요약 카드 (4개) */}
            <Row gutter={[16, 16]}>
                <Col xs={12} sm={6}><Card>총 봇</Card></Col>
                <Col xs={12} sm={6}><Card>실행 중</Card></Col>
                <Col xs={12} sm={6}><Card>총 손익</Card></Col>
                <Col xs={12} sm={6}><Card>평균 승률</Card></Col>
            </Row>
            
            {/* 잔고 할당 시각화 */}
            <AllocationBar bots={bots} totalAllocation={totalAllocation} />
            
            {/* 봇 카드 그리드 */}
            <Row gutter={[16, 16]}>
                {bots.map(bot => (
                    <Col xs={24} sm={12} lg={8} xl={6} key={bot.id}>
                        <BotCard
                            bot={bot}
                            onStart={handleStartBot}
                            onStop={handleStopBot}
                            onEdit={handleEditBot}
                            onDelete={handleDeleteBot}
                            onViewStats={handleViewStats}
                        />
                    </Col>
                ))}
                
                {/* 새 봇 추가 카드 */}
                {availableAllocation > 0 && (
                    <Col xs={24} sm={12} lg={8} xl={6}>
                        <AddBotCard 
                            maxAllocation={availableAllocation}
                            strategies={strategies}
                            onCreate={handleCreateBot}
                        />
                    </Col>
                )}
            </Row>
            
            {/* 모달들 */}
            <BotStatsModal ... />
            <EditBotModal ... />
        </div>
    );
}
```

### 2. 봇 컴포넌트들 ✅

**폴더**: `frontend/src/components/bot/`

| 파일 | 줄 수 | 설명 |
|------|------|------|
| `AllocationBar.jsx` | 140 | 잔고 할당 시각화 바 (색상별 봇 구분, 툴팁, 범례) |
| `BotCard.jsx` | 309 | 봇 카드 (상태 표시, PNL, 승률, 액션 버튼) |
| `AddBotCard.jsx` | 294 | 봇 추가 카드 + 생성 모달 (타입 선택, 설정 입력) |
| `BotStatsModal.jsx` | 200+ | 봇 상세 통계 모달 (API 호출, 통계 표시) |
| `EditBotModal.jsx` | 200+ | 봇 설정 편집 모달 (폼 프리필, 수정 저장) |

**BotCard 주요 기능:**

- 봇 상태 표시 (running: 녹색 글로우, stopped: 회색)
- 봇 타입 태그 (AI 추세 / 그리드)
- 통계 표시: PNL, 승률, 총 거래 수, 레버리지
- 액션 버튼: 시작/중지, 편집, 통계, 삭제
- 로딩 상태 처리

**AddBotCard 폼 필드:**

- 봇 타입 선택 (AI 추세 / 그리드)
- 이름, 설명
- 심볼 선택 (BTC, ETH, BNB, SOL, ADA, XRP, DOGE)
- 전략 선택 (AI 봇 전용, StrategyContext에서 가져옴)
- 잔고 할당 슬라이더 (0~maxAllocation%)
- 최대 레버리지 (1~100x)
- 최대 포지션 수 (1~20)
- 손절/익절 비율 (%)
- 텔레그램 알림 토글

### 3. API 클라이언트: botInstances.js ✅

**파일**: `frontend/src/api/botInstances.js` (90 lines)

```javascript
// 실제 구현된 API 클라이언트
import apiClient from './index';

const botInstancesAPI = {
    // 목록 조회
    list: async () => {
        const response = await apiClient.get('/bot-instances/list');
        return response.data;
    },
    
    // CRUD
    create: async (data) => { ... },
    get: async (botId) => { ... },
    update: async (botId, data) => { ... },
    delete: async (botId) => { ... },
    
    // 시작/중지
    start: async (botId) => { ... },
    stop: async (botId) => { ... },
    startAll: async () => { ... },
    stopAll: async () => { ... },
    
    // 통계
    getStats: async (botId) => { ... },
    getSummary: async () => { ... },
};

export default botInstancesAPI;
```

### 4. 라우팅 및 메뉴 ✅

**수정 파일:**

- `frontend/src/App.jsx` - `/bots` 라우트 추가
- `frontend/src/components/layout/MainLayout.jsx` - 사이드바에 "봇 관리" 메뉴 추가

```jsx
// App.jsx 라우트
<Route
  path="/bots"
  element={
    <ProtectedRoute>
      <BotManagement />
    </ProtectedRoute>
  }
/>

// MainLayout.jsx 메뉴
{
    key: '/bots',
    icon: <RobotOutlined />,
    label: '봇 관리',
}
```

### 5. 그리드 봇 API (미구현 - 대기)

```javascript
export const gridBotAPI = {
    configure: (botId, config) => apiClient.post(`/grid-bot/${botId}/configure`, config),
    getGrids: (botId) => apiClient.get(`/grid-bot/${botId}/grids`),
    reconfigure: (botId, config) => apiClient.post(`/grid-bot/${botId}/reconfigure`, config),
};
```

---

## 🧪 테스트 계획

### 단위 테스트

```python
# tests/test_allocation_manager.py
class TestAllocationManager:
    async def test_validate_allocation_under_100(self):
        """100% 미만 할당 허용"""
        pass
    
    async def test_validate_allocation_over_100(self):
        """100% 초과 할당 거부"""
        pass
    
    async def test_concurrent_order_lock(self):
        """동시 주문 시 락 동작"""
        pass


# tests/test_grid_bot.py
class TestGridBot:
    def test_create_arithmetic_grids(self):
        """균등 간격 그리드 생성"""
        pass
    
    def test_create_geometric_grids(self):
        """기하 간격 그리드 생성"""
        pass
    
    async def test_buy_fill_triggers_sell(self):
        """매수 체결 시 매도 주문 생성"""
        pass
```

### 통합 테스트

```python
# tests/integration/test_multi_bot.py
class TestMultiBot:
    async def test_user_runs_multiple_bots(self):
        """사용자가 여러 봇 동시 실행"""
        pass
    
    async def test_allocation_limit_enforced(self):
        """할당 한도 초과 시 주문 거부"""
        pass
```

---

## 📋 체크리스트 사용법

### 작업 시작 시

1. 본인 이름을 "담당자" 열에 기입
2. "시작일"에 날짜 기입
3. 상태를 `[ ]` → `[🔄]` 변경

### 작업 완료 시

1. 상태를 `[🔄]` → `[✅]` 변경
2. "완료일"에 날짜 기입
3. PR 링크가 있으면 추가

### 예시

```markdown
| 2.1 | [✅] `api/bot_instances.py` 파일 생성 | 완료 | 김개발 | 12/10 | 12/11 | PR #45 |
```

---

**끝**
