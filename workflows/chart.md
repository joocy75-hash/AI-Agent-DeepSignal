---
description: 차트 개발 - 시그널 마커 및 거래 오버레이 구현
---

# 📊 차트 개발 워크플로우

## 📋 사전 준비

### 1. 차트 가이드 읽기

// turbo

- `docs/CHART_SIGNAL_MARKERS_GUIDE.md` 읽기

### 2. 현재 차트 구현 확인

- `frontend/src/components/TradingChart.jsx`

## 🛠️ 개발 단계

### Step 1: 시그널 마커 구현

**백엔드**: 시그널 컬럼 추가

```python
# 전략 엔진에서 시그널 컬럼 생성
_enter_long_signal_close  # 롱 진입 가격
_exit_long_signal_close   # 롱 청산 가격
_enter_short_signal_close # 숏 진입 가격
_exit_short_signal_close  # 숏 청산 가격
```

**프론트엔드**: Scatter 시리즈 추가

```jsx
// 롱 진입 마커
{
  type: 'scatter',
  name: 'Long Entry',
  symbol: 'triangle',
  symbolSize: 10,
  itemStyle: { color: '#00ff26' },
}
```

### Step 2: 거래 오버레이 구현

**데이터 구조**:

```javascript
{
  timestamp: number,
  price: number,
  type: 'entry' | 'exit' | 'adjustment',
  side: 'long' | 'short',
  profit_pct: number,  // 청산 시
}
```

**마커 스타일**:

- 롱: `#0066FF` (파란색)
- 숏: `#AD00FF` (보라색)

### Step 3: 스탑로스 라인 추가

```jsx
markLine: {
  data: [{
    yAxis: stopLossPrice,
    lineStyle: { color: '#ff0000AA', type: 'dashed' },
    label: { formatter: 'SL: {c}' },
  }]
}
```

### Step 4: 타임프레임 변경

기본값 변경: `1h` → `15m`

```jsx
const [timeframe, setTimeframe] = useState('15m');
```

## ✅ 완료 체크리스트

- [ ] 시그널 컬럼 백엔드 구현
- [ ] 시그널 마커 프론트엔드 구현
- [ ] 거래 오버레이 구현
- [ ] 스탑로스 라인 구현
- [ ] 타임프레임 기본값 변경
- [ ] Tooltip 구현
- [ ] Legend 추가
