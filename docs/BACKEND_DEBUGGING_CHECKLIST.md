# 🛠️ 백엔드 전체 디버깅 체크리스트

이 문서는 백엔드 시스템의 안정성과 기능 정확성을 검증하기 위한 포괄적인 체크리스트입니다. 최근 수정된 기능(포지션 청산, 봇 자동 시작 등)을 포함하여 전체적인 시스템을 점검할 수 있도록 구성되었습니다.

## 🚨 최근 수정 사항 집중 점검 (Priority High)

가장 최근에 수정된 기능들이 정상적으로 동작하는지 우선적으로 확인해야 합니다.

| 기능 | 테스트 항목 | 예상 결과 | 확인 방법 |
|------|------------|-----------|-----------|
| **포지션 청산** | `POST /api/v1/bitget/positions/close` 호출 | 200 OK 및 포지션 청산됨 | 1. 프론트엔드 포지션 목록에서 'Close' 버튼 클릭<br>2. 백엔드 로그에 `Closing {side} position` 확인<br>3. Bitget 앱/웹에서 포지션 사라짐 확인 |
| **봇 자동 시작** | 템플릿(AI/Grid)으로 봇 생성 | 봇 생성 즉시 `Running` 상태 | 1. 템플릿 사용 모달에서 봇 생성<br>2. 'My Bots' 탭에서 상태가 'Running'인지 확인<br>3. DB `bot_instances` 테이블 `is_running=true` 확인 |
| **최소 투자금** | AI Trend 봇 생성 (10 USDT) | 정상 생성됨 | 1. 10 USDT로 봇 생성 시도 -> 성공<br>2. 9 USDT로 생성 시도 -> 실패 (Validation Error) |
| **그리드 투자금** | 그리드 봇 생성 (Total 10 USDT) | 정상 생성됨 | 1. 총 10 USDT, 그리드 5개 ($2/grid) -> 성공<br>2. 총 9 USDT -> 실패 |

---

## 1. 🏗️ 시스템 및 인프라 점검 (System Health)

서버의 기본 상태와 연결성을 점검합니다.

- [ ] **Docker 컨테이너 상태**
  - `docker compose ps` 명령어로 모든 컨테이너(`backend`, `frontend`, `postgres`, `redis`)가 `Up (healthy)` 상태인지 확인.
- [ ] **데이터베이스 연결**
  - 백엔드 로그에 `Database initialized` 메시지가 있는지 확인.
  - `docker exec -it trading-postgres psql -U trading_user -d trading_db` 접속 가능 여부 확인.
- [ ] **Redis 연결**
  - Celery 워커나 캐싱 기능이 Redis에 정상적으로 연결되었는지 로그 확인.
- [ ] **환경 변수 적용**
  - `.env.production` 파일의 설정(DB 비밀번호, API URL 등)이 컨테이너에 올바르게 주입되었는지 확인.

## 2. 🔐 인증 및 사용자 관리 (Auth & User)

사용자 접근 제어 및 보안 기능을 점검합니다.

- [ ] **회원가입 및 로그인**
  - 신규 회원가입 진행 및 로그인 성공 여부.
  - JWT 토큰 발급 및 만료 시간 확인.
- [ ] **관리자 권한**
  - `admin@admin.com` 계정으로 로그인 후 관리자 전용 API 접근 가능 여부.
- [ ] **API 키 관리**
  - Bitget API 키 등록, 수정, 삭제 테스트.
  - API 키가 DB에 암호화되어 저장되는지 확인 (`api_keys` 테이블).
  - 등록된 API 키로 잔고 조회(`GET /api/v1/bitget/account/balance`) 성공 여부.

## 3. 🤖 봇 관리 및 실행 (Bot Management)

봇의 생명주기와 전략 실행을 점검합니다.

- [ ] **봇 생성 (Create)**
  - **AI Trend Bot**: 템플릿 선택 -> 생성 -> DB `bot_instances` 확인.
  - **Grid Bot**: 파라미터 설정 -> 생성 -> DB `bot_instances` 및 `grid_bot_configs` 확인.
