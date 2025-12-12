# 실시간 로그 뷰어 테스트 가이드

## ✅ 배포 완료

실시간 로그 뷰어가 성공적으로 배포되었습니다.

## 🧪 테스트 방법

### 1단계: 웹 UI 접속
1. 브라우저에서 http://158.247.245.197:3000 접속
2. 로그인: `admin@admin.com` / 비밀번호

### 2단계: 트레이딩 페이지로 이동
1. 왼쪽 메뉴에서 **"트레이딩"** 클릭
2. 화면이 로딩되는지 확인

### 3단계: 봇 시작
1. 오른쪽 패널에서 **전략 선택** 드롭다운 클릭
2. 아무 전략이나 선택 (예: "균형적 RSI 다이버전스 전략")
3. **Start** 버튼 클릭
4. 확인 모달이 뜨면 **"확인 - 봇 시작"** 클릭

### 4단계: 로그 뷰어 확인
1. 봇이 시작되면 화면 하단에 **"실시간 봇 로그"** 카드가 나타남
2. 검은색 배경의 터미널 스타일 로그 화면 확인

### 5단계: 로그 내용 확인

다음과 같은 로그들이 실시간으로 표시되어야 합니다:

#### ✅ 예상 로그 유형

**1. 시장 데이터 처리**
```
🔄 Processing market data: BTCUSDT @ $92,503.90 (user 1)
```

**2. 전략 로딩**
```
Loading Proven Balanced Strategy (RSI Divergence)
```

**3. 전략 컴파일**
```
Strategy code compiled successfully
```

**4. AI 신호 체크 (가장 중요!)**
```
🔍 Signal check - action:hold, size_from_strategy:0, size_metadata:None
```

**5. AI 신호 결과**
```
Strategy signal for user 1: hold (confidence: 0.50, reason: No signal)
```

**6. 캔들 업데이트**
```
📡 Broadcasted: candle_update for BTCUSDT - candle: {...}
```

### 6단계: 로그 뷰어 기능 테스트

#### 일시정지/재개
1. **일시정지** 버튼 클릭
2. 로그가 멈추는지 확인
3. 상단에 "일시정지" 태그 표시 확인
4. **재개** 버튼 클릭
5. 버퍼에 쌓인 로그가 한 번에 표시되는지 확인

#### 자동 스크롤
1. **자동 스크롤** 스위치를 OFF로 변경
2. 스크롤이 자동으로 아래로 내려가지 않는지 확인
3. 다시 ON으로 변경
4. 새 로그가 들어올 때마다 자동 스크롤 확인

#### 로그 클리어
1. **클리어** 버튼 클릭
2. 모든 로그가 삭제되는지 확인
3. 새 로그가 계속 들어오는지 확인

#### 로그 다운로드
1. **다운로드** 버튼 클릭
2. .txt 파일이 다운로드되는지 확인
3. 파일 열어서 로그 내용 확인

## 🔍 예상 결과

### 정상 동작 시

- ✅ 1~2초마다 새 로그가 계속 표시됨
- ✅ 로그 레벨별로 색상이 다름:
  - **INFO**: 파란색
  - **WARNING**: 주황색
  - **ERROR**: 빨간색
- ✅ 시간 정보가 왼쪽에 표시됨
- ✅ 최하단에 "총 N개 로그" 표시
- ✅ 연결 상태 "연결됨" (녹색 점)

### 비정상 동작 시

#### 문제 1: "로그를 기다리는 중..." 계속 표시
**원인**: WebSocket 연결 실패 또는 로그 핸들러 미작동

**해결 방법**:
1. F12 개발자 도구 열기
2. Console 탭에서 에러 확인
3. Network 탭에서 WebSocket 연결 확인
4. 봇을 중지하고 다시 시작

#### 문제 2: "연결 끊김" (빨간색 점)
**원인**: WebSocket 연결 끊김

**해결 방법**:
1. 페이지 새로고침 (F5)
2. 다시 로그인
3. 봇을 다시 시작

#### 문제 3: 로그가 너무 빠르게 흐름
**원인**: 정상 동작 (초당 여러 개의 로그 발생)

**해결 방법**:
1. **일시정지** 버튼 클릭
2. 천천히 확인
3. 필요 시 **다운로드** 버튼으로 저장

## 📊 AI 신호 디버깅

### 왜 거래가 발생하지 않는지 확인하는 방법

로그에서 다음 항목을 확인하세요:

#### 1. AI 신호가 "hold"인 경우
```
Strategy signal for user 1: hold (confidence: 0.50, reason: No signal)
```
→ **원인**: AI가 진입 조건을 충족하지 못함
→ **해결**: 다른 전략 시도 또는 시장 상황 변화 대기

