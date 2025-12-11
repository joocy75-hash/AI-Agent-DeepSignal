프론트엔드 차트 분석 (캔들 주기·진입 마크 구현)
========================================================

1) 캔들 주기(타임프레임) 선택 흐름

- 기본값: `chartConfig` 스토어의 `selectedTimeframe` 초기값이 `1h` (src/stores/chartConfig.ts).
- 선택 목록: TimeframeSelect 컴포넌트가 제공하는 옵션은 아래 순서로 고정됨 (src/components/ftbot/TimeframeSelect.vue).
  - 공백(전략 기본값 사용), 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 2w, 1M, 1y
- 적용 방식:
  - ChartsView에서 `finalTimeframe`을 계산: 웹서버 모드면 `selectedTimeframe` → 없으면 전략 기본 timeframe → 빈 값. 로컬/비웹서버 모드면 봇의 `timeframe` 사용 (src/views/ChartsView.vue).
  - CandleChartContainer는 `:timeframe="finalTimeframe"`을 받아 PairHistory/PairsCandles API 호출 시 payload의 `timeframe`으로 전달 (same file의 `refreshOHLCV`, `refresh` 로직).
  - 받아온 PairHistory 구조체에 `timeframe`과 `timeframe_ms`가 함께 내려와 X축과 데이터 가공에 사용됨 (src/types/candleTypes.ts).

2) 차트 렌더 파이프라인 요약

- CandleChartContainer가 현재 선택 페어/타임프레임에 맞는 PairHistory와 Trade 배열을 CandleChart로 전달.
- CandleChart는 받은 dataset 컬럼을 파싱해 캔들/거래량/인디케이터/시그널 시리즈를 구성하고 `vue-echarts`로 렌더 (src/components/charts/CandleChart.vue).
- 데이터 확대/축소: dataZoom inside + bar(슬라이더) 2개를 모든 xAxis에 바인딩하며, 초기 표시는 `start_candle_count`(기본 250개 캔들) 기준으로 오른쪽 끝 250+2개만 보이도록 start 퍼센트를 계산.
- 스크롤 패스: 마지막 캔들 뒤로 timeframe_ms * 5 만큼 빈 row를 추가해 우측으로 약간 스크롤 여유를 둠.
- Heikin Ashi 토글은 dataset을 변환한 뒤 동일 파이프라인으로 그려짐 (`heikinAshiDataset`).

3) 시그널 마커(전략 진입/청산 시그널)

- CandleChart에서 dataset 컬럼을 검색해 시그널용 scatter series 4종을 추가함 (src/components/charts/CandleChart.vue).
  - 롱 진입: 컬럼 `_buy_signal_close` 또는 `_enter_long_signal_close`, 심볼 ▲(triangle), 크기 10, 색 `#00ff26`, tooltip prefix `Long entry`.
  - 롱 청산: 컬럼 `_sell_signal_close` 또는 `_exit_long_signal_close`, 심볼 ◆(diamond), 크기 8, 색 `#faba25`, tooltip prefix `Long exit`.
  - 숏 진입: 컬럼 `_enter_short_signal_close`, 심볼 ▼(triangle 회전 180°), 크기 10, 색 `#00ff26`, tooltip prefix `Short entry`.
  - 숏 청산: 컬럼 `_exit_short_signal_close`, 심볼 pin, 크기 8, 색 `#faba25`, tooltip prefix `Short exit`.
- 위치 매핑: x축은 `__date_ts` 컬럼(밀리초 타임스탬프), y축은 각 시그널 컬럼의 값(대개 close 가격). 존재 여부(`colData >= 0`)에 따라 시리즈를 조건부 생성.
- Tooltip 구성: enter_tag/exit_tag 컬럼을 함께 encode하여 시그널 값과 태그를 최대 100자까지 병기. 태그가 없으면 값만 표시.
- Legend: 기본 legend 데이터에 Entry/Exit를 포함하고, trades 시리즈 삽입 전에 legend 배열에 Trades를 끼워 넣음.

4) 실거래/주문 마커(트레이드 오버레이)

- Trade 배열과 PairHistory를 기반으로 `generateTradeSeries`가 별도 scatter 시리즈를 생성 (src/utils/charts/tradeChartData.ts).
- 심볼 정의:
  - 최초 주문(포지션 오픈)과 마지막 주문(포지션 클로즈)은 OPEN_CLOSE_SYMBOL 커스텀 path 사용. 롱은 0°, 숏은 180°(오픈), 클로즈는 롱 180°/숏 0° 회전.
  - 중간 주문(증감/조정)은 ADJUSTMENT_SYMBOL path를 사용, 롱 0°/숏 180° 회전. 미체결 스탑로스는 시각화 제외.
