# 📊 차트 시그널 마커 구현 가이드

## 📌 문서 정보

| 항목 | 내용 |
|------|------|
| 작성일 | 2025-12-12 |
| 참조 소스 | FreqUI (freqtrade/frequi) |
| 적용 대상 | auto-dashboard 트레이딩 차트 |
| 목적 | 캔들 차트에 진입/청산 마커, 거래 오버레이 구현 |

---

## 🎯 구현 목표

현재 우리 차트(`TradingChart.jsx`)에 다음 기능 추가:

| 기능 | 설명 | 우선순위 |
|------|------|----------|
| 시그널 마커 | 전략 진입/청산 시그널 표시 (▲▼◆) | 🔴 HIGH |
| 거래 오버레이 | 실제 체결된 거래 마커 표시 | 🔴 HIGH |
| 스탑로스 라인 | 열린 포지션의 손절 가격 수평선 | 🟡 MEDIUM |
| 마크 영역 | 커스텀 주석 영역/라인 | 🟢 LOW |
| 타임프레임 선택 | 15m 기본값으로 변경 | 🔴 HIGH |

---

## 📐 FreqUI 아키텍처 분석

### 1. 캔들 주기(타임프레임) 선택 흐름

```
┌─────────────────────────────────────────────────────────────────┐
│                      TimeframeSelect                            │
│  드롭다운 옵션: 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h   │
│               1d, 3d, 1w, 2w, 1M, 1y                           │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      chartConfig Store                          │
│  selectedTimeframe: '1h' (기본값)                               │
│  → persistence: 로컬 스토리지에 저장                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        ChartsView                               │
│  finalTimeframe = selectedTimeframe || 전략기본 || ''            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   CandleChartContainer                          │
│  API 호출: /pair_history?timeframe={finalTimeframe}             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        CandleChart                              │
│  ECharts 렌더링                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2. 차트 렌더 파이프라인

```javascript
// CandleChartContainer → CandleChart 데이터 흐름
{
  dataset: PairHistory,      // 캔들 데이터
  trades: Trade[],           // 거래 내역  
  timeframe: '15m',          // 선택된 주기
  timeframe_ms: 900000,      // 주기 (밀리초)
}
```

---

## 🔺 시그널 마커 구현 명세

### 컬럼명 매핑 (백엔드 → 프론트엔드)

| 시그널 타입 | 컬럼명 | 대체 컬럼명 | 심볼 | 크기 | 색상 |
|------------|--------|------------|------|------|------|
| **롱 진입** | `_enter_long_signal_close` | `_buy_signal_close` | ▲ (triangle) | 10 | `#00ff26` |
| **롱 청산** | `_exit_long_signal_close` | `_sell_signal_close` | ◆ (diamond) | 8 | `#faba25` |
| **숏 진입** | `_enter_short_signal_close` | - | ▼ (triangle 180°) | 10 | `#00ff26` |
| **숏 청산** | `_exit_short_signal_close` | - | pin | 8 | `#faba25` |

### ECharts Scatter Series 구현

```javascript
// 롱 진입 시그널 시리즈
{
  type: 'scatter',
  name: 'Long Entry',
  xAxisIndex: 0,
  yAxisIndex: 0,
  symbol: 'triangle',
  symbolSize: 10,
  itemStyle: {
    color: '#00ff26',
  },
  encode: {
    x: '__date_ts',           // X축: 타임스탬프 (밀리초)
    y: '_enter_long_signal_close',  // Y축: close 가격
  },
  // 데이터가 존재할 때만 표시
  data: dataset.filter(d => d._enter_long_signal_close != null),
}

// 숏 진입 시그널 (회전 적용)
{
  type: 'scatter',
  name: 'Short Entry',
  symbol: 'triangle',
  symbolRotate: 180,  // ▼ 모양으로 회전
  symbolSize: 10,
  itemStyle: {
    color: '#00ff26',
  },
  // ...
}
```

### Tooltip 구현

```javascript
tooltip: {
  formatter: (params) => {
    const { seriesName, value, data } = params;
    const signalValue = value[1];  // Y값 (가격)
    const enterTag = data.enter_tag || '';
    const exitTag = data.exit_tag || '';
    
    let tooltip = `${seriesName}: ${signalValue.toFixed(2)}`;
    
    if (enterTag) {
      tooltip += `<br/>Tag: ${enterTag.substring(0, 100)}`;
    }
    if (exitTag) {
      tooltip += `<br/>Exit: ${exitTag.substring(0, 100)}`;
    }
    
    return tooltip;
  }
}
```

---

## 📍 거래 오버레이 구현 명세

### Trade 마커 타입

| 타입 | 심볼 | 회전 (롱) | 회전 (숏) | 색상 |
|------|------|----------|----------|------|
| **포지션 오픈** | OPEN_CLOSE_SYMBOL (커스텀) | 0° | 180° | 롱 `#0066FF` / 숏 `#AD00FF` |
| **포지션 클로즈** | OPEN_CLOSE_SYMBOL (커스텀) | 180° | 0° | 롱 `#0066FF` / 숏 `#AD00FF` |
| **증감/조정** | ADJUSTMENT_SYMBOL (커스텀) | 0° | 180° | 롱 `#0066FF` / 숏 `#AD00FF` |