- [ ] **봇 제어 (Control)**
  - **Start**: 중지된 봇 시작 -> 로그에 `Bot {id} started` 기록 확인.
  - **Stop**: 실행 중인 봇 중지 -> 로그에 `Bot {id} stopped` 기록 확인.
  - **Delete**: 봇 삭제 -> 목록에서 사라짐, DB `is_active=false` (Soft Delete) 확인.
- [ ] **다중 봇 실행**
  - 여러 개의 봇(예: BTC 롱, ETH 숏)을 동시에 실행하고 서로 간섭 없이 동작하는지 확인.

## 4. 📉 트레이딩 및 시장 데이터 (Trading & Market)

실제 거래소와의 상호작용을 점검합니다. **(금전적 손실 주의)**

- [ ] **실시간 시세 수신**
  - 프론트엔드 차트나 호가창이 실시간으로 업데이트되는지 확인.
  - 백엔드 로그에 `Broadcasted: candle_update` 메시지 확인.
- [ ] **주문 실행 (Order Execution)**
  - **Market Order**: 시장가 주문 테스트 (소액).
  - **Limit Order**: 지정가 주문 테스트 (현재가보다 먼 가격으로).
  - **Cancel Order**: 미체결 주문 취소 테스트.
- [ ] **포지션 동기화**
  - 거래소에서 포지션 진입 후, 대시보드에 해당 포지션이 표시되는지 확인.
  - PnL(손익) 및 ROE(수익률) 계산이 정확한지 비교.

## 5. 🕸️ 그리드 봇 심화 점검 (Grid Bot Specific)

그리드 봇의 복잡한 로직을 검증합니다.

- [ ] **그리드 주문 생성**
  - 봇 시작 시 상/하한가 범위 내에 매수/매도 주문이 촘촘하게 깔리는지 확인 (`GET /api/v1/bitget/orders/open`).
- [ ] **주문 사이클 (Buy -> Sell)**
  - 매수 주문 체결 시 -> 즉시 상응하는 매도 주문이 생성되는지 로그 확인.
- [ ] **주문 사이클 (Sell -> Buy)**
  - 매도 주문 체결 시 -> 즉시 하방에 매수 주문이 다시 생성되는지 확인.
- [ ] **예외 처리**
  - 급격한 가격 변동 시 주문이 누락되지 않는지 확인.
  - API Rate Limit 걸렸을 때 재시도 로직 동작 여부.

## 6. 📊 데이터 분석 및 백테스팅 (Analytics & Backtest)

- [ ] **백테스팅 실행**
  - 관리자 페이지에서 백테스트 실행 -> 결과(ROI, MDD)가 정상적으로 계산되어 나오는지 확인.
  - 과거 데이터가 없는 기간 요청 시 자동으로 데이터를 다운로드하는지 확인.
- [ ] **수익률 분석**
  - 대시보드의 수익금/수익률 차트가 거래 내역을 기반으로 올바르게 그려지는지 확인.

## 7. 📡 웹소켓 및 알림 (WebSocket & Notification)

- [ ] **웹소켓 연결**
  - 브라우저 개발자 도구(Network -> WS)에서 웹소켓 연결이 끊기지 않고 유지되는지 확인.
  - 봇 상태 변경 시 실시간으로 UI에 반영되는지 확인.
- [ ] **텔레그램 알림**
  - 봇 시작/중지, 주문 체결 시 텔레그램으로 메시지가 오는지 확인.
  - 에러 발생 시 알림 전송 여부.

---

## 🛠️ 디버깅 팁

### 로그 확인 방법

```bash
# 백엔드 전체 로그 (실시간)
docker compose --env-file .env.production logs -f backend

# 특정 시간대 로그 검색 (예: 에러만)
docker compose --env-file .env.production logs backend | grep "ERROR"
```

### DB 직접 조회 (PostgreSQL)

```bash
# DB 접속
docker exec -it trading-postgres psql -U trading_user -d trading_db

# 봇 상태 확인 쿼리
SELECT id, name, bot_type, is_running, created_at FROM bot_instances ORDER BY created_at DESC LIMIT 5;

# 포지션 확인 쿼리
SELECT symbol, side, size, entry_price, pnl FROM positions WHERE size > 0;
```

### API 직접 테스트 (cURL)

```bash
# 봇 목록 조회
curl -X GET http://localhost:8000/api/v1/bots \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```