#### 2. AI 신호가 "buy" 또는 "sell"인 경우
```
Strategy signal for user 1: buy (confidence: 0.85, reason: Strong bullish signal)
```
→ **원인**: AI가 매수 신호를 보냈으나 실제 주문이 실행되지 않음
→ **추가 확인**: 이후 로그에서 에러 메시지 확인

#### 3. 리스크 제한에 걸린 경우
```
🚫 Trade BLOCKED for user 1: Daily loss limit exceeded!
🚫 Trade BLOCKED for user 1: Max positions reached!
```
→ **원인**: 리스크 관리 설정 초과
→ **해결**: Settings 페이지에서 리스크 설정 조정

#### 4. 잔고 부족
```
⚠️ No available balance for user 1, using minimum size
```
→ **원인**: 거래소 잔고 부족
→ **해결**: 거래소에 자금 입금

#### 5. API 에러
```
❌ Failed to calculate order size for user 1: ...
```
→ **원인**: Bitget API 에러
→ **해결**: Settings에서 API 키 재설정

## 🎯 성공 사례

로그에서 다음과 같은 메시지가 보이면 **실제 거래가 발생한 것**입니다:

```
💰 Starting balance query for user 1
✅ Calculated order size for user 1: 0.001000 BTC (balance: $84.07, position: 35.0%, leverage: 10x)
Executing buy order for user 1 at 92503.9 (size: 0.001, confidence: 0.85)
Bitget order executed successfully for user 1: {...}
📱 Telegram: Trade entry notification sent for user 1
```

## 📝 로그 분석 팁

### 로그 레벨 이해하기

- **DEBUG**: 개발자용 상세 로그 (일반적으로 표시 안 됨)
- **INFO**: 일반 정보 (시장 데이터, AI 신호 등)
- **WARNING**: 경고 (잔고 부족, 최소 주문량 사용 등)
- **ERROR**: 에러 (API 실패, 주문 실패 등)
- **CRITICAL**: 치명적 에러 (봇 중지될 수 있음)

### 중요한 로그 키워드

- `🔍 Signal check` - AI가 신호를 분석 중
- `💰 Starting balance` - 실제 거래 준비 중
- `Executing` - 주문 실행 중
- `successfully` - 성공
- `Failed` / `Error` - 실패 (원인 확인 필요)

## 🛠️ 고급 기능

### 로그 필터링 (향후 업데이트 예정)
- 로그 레벨별 필터 (INFO만 보기, ERROR만 보기 등)
- 키워드 검색 (예: "buy", "error")

### 로그 영구 저장 (향후 업데이트 예정)
- 데이터베이스에 로그 저장
- 과거 로그 조회 기능

## ✅ 체크리스트

배포 후 다음 항목을 확인하세요:

- [ ] 웹 UI 접속 가능
- [ ] 로그인 성공
- [ ] 트레이딩 페이지 로드
- [ ] 봇 시작 가능
- [ ] 로그 뷰어 카드 표시
- [ ] 실시간 로그 수신 (1~2초마다)
- [ ] 일시정지/재개 작동
- [ ] 자동 스크롤 작동
- [ ] 로그 클리어 작동
- [ ] 로그 다운로드 작동
- [ ] AI 신호 로그 확인 (`🔍 Signal check`)
- [ ] 전략 로딩 로그 확인 (`Loading ... Strategy`)
- [ ] 캔들 업데이트 로그 확인 (`📡 Broadcasted`)

## 📞 문제 발생 시

1. **백엔드 로그 확인**:
   ```bash
   ssh root@158.247.245.197
   cd /root/auto-dashboard
   docker compose logs backend --tail 100
   ```

2. **봇 상태 확인**:
   - 트레이딩 페이지 상단 "AI Bot 실행 중" 표시 확인
   - 녹색 아이콘과 "실행 중" 배지 확인

3. **WebSocket 연결 확인**:
   - F12 개발자 도구 → Console
   - "WebSocket connected successfully" 메시지 확인

4. **재시작**:
   - 봇 중지 → 봇 시작
   - 페이지 새로고침
   - 로그아웃 → 다시 로그인

## 🎉 성공!

로그 뷰어가 정상 작동하면, 이제 AI가 어떤 매매 신호를 생성하는지 실시간으로 확인할 수 있습니다!

- **왜 거래가 발생하지 않는지** 명확히 알 수 있음
- **AI 전략이 어떻게 작동하는지** 투명하게 확인 가능
- **에러 발생 시 즉시 대응** 가능

Happy Trading! 📈🤖