### 커스텀 심볼 Path

```javascript
// 오픈/클로즈 심볼 (FreqUI에서 사용하는 커스텀 SVG path)
const OPEN_CLOSE_SYMBOL = 'path://M0,8 L8,0 L16,8 L8,16 Z';  // 마름모 형태

// 조정 심볼
const ADJUSTMENT_SYMBOL = 'path://M0,4 L4,0 L8,4 L4,8 Z';  // 작은 마름모
```

### 데이터 포맷

```javascript
// Trade scatter 데이터 구조
[
  rounded_ts,      // X축: 캔들 타임스탬프로 반올림
  price,           // Y축: 체결 가격
  symbolPath,      // 심볼 path
  rotate,          // 회전 각도
  color,           // 색상
  label,           // 라벨 텍스트 ("Long (open)" 등)
  tooltip,         // 툴팁 HTML
]
```

### Label 스타일

```javascript
label: {
  show: true,
  rotate: 75,  // 75도 회전
  formatter: '{@label}',
  backgroundColor: isDark ? '#000' : '#fff',
  color: isDark ? '#fff' : '#000',
  padding: [2, 4],
  fontSize: 10,
}
```

### Tooltip 내용

```javascript
// Trade Tooltip에 포함할 정보
{
  type: 'Long Entry' | 'Long Exit' | 'Short Entry' | 'Short Exit' | 'Adjustment',
  price: 95234.50,
  profit_pct: '+2.35%',       // 청산 시
  profit_abs: '+$47.12',      // 청산 시
  cost: '$2,000.00',          // 주문 금액
  enter_tag: 'ema_cross',     // 진입 태그
  order_tag: 'main_entry',    // 주문 태그
  exit_reason: 'take_profit', // 청산 사유
}
```

---

## 📏 스탑로스 보조선 구현

```javascript
// markLine으로 스탑로스 수평선 추가
markLine: {
  data: [
    {
      name: 'Stop Loss',
      yAxis: stopLossPrice,
      lineStyle: {
        color: '#ff0000AA',
        width: 2,
        type: 'dashed',
      },
      label: {
        formatter: 'SL: {c}',
        position: 'end',
      },
      // X 범위: 포지션 시작 ~ 데이터 끝 + 오프셋
      coord: [
        [Math.min(open_timestamp, data_end - offset), stopLossPrice],
        [close_timestamp || (data_stop_ts + timeframe_ms), stopLossPrice],
      ]
    }
  ]
}
```

---

## 🖼️ 마크 영역/라인 구현 (Optional)

### 영역 (Area)

```javascript
// annotations 배열에서 type='area' 항목 처리
markArea: {
  data: [
    [
      {
        xAxis: annotation.start,      // 시작 X
        yAxis: annotation.y_start,    // 시작 Y
        itemStyle: { color: annotation.color },
        label: { 
          show: true, 
          position: 'insideTop',
          formatter: annotation.label,
        },
      },
      {
        xAxis: annotation.end,        // 끝 X
        yAxis: annotation.y_end,      // 끝 Y
      }
    ]
  ]
}
```

### 라인 (Line)

```javascript
// annotations 배열에서 type='line' 항목 처리
markLine: {
  data: [
    {
      name: annotation.label,
      lineStyle: {
        color: annotation.color,
        width: annotation.width || 1,
        type: annotation.line_style || 'solid',  // solid/dashed/dotted
      },
      coord: [
        [annotation.start, annotation.y_start],
        [annotation.end, annotation.y_end],
      ]
    }
  ]
}
```

---

## ✅ 체크리스트: 우리 프로젝트 적용

### Phase 1: 데이터 파이프라인 (백엔드)

| 순번 | 작업 | 상태 | 설명 |
|------|------|------|------|
| 1.1 | [x] 시그널 컬럼 추가 | ✅ 완료 | `DynamicStrategyExecutor`에서 `enter_tag` 생성, `bot_runner`에서 저장 |
| 1.2 | [x] `timeframe_ms` 필드 추가 | ✅ 완료 | Candle API 응답에 주기(밀리초) 포함 |
| 1.3 | [x] Trade 데이터 포맷 변경 | ✅ 완료 | `enter_tag`, `exit_tag`, `order_tag` 필드 추가 (DB + API) |
| 1.4 | [ ] Annotations API 구현 | 대기 | 마크 영역/라인 정의 엔드포인트 (Optional) |

### Phase 2: 차트 컴포넌트 (프론트엔드)

| 순번 | 작업 | 상태 | 설명 |
|------|------|------|------|
| 2.1 | [x] 타임프레임 15m 고정 | ✅ 완료 | 타임프레임 선택 UI 제거, 15m 고정 |
| 2.2 | [x] 시그널 마커 시리즈 추가 | ✅ 완료 | FreqUI 스타일 마커 (롱/숏 진입/청산) |
| 2.3 | [x] 거래 오버레이 시리즈 추가 | ✅ 완료 | Trade 마커 + PnL 표시 + exit_reason |
| 2.4 | [x] 스탑로스/익절 라인 추가 | ✅ 완료 | SL/TP/LIQ 수평선 (열린 포지션) |
| 2.5 | [x] 마커 토글 추가 | ✅ 완료 | Switch로 마커 표시 여부 제어 |
| 2.6 | [ ] 데이터 줌 여유 공간 | 대기 | 우측에 `timeframe_ms * 5` 빈 공간 |