- 색상: 롱 `#0066FF`, 숏 `#AD00FF`. itemStyle에서 데이터별 색을 적용.
- 데이터 포맷: `[rounded_ts, price, symbolPath, rotate, color, label, tooltip]` 형태로 scatter encode.
  - label에는 “Long/Short (open)” 또는 “profit%” 등을 표시, 차트에 75° 회전 텍스트로 노출. 배경색은 테마별 흑/백.
  - tooltip에는 진입/청산/조정 여부, 수익률, 절대 수익, 주문 금액(+/- cost), enter_tag, order_tag, exit_reason 등을 모두 포함.
- Stoploss 보조선: 열려있는 포지션이 있으면 markLine으로 스탑로스 수평선 추가. 시작 x는 open_timestamp 또는 데이터 끝-오프셋 중 더 이른 값, 끝 x는 close_timestamp 또는 data_stop_ts+timeframe_ms. 색 `#ff0000AA`.

5) 마크 영역/라인(annotations)

- PairHistory.annotations에 영역/라인 정의가 있으면 `generateMarkAreaSeries`가 눈에 보이지 않는 scatter 시리즈를 추가하고 markArea/markLine을 부착 (src/utils/charts/tradeChartData.ts).
- 영역(type=area): start/end, y_start/y_end, color, label, z_index를 사용해 직사각형을 채움. 라벨은 insideTop.
- 라인(type=line): start/end, y_start/y_end, color, width, line_style(solid/dashed/dotted), z_index를 반영한 markLine 생성.
- 마크 영역 표시 여부는 설정 `showMarkArea`로 토글 (CandleChartContainer에서 BaseCheckbox로 제어).

6) 기타 렌더 설정 포인트

- X축은 time 타입 2개(메인, 거래량), Y축은 가격/거래량 + 서브플롯별로 동적 추가. 레이블 위치는 설정의 좌/우(labelSide)로 결정.
- 데이터 줌 슬라이더는 모든 xAxisIndex에 공유해 서브플롯과 동기화. 초기 start/end는 데이터 로드 후 재계산하여 차트 재설정 방지.
- 색상: 양봉/음봉 색은 테마 스토어의 colorUp/colorDown을 주입. 시그널은 고정된 녹색/노란색.

재사용 시 체크 포인트

- 동일한 시그널/주문 표시를 다른 플랫폼에 옮길 때는 위 시그널 컬럼명과 데이터 포맷을 그대로 매칭해야 동일한 모양과 회전에 맞출 수 있음.
- PairHistory 구조체의 timeframe_ms가 시그널/주문 TS 라운딩과 stoploss 보조선 오프셋 계산에 직접 사용되므로, 주기 단위(ms) 전달을 잊지 말 것.
- Enter/Exit 태그 툴팁은 배열 형태로 encode되므로, 데이터 소스에서 enter_tag/exit_tag를 빠짐없이 포함해야 UI가 의도대로 동작함.

1h → 15m 세팅 가이드 (동일 구현 재현용)

- 기본 선택 주기를 15분봉으로 바꾸려면 `src/stores/chartConfig.ts`에서 `selectedTimeframe` 초기값을 `'1h'` → `'15m'`로 수정한다. 스토어는 최초 로드 시 기본값을 사용하고, 이후 사용자가 바꾼 값은 persistence(`ftUIChartSettings`)에 저장된다.
- Timeframe 드롭다운은 이미 `15m` 옵션을 포함한다(`src/components/ftbot/TimeframeSelect.vue`), 추가 작업 없이 선택 가능.
- 웹서버 모드 동작 확인: `src/views/ChartsView.vue`에서 `finalTimeframe`은 `chartStore.selectedTimeframe || 전략 기본 || ''` 순서로 결정되므로, 기본값만 15m로 바꿔도 차트 요청 payload의 timeframe이 15m로 내려간다.
- 로컬/비웹서버 모드: 봇 객체의 `timeframe`을 그대로 쓴다. 여기서도 기본을 15m로 두려면 봇 생성 시 `timeframe: '15m'` 설정을 맞춰준다(백엔드 설정 영역).
- 동작 검증: 차트 헤더에 표기되는 `{{ strategyName }} | {{ timeframe || '' }}`가 15m로 바뀌는지 확인하고, PairHistory 응답의 `timeframe_ms`가 900000(15분)으로 오는지 콘솔/네트워크 탭에서 확인하면 된다.