### Phase 3: 스타일 및 UX

| 순번 | 작업 | 상태 | 설명 |
|------|------|------|------|
| 3.1 | [ ] 다크/라이트 테마 대응 | 대기 | 라벨 배경색 동적 변경 |
| 3.2 | [x] Legend 정리 | ✅ 완료 | 마커/포지션 범례 추가 (좌하단/우하단) |
| 3.3 | [x] PnL 포맷팅 | ✅ 완료 | 수익률, 청산 사유 표시 |
| 3.4 | [x] 반응형 심볼 크기 | ✅ 완료 | 모바일에서 심볼/텍스트 크기 조정 |

---

## 📁 수정 대상 파일

### 백엔드

```
backend/src/
├── services/
│   ├── chart_data_service.py    # 시그널 컬럼 추가
│   └── strategy_engine.py       # 시그널 생성 로직
├── api/
│   └── chart.py                 # timeframe_ms 필드 추가
└── database/
    └── models.py                # Trade 모델 필드 추가
```

### 프론트엔드

```
frontend/src/
├── pages/
│   └── Trading.jsx              # 타임프레임 기본값
├── components/
│   ├── TradingChart.jsx         # 차트 메인 컴포넌트
│   └── chart/
│       ├── SignalMarkers.jsx    # [NEW] 시그널 마커 로직
│       ├── TradeOverlay.jsx     # [NEW] 거래 오버레이 로직
│       └── StopLossLine.jsx     # [NEW] 스탑로스 라인 로직
└── utils/
    └── chartHelpers.js          # [NEW] 차트 유틸 함수
```

---

## 🔧 구현 예시 코드 (TradingChart.jsx)

```jsx
// 시그널 마커 시리즈 생성 함수
const generateSignalSeries = (dataset, columns) => {
  const series = [];
  
  // 롱 진입 시그널
  const longEntryCol = columns.find(c => 
    c === '_enter_long_signal_close' || c === '_buy_signal_close'
  );
  if (longEntryCol) {
    series.push({
      type: 'scatter',
      name: 'Long Entry',
      symbol: 'triangle',
      symbolSize: 10,
      itemStyle: { color: '#00ff26' },
      data: dataset
        .filter(d => d[longEntryCol] != null)
        .map(d => [d.timestamp, d[longEntryCol]]),
    });
  }
  
  // 숏 진입 시그널
  const shortEntryCol = columns.find(c => c === '_enter_short_signal_close');
  if (shortEntryCol) {
    series.push({
      type: 'scatter',
      name: 'Short Entry',
      symbol: 'triangle',
      symbolRotate: 180,
      symbolSize: 10,
      itemStyle: { color: '#00ff26' },
      data: dataset
        .filter(d => d[shortEntryCol] != null)
        .map(d => [d.timestamp, d[shortEntryCol]]),
    });
  }
  
  // ... 롱/숏 청산도 동일하게 처리
  
  return series;
};

// 차트 옵션에 시그널 시리즈 추가
const chartOption = useMemo(() => {
  const signalSeries = generateSignalSeries(candleData, dataColumns);
  const tradeSeries = generateTradeSeries(trades, timeframe_ms);
  
  return {
    // ... 기존 옵션
    series: [
      ...candleSeries,
      ...volumeSeries,
      ...signalSeries,
      ...tradeSeries,
    ],
  };
}, [candleData, trades, timeframe_ms]);
```

---

## ⚠️ 주의사항

### 타임스탬프 라운딩

```javascript
// Trade 타임스탬프를 캔들 주기에 맞게 라운딩
const roundToTimeframe = (timestamp, timeframe_ms) => {
  return Math.floor(timestamp / timeframe_ms) * timeframe_ms;
};
```

### 필수 데이터 필드

- `timeframe_ms`: 반드시 백엔드에서 전달 (15분 = 900000ms)
- `__date_ts`: 밀리초 타임스탬프
- `enter_tag` / `exit_tag`: 시그널 태그 (Optional but recommended)

### 성능 최적화

- 대량 데이터 시 `large: true` 옵션 사용
- 시그널 필터링은 데이터 로드 시 1회만 수행
- 줌/패닝 시 재계산 피하기

---

## 📚 참조 문서

- FreqUI 소스: <https://github.com/freqtrade/frequi>
- ECharts Scatter: <https://echarts.apache.org/en/option.html#series-scatter>
- ECharts MarkLine: <https://echarts.apache.org/en/option.html#series-line.markLine>

---

**작성자**: Claude (AI Assistant)  
**작성일**: 2025-12-12  
**다음 작업**: Phase 1 - 백엔드 시그널 컬럼 구현
