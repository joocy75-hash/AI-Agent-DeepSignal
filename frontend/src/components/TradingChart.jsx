import { useEffect, useRef, useState, memo } from 'react';
import { createChart } from 'lightweight-charts';
import { Modal, Input, Switch, Space, Typography, Button, ColorPicker, InputNumber } from 'antd';
import { SearchOutlined, DownOutlined, DeleteOutlined } from '@ant-design/icons';

const { Text } = Typography;

// 환율 설정 (1 USD = 1,460 KRW)
const USD_KRW_RATE = 1460;

// 코인 정보 (아이콘, 색상)
const COIN_DATA = {
  btc: { name: 'Bitcoin', symbol: '₿', color: '#F7931A', gradient: 'linear-gradient(135deg, #F7931A 0%, #FFAB40 100%)' },
  eth: { name: 'Ethereum', symbol: 'Ξ', color: '#627EEA', gradient: 'linear-gradient(135deg, #627EEA 0%, #8C9EFF 100%)' },
  bnb: { name: 'BNB', symbol: 'B', color: '#F3BA2F', gradient: 'linear-gradient(135deg, #F3BA2F 0%, #FFD54F 100%)' },
  sol: { name: 'Solana', symbol: 'S', color: '#9945FF', gradient: 'linear-gradient(135deg, #9945FF 0%, #14F195 100%)' },
  ada: { name: 'Cardano', symbol: 'A', color: '#0033AD', gradient: 'linear-gradient(135deg, #0033AD 0%, #3F51B5 100%)' },
  xrp: { name: 'XRP', symbol: 'X', color: '#23292F', gradient: 'linear-gradient(135deg, #23292F 0%, #607D8B 100%)' },
  doge: { name: 'Dogecoin', symbol: 'Ð', color: '#C2A633', gradient: 'linear-gradient(135deg, #C2A633 0%, #FFE082 100%)' },
};

const formatPrice = (value) => {
  if (value === undefined || value === null) return '-';
  return Math.round(Number(value)).toLocaleString('en-US');
};

const formatPriceShort = (value) => {
  if (value === undefined || value === null) return '-';
  const num = Number(value);
  if (num >= 1000) {
    return (num / 1000).toFixed(1) + 'K';
  }
  return num.toLocaleString('en-US');
};

const formatKRW = (value) => {
  if (value === undefined || value === null) return '₩0';
  const krwPrice = Number(value) * USD_KRW_RATE;
  if (krwPrice >= 1000000) {
    return '₩' + (krwPrice / 10000).toFixed(0) + '만';
  }
  return '₩' + Math.round(krwPrice).toLocaleString('ko-KR');
};

// Custom hook for responsive detection
const useIsMobile = () => {
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return isMobile;
};

function TradingChart({
  data = [],
  symbol = 'BTC/USDT',
  height = 500,
  timeframe = '15m',  // 15m 고정
  availableSymbols = [],
  onSymbolChange,
  positions = [],
  tradeMarkers = [],
  annotations = [],  // 차트 어노테이션 (수평선, 메모 등)
  onAnnotationAdd,   // 어노테이션 추가 콜백
  onAnnotationDelete, // 어노테이션 삭제 콜백
  onAnnotationEdit,   // 어노테이션 편집 콜백
  onAnnotationResetAlert, // 가격 알림 리셋 콜백
}) {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candlestickSeriesRef = useRef(null);
  const [coinModalOpen, setCoinModalOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [showMarkers, setShowMarkers] = useState(true);
  const [showAnnotations, setShowAnnotations] = useState(true);
  const [contextMenu, setContextMenu] = useState({ visible: false, x: 0, y: 0, price: null, nearbyAnnotation: null });
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [editingAnnotation, setEditingAnnotation] = useState(null);
  const isMobile = useIsMobile();

  // Initialize chart once
  useEffect(() => {
    if (!chartContainerRef.current) return;

    const container = chartContainerRef.current;
    const chartWidth = container.clientWidth;

    if (chartWidth === 0) {
      return;
    }

    // Create chart
    const chart = createChart(container, {
      width: chartWidth,
      height: height || 600,
      layout: {
        background: { type: 'solid', color: '#ffffff' },
        textColor: '#4b5563',
        fontSize: isMobile ? 10 : 12,
      },
      grid: {
        vertLines: { color: '#eceff3' },
        horzLines: { color: '#eceff3' },
      },
      rightPriceScale: {
        borderColor: '#e5e7eb',
        autoScale: true,
        scaleMargins: {
          top: 0.1,
          bottom: 0.1,
        },
      },
      timeScale: {
        borderColor: '#e5e7eb',
        timeVisible: true,
        rightOffset: isMobile ? 5 : 12,
        barSpacing: isMobile ? 6 : 8,
      },
    });

    // Add candlestick series
    const candlestickSeries = chart.addCandlestickSeries({
      upColor: '#0ecb81',
      downColor: '#f6465d',
      borderVisible: false,
      wickUpColor: '#0ecb81',
      wickDownColor: '#f6465d',
    });

    chartRef.current = chart;
    candlestickSeriesRef.current = candlestickSeries;


    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current && chartRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      if (chartRef.current) {
        chart.remove();
      }
      chartRef.current = null;
      candlestickSeriesRef.current = null;
    };
  }, [height, isMobile]);

  // Update data and markers when they change
  useEffect(() => {
    if (!candlestickSeriesRef.current || !data || data.length === 0) {
      return;
    }

    const candleData = data
      .filter(c => c.time && c.open && c.high && c.low && c.close)
      .map(c => ({
        time: c.time,
        open: parseFloat(c.open),
        high: parseFloat(c.high),
        low: parseFloat(c.low),
        close: parseFloat(c.close),
      }))
      .sort((a, b) => a.time - b.time);

    if (candleData.length === 0) {
      return;
    }

    candlestickSeriesRef.current.setData(candleData);

    // Update markers if enabled
    if (showMarkers && tradeMarkers && tradeMarkers.length > 0) {
      const chartMarkers = createChartMarkers(tradeMarkers, candleData);
      if (chartMarkers.length > 0) {
        candlestickSeriesRef.current.setMarkers(chartMarkers);
        console.log('[TradingChart] Added', chartMarkers.length, 'markers');
      }
    } else {
      candlestickSeriesRef.current.setMarkers([]);
    }

    if (chartRef.current) {
      setTimeout(() => {
        chartRef.current?.timeScale().fitContent();
      }, 100);
    }

    console.log('[TradingChart] Data updated successfully');
  }, [data, tradeMarkers, showMarkers]);

  // FreqUI 스타일 마커 색상 (CHART_SIGNAL_MARKERS_GUIDE.md 참조)
  const MARKER_COLORS = {
    entryLong: '#00ff26',   // 롱 진입 - 밝은 녹색
    entryShort: '#00ff26',  // 숏 진입 - 밝은 녹색 (방향은 화살표로 구분)
    exitLong: '#faba25',    // 롱 청산 - 황금색
    exitShort: '#faba25',   // 숏 청산 - 황금색
    profitExit: '#00d26a',  // 익절 청산
    lossExit: '#ff4757',    // 손절 청산
  };

  // Create chart markers from trade data
  const createChartMarkers = (markers, candleData) => {
    if (!markers || markers.length === 0 || !candleData || candleData.length === 0) {
      return [];
    }

    // Get time range of candle data
    const minTime = candleData[0].time;
    const maxTime = candleData[candleData.length - 1].time;

    // Convert trade markers to lightweight-charts format
    const chartMarkers = markers
      .filter(m => m.timestamp >= minTime && m.timestamp <= maxTime)
      .map(marker => {
        // Find the closest candle time
        const closestCandle = candleData.reduce((prev, curr) => {
          return Math.abs(curr.time - marker.timestamp) < Math.abs(prev.time - marker.timestamp) ? curr : prev;
        });

        if (marker.type === 'entry') {
          // Entry markers - FreqUI 스타일
          if (marker.side === 'long') {
            return {
              time: closestCandle.time,
              position: 'belowBar',
              color: MARKER_COLORS.entryLong,
              shape: 'arrowUp',
              text: isMobile ? 'L' : `▲ Long ${formatPriceShort(marker.price)}`,
              size: isMobile ? 1 : 2,
            };
          } else {
            return {
              time: closestCandle.time,
              position: 'aboveBar',
              color: MARKER_COLORS.entryShort,
              shape: 'arrowDown',
              text: isMobile ? 'S' : `▼ Short ${formatPriceShort(marker.price)}`,
              size: isMobile ? 1 : 2,
            };
          }
        } else if (marker.type === 'exit') {
          // Exit markers with P&L indicator
          const pnl = marker.pnl || 0;
          const pnlText = pnl >= 0
            ? `+${pnl.toFixed(isMobile ? 0 : 2)}`
            : pnl.toFixed(isMobile ? 0 : 2);
          // 수익/손실에 따른 색상 (청산은 결과 기반)
          const exitColor = pnl >= 0 ? MARKER_COLORS.profitExit : MARKER_COLORS.lossExit;
          // 청산 사유 표시
          const exitReason = marker.exit_reason || '';
          const reasonText = exitReason ? ` (${exitReason})` : '';

          return {
            time: closestCandle.time,
            position: marker.side === 'long' ? 'aboveBar' : 'belowBar',
            color: exitColor,
            shape: 'square',
            text: isMobile ? `${pnl >= 0 ? '+' : ''}${pnl.toFixed(0)}` : `◆ ${pnlText}${reasonText}`,
            size: isMobile ? 1 : 2,
          };
        } else if (marker.type === 'signal') {
          // 전략 시그널 마커 (아직 체결되지 않은 시그널)
          const isLong = marker.signal === 'long' || marker.signal === 'buy';
          return {
            time: closestCandle.time,
            position: isLong ? 'belowBar' : 'aboveBar',
            color: '#5c7cfa',  // 시그널은 파란색
            shape: isLong ? 'arrowUp' : 'arrowDown',
            text: isMobile ? '!' : `Signal: ${marker.signal}`,
            size: isMobile ? 0.5 : 1,
          };
        }
        return null;
      })
      .filter(m => m !== null)
      .sort((a, b) => a.time - b.time);

    return chartMarkers;
  };

  // Add annotation lines on chart (수평선, 가격 레벨 등)
  useEffect(() => {
    if (!chartRef.current || !candlestickSeriesRef.current || !annotations || annotations.length === 0 || !showAnnotations) {
      return;
    }

    const annotationLines = [];

    // 활성화된 어노테이션만 표시
    const activeAnnotations = annotations.filter(a => a.is_active);

    activeAnnotations.forEach(annotation => {
      try {
        // 수평선 타입 (hline, price_level)
        if ((annotation.annotation_type === 'hline' || annotation.annotation_type === 'price_level') && annotation.price) {
          const style = annotation.style || {};
          const lineStyle = style.lineDash ? 2 : 0; // 점선 여부

          const priceLine = candlestickSeriesRef.current.createPriceLine({
            price: parseFloat(annotation.price),
            color: style.color || '#1890ff',
            lineWidth: style.lineWidth || 1,
            lineStyle: lineStyle,
            axisLabelVisible: true,
            title: isMobile
              ? (annotation.label || '')
              : (annotation.label || `$${formatPrice(annotation.price)}`),
          });
          annotationLines.push(priceLine);
        }
      } catch (e) {
        console.warn('[TradingChart] Failed to create annotation line:', e);
      }
    });

    // Cleanup
    return () => {
      annotationLines.forEach(line => {
        try {
          candlestickSeriesRef.current?.removePriceLine(line);
        } catch (e) {
          // 이미 제거된 경우 무시
        }
      });
    };
  }, [annotations, data, isMobile, showAnnotations]);

  // Add position lines on chart (진입가 + 스탑로스 + 익절가)
  useEffect(() => {
    if (!chartRef.current || !candlestickSeriesRef.current || !positions || positions.length === 0) {
      return;
    }

    const priceLines = [];

    // Create price lines for open positions
    positions.forEach(pos => {
      try {
        // 1. 진입가 라인 (실선)
        const entryLine = candlestickSeriesRef.current.createPriceLine({
          price: pos.entry_price,
          color: pos.side === 'long' ? '#0ecb81' : '#f6465d',
          lineWidth: 2,
          lineStyle: 0, // Solid
          axisLabelVisible: true,
          title: isMobile
            ? `${pos.side === 'long' ? 'L' : 'S'}`
            : `${pos.side.toUpperCase()} @ ${formatPrice(pos.entry_price)}`,
        });
        priceLines.push(entryLine);

        // 2. 스탑로스 라인 (점선, 빨간색)
        if (pos.stop_loss) {
          const slLine = candlestickSeriesRef.current.createPriceLine({
            price: pos.stop_loss,
            color: '#ff4757',
            lineWidth: 1,
            lineStyle: 2, // Dashed
            axisLabelVisible: true,
            title: isMobile ? 'SL' : `SL ${formatPrice(pos.stop_loss)}`,
          });
          priceLines.push(slLine);
        }

        // 3. 익절가 라인 (점선, 녹색)
        if (pos.take_profit) {
          const tpLine = candlestickSeriesRef.current.createPriceLine({
            price: pos.take_profit,
            color: '#00d26a',
            lineWidth: 1,
            lineStyle: 2, // Dashed
            axisLabelVisible: true,
            title: isMobile ? 'TP' : `TP ${formatPrice(pos.take_profit)}`,
          });
          priceLines.push(tpLine);
        }

        // 4. 청산가 라인 (강제 청산 가격, 주황색 점선)
        if (pos.liquidation_price) {
          const liqLine = candlestickSeriesRef.current.createPriceLine({
            price: pos.liquidation_price,
            color: '#ff6b35',
            lineWidth: 1,
            lineStyle: 3, // Dotted
            axisLabelVisible: true,
            title: isMobile ? 'LIQ' : `LIQ ${formatPrice(pos.liquidation_price)}`,
          });
          priceLines.push(liqLine);
        }
      } catch (e) {
        console.warn('[TradingChart] Failed to create price line:', e);
      }
    });

    // Cleanup - 모든 라인 제거
    return () => {
      priceLines.forEach(line => {
        try {
          candlestickSeriesRef.current?.removePriceLine(line);
        } catch (e) {
          // 이미 제거된 경우 무시
        }
      });
    };
  }, [positions, data, isMobile]);

  const latestCandle = data && data.length > 0 ? data[data.length - 1] : null;
  const firstCandle = data && data.length > 0 ? data[0] : null;
  const changePercent = latestCandle && firstCandle
    ? (((latestCandle.close - firstCandle.open) / firstCandle.open) * 100).toFixed(2)
    : 0;

  // 코인 ID 추출
  const coinId = symbol.replace('/USDT', '').replace('USDT', '').toLowerCase();
  const coinInfo = COIN_DATA[coinId] || { name: coinId.toUpperCase(), symbol: coinId.charAt(0).toUpperCase(), color: '#1890ff', gradient: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)' };

  // 필터링된 심볼 목록
  const filteredSymbols = availableSymbols.filter(sym =>
    sym.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCoinSelect = (newSymbol) => {
    if (onSymbolChange) {
      onSymbolChange(newSymbol);
    }
    setCoinModalOpen(false);
    setSearchTerm('');
  };

  // 타임프레임 15m 고정 - 라벨 표시용
  const timeframeLabel = isMobile ? timeframe : (timeframe === '15m' ? '15분' : timeframe);

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      {/* Combined Header: Coin Info + Timeframe + Price */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: isMobile ? '8px' : '16px',
        padding: isMobile ? '10px 12px' : '14px 16px',
        border: '1px solid #e5e7eb',
        borderRadius: '12px 12px 0 0',
        background: '#ffffff',
        flexWrap: 'wrap',
      }}>
        {/* Left: Coin Selector */}
        <div
          onClick={() => setCoinModalOpen(true)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: isMobile ? '8px' : '12px',
            cursor: 'pointer',
            padding: isMobile ? '4px 8px 4px 4px' : '6px 12px 6px 6px',
            borderRadius: '10px',
            transition: 'all 0.2s ease',
            background: 'transparent',
            flex: isMobile ? '0 0 auto' : 'none',
          }}
          onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f7'}
          onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
        >
          {/* Coin Icon */}
          <div style={{
            width: isMobile ? '32px' : '40px',
            height: isMobile ? '32px' : '40px',
            borderRadius: '50%',
            background: coinInfo.gradient,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: isMobile ? '16px' : '20px',
            fontWeight: '700',
            color: '#fff',
            boxShadow: `0 4px 12px ${coinInfo.color}40`,
          }}>
            {coinInfo.symbol}
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: isMobile ? '4px' : '8px' }}>
              <span style={{
                fontSize: isMobile ? '14px' : '18px',
                fontWeight: '700',
                color: '#111827',
                letterSpacing: '-0.02em',
              }}>
                {symbol.replace('/USDT', '').replace('USDT', '')}
              </span>
              {!isMobile && (
                <span style={{
                  fontSize: '12px',
                  color: '#9ca3af',
                  background: '#f3f4f6',
                  padding: '2px 6px',
                  borderRadius: '4px',
                }}>Perpetual</span>
              )}
              <DownOutlined style={{ fontSize: isMobile ? '8px' : '10px', color: '#9ca3af' }} />
            </div>
            {!isMobile && (
              <div style={{ fontSize: '11px', color: '#9ca3af' }}>
                {coinInfo.name} · Bitget
              </div>
            )}
          </div>
        </div>

        {/* Price Info - Simplified for Mobile */}
        {latestCandle && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: isMobile ? '8px' : '12px',
            flex: isMobile ? '1' : 'none',
            justifyContent: isMobile ? 'flex-end' : 'flex-start',
          }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{
                fontWeight: '800',
                color: parseFloat(changePercent) >= 0 ? '#059669' : '#dc2626',
                fontSize: isMobile ? '16px' : '22px',
                lineHeight: 1.1,
                letterSpacing: '-0.02em',
              }}>
                ${formatPrice(latestCandle.close)}
              </div>
              {!isMobile && (
                <div style={{
                  fontSize: '12px',
                  color: '#9ca3af',
                  marginTop: '2px',
                }}>
                  {formatKRW(latestCandle.close)}
                </div>
              )}
            </div>
            <div style={{
              padding: isMobile ? '4px 8px' : '6px 12px',
              borderRadius: '8px',
              background: parseFloat(changePercent) >= 0 ? '#dcfce7' : '#fee2e2',
              color: parseFloat(changePercent) >= 0 ? '#059669' : '#dc2626',
              fontWeight: '700',
              fontSize: isMobile ? '12px' : '14px',
            }}>
              {parseFloat(changePercent) >= 0 ? '+' : ''}{changePercent}%
            </div>
          </div>
        )}

        {/* OHLC - Hidden on Mobile */}
        {!isMobile && latestCandle && (
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '4px',
            fontSize: '12px',
            color: '#6b7280',
            borderLeft: '1px solid #e5e7eb',
            paddingLeft: '16px',
          }}>
            <span>O <b style={{ color: '#111827' }}>{formatPrice(latestCandle.open)}</b></span>
            <span>H <b style={{ color: '#059669' }}>{formatPrice(latestCandle.high)}</b></span>
            <span>L <b style={{ color: '#dc2626' }}>{formatPrice(latestCandle.low)}</b></span>
            <span>C <b style={{ color: '#111827' }}>{formatPrice(latestCandle.close)}</b></span>
          </div>
        )}
      </div>

      {/* Second Row: Timeframe (Fixed 15m) + Marker Toggle */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '8px',
        padding: isMobile ? '8px 12px' : '10px 16px',
        borderLeft: '1px solid #e5e7eb',
        borderRight: '1px solid #e5e7eb',
        background: '#fafafa',
      }}>
        {/* Timeframe Fixed Label */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
        }}>
          <div style={{
            padding: isMobile ? '6px 12px' : '8px 16px',
            borderRadius: isMobile ? '6px' : '8px',
            background: '#111827',
            color: '#ffffff',
            fontWeight: 600,
            fontSize: isMobile ? '11px' : '13px',
          }}>
            {timeframeLabel}
          </div>
          <span style={{
            fontSize: isMobile ? '10px' : '11px',
            color: '#9ca3af',
          }}>
            고정
          </span>
        </div>

        {/* Marker & Annotation Toggles */}
        <Space size={isMobile ? 8 : 16} style={{ flexShrink: 0 }}>
          {/* Marker Toggle */}
          <Space size={4}>
            <Switch
              size="small"
              checked={showMarkers}
              onChange={setShowMarkers}
              style={{ background: showMarkers ? '#0ecb81' : undefined }}
            />
            {!isMobile && (
              <Text style={{ fontSize: '11px', color: '#6b7280' }}>
                마커 {tradeMarkers?.length || 0}
              </Text>
            )}
          </Space>

          {/* Annotation Toggle */}
          {annotations && annotations.length > 0 && (
            <Space size={4}>
              <Switch
                size="small"
                checked={showAnnotations}
                onChange={setShowAnnotations}
                style={{ background: showAnnotations ? '#1890ff' : undefined }}
              />
              {!isMobile && (
                <Text style={{ fontSize: '11px', color: '#6b7280' }}>
                  주석 {annotations.filter(a => a.is_active).length}
                </Text>
              )}
            </Space>
          )}
        </Space>
      </div>

      {/* Chart Container */}
      <div
        ref={chartContainerRef}
        onContextMenu={(e) => {
          if (isMobile) return; // 모바일에서는 context menu 비활성화

          e.preventDefault();

          // 차트에서 클릭한 가격 계산
          const rect = chartContainerRef.current.getBoundingClientRect();
          const y = e.clientY - rect.top;

          // lightweight-charts의 coordinateToPrice 사용
          if (candlestickSeriesRef.current && chartRef.current) {
            try {
              const price = candlestickSeriesRef.current.coordinateToPrice(y);
              if (price && price > 0) {
                // 클릭 위치 근처의 어노테이션 찾기 (가격 차이 1% 이내)
                const threshold = price * 0.01;
                const nearbyAnnotation = annotations.find(a =>
                  a.is_active &&
                  a.price &&
                  Math.abs(parseFloat(a.price) - price) < threshold
                );

                setContextMenu({
                  visible: true,
                  x: e.clientX,
                  y: e.clientY,
                  price: price,
                  nearbyAnnotation: nearbyAnnotation || null,
                });
              }
            } catch (err) {
              console.warn('[TradingChart] Failed to get price from coordinate:', err);
            }
          }
        }}
        onClick={() => {
          // 다른 곳 클릭 시 context menu 닫기
          if (contextMenu.visible) {
            setContextMenu({ visible: false, x: 0, y: 0, price: null, nearbyAnnotation: null });
          }
        }}
        style={{
          width: '100%',
          height: `${height}px`,
          minHeight: isMobile ? '280px' : '400px',
          border: '1px solid #e5e7eb',
          borderTop: 'none',
          borderRadius: '0 0 12px 12px',
        }}
      />

      {/* Context Menu for Annotations */}
      {contextMenu.visible && (
        <div
          style={{
            position: 'fixed',
            top: contextMenu.y,
            left: contextMenu.x,
            background: '#ffffff',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 4px 16px rgba(0,0,0,0.12)',
            zIndex: 1000,
            minWidth: '180px',
            overflow: 'hidden',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header with price */}
          <div style={{
            padding: '8px 12px',
            borderBottom: '1px solid #f0f0f0',
            fontSize: '11px',
            color: '#9ca3af',
            background: '#fafafa',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}>
            <span>${formatPrice(contextMenu.price)}</span>
            {contextMenu.nearbyAnnotation && (
              <span style={{
                background: '#e6f7ff',
                color: '#1890ff',
                padding: '2px 6px',
                borderRadius: '4px',
                fontSize: '10px',
              }}>
                주석 선택됨
              </span>
            )}
          </div>

          {/* 기존 어노테이션이 있을 때 - 편집/삭제 옵션 */}
          {contextMenu.nearbyAnnotation && (
            <>
              <div
                onClick={() => {
                  setEditingAnnotation(contextMenu.nearbyAnnotation);
                  setEditModalOpen(true);
                  setContextMenu({ visible: false, x: 0, y: 0, price: null, nearbyAnnotation: null });
                }}
                style={{
                  padding: '10px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '13px',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f7'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <span style={{ color: '#1890ff' }}>✎</span>
                주석 편집
              </div>
              {onAnnotationDelete && (
                <div
                  onClick={() => {
                    onAnnotationDelete(contextMenu.nearbyAnnotation.id);
                    setContextMenu({ visible: false, x: 0, y: 0, price: null, nearbyAnnotation: null });
                  }}
                  style={{
                    padding: '10px 12px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '13px',
                    transition: 'background 0.15s',
                    color: '#ff4d4f',
                  }}
                  onMouseEnter={(e) => e.currentTarget.style.background = '#fff1f0'}
                  onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                >
                  <span>✕</span>
                  주석 삭제
                </div>
              )}
              <div style={{ borderTop: '1px solid #f0f0f0', margin: '4px 0' }} />
            </>
          )}

          {/* 새 어노테이션 추가 옵션 */}
          {onAnnotationAdd && (
            <>
              <div
                onClick={() => {
                  onAnnotationAdd({
                    type: 'hline',
                    price: contextMenu.price,
                    label: `지지/저항 $${formatPrice(contextMenu.price)}`,
                  });
                  setContextMenu({ visible: false, x: 0, y: 0, price: null, nearbyAnnotation: null });
                }}
                style={{
                  padding: '10px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '13px',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f7'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <span style={{ color: '#52c41a' }}>━</span>
                수평선 추가
              </div>
              <div
                onClick={() => {
                  onAnnotationAdd({
                    type: 'price_level',
                    price: contextMenu.price,
                    label: `알림 $${formatPrice(contextMenu.price)}`,
                    alert_enabled: true,
                  });
                  setContextMenu({ visible: false, x: 0, y: 0, price: null, nearbyAnnotation: null });
                }}
                style={{
                  padding: '10px 12px',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '13px',
                  transition: 'background 0.15s',
                }}
                onMouseEnter={(e) => e.currentTarget.style.background = '#f5f5f7'}
                onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
              >
                <span style={{ color: '#ff4d4f' }}>┅</span>
                가격 알림 추가
              </div>
            </>
          )}
        </div>
      )}

      {/* Marker Legend - FreqUI 스타일 */}
      {showMarkers && tradeMarkers && tradeMarkers.length > 0 && (
        <div style={{
          position: 'absolute',
          bottom: isMobile ? '8px' : '16px',
          left: isMobile ? '8px' : '16px',
          background: 'rgba(255,255,255,0.95)',
          padding: isMobile ? '4px 8px' : '8px 12px',
          borderRadius: isMobile ? '6px' : '8px',
          border: '1px solid #e5e7eb',
          display: 'flex',
          flexWrap: 'wrap',
          gap: isMobile ? '6px' : '12px',
          fontSize: isMobile ? '9px' : '11px',
          color: '#6b7280',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
          maxWidth: isMobile ? '200px' : 'none',
        }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
            <span style={{ color: '#00ff26', fontSize: isMobile ? '10px' : '12px' }}>▲</span>
            {isMobile ? 'L' : '롱 진입'}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
            <span style={{ color: '#00ff26', fontSize: isMobile ? '10px' : '12px' }}>▼</span>
            {isMobile ? 'S' : '숏 진입'}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
            <span style={{ color: '#00d26a', fontSize: isMobile ? '10px' : '12px' }}>◆</span>
            {isMobile ? '+' : '익절'}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
            <span style={{ color: '#ff4757', fontSize: isMobile ? '10px' : '12px' }}>◆</span>
            {isMobile ? '-' : '손절'}
          </span>
        </div>
      )}

      {/* Position Lines Legend - 열린 포지션이 있을 때만 표시 */}
      {positions && positions.length > 0 && (
        <div style={{
          position: 'absolute',
          bottom: isMobile ? '8px' : '16px',
          right: isMobile ? '8px' : '16px',
          background: 'rgba(255,255,255,0.95)',
          padding: isMobile ? '4px 8px' : '8px 12px',
          borderRadius: isMobile ? '6px' : '8px',
          border: '1px solid #e5e7eb',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px',
          fontSize: isMobile ? '9px' : '11px',
          color: '#6b7280',
          boxShadow: '0 2px 8px rgba(0,0,0,0.08)',
        }}>
          <span style={{ fontWeight: 600, color: '#374151' }}>
            {isMobile ? '포지션' : '열린 포지션'}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '16px', height: '2px', background: '#0ecb81' }}></span>
            {isMobile ? 'L' : '롱 진입가'}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '16px', height: '2px', background: '#f6465d' }}></span>
            {isMobile ? 'S' : '숏 진입가'}
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '16px', height: '1px', background: '#ff4757', borderStyle: 'dashed' }}></span>
            SL
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '16px', height: '1px', background: '#00d26a', borderStyle: 'dashed' }}></span>
            TP
          </span>
        </div>
      )}

      {/* Annotation Edit Modal */}
      <Modal
        title="주석 편집"
        open={editModalOpen}
        onCancel={() => {
          setEditModalOpen(false);
          setEditingAnnotation(null);
        }}
        footer={[
          <Button
            key="delete"
            danger
            icon={<DeleteOutlined />}
            onClick={() => {
              if (onAnnotationDelete && editingAnnotation) {
                onAnnotationDelete(editingAnnotation.id);
                setEditModalOpen(false);
                setEditingAnnotation(null);
              }
            }}
          >
            삭제
          </Button>,
          <Button key="cancel" onClick={() => {
            setEditModalOpen(false);
            setEditingAnnotation(null);
          }}>
            취소
          </Button>,
          <Button
            key="save"
            type="primary"
            onClick={async () => {
              if (editingAnnotation) {
                // 알림 리셋 요청이 있으면 먼저 처리
                if (editingAnnotation._reset_alert && onAnnotationResetAlert) {
                  await onAnnotationResetAlert(editingAnnotation.id);
                }
                // 일반 편집 저장
                if (onAnnotationEdit) {
                  onAnnotationEdit(editingAnnotation.id, {
                    label: editingAnnotation.label,
                    price: editingAnnotation.price,
                    style: editingAnnotation.style,
                    alert_enabled: editingAnnotation.alert_enabled,
                  });
                }
                setEditModalOpen(false);
                setEditingAnnotation(null);
              }
            }}
          >
            저장
          </Button>,
        ]}
        width={400}
        centered
      >
        {editingAnnotation && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Label */}
            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>라벨</Text>
              <Input
                value={editingAnnotation.label || ''}
                onChange={(e) => setEditingAnnotation({
                  ...editingAnnotation,
                  label: e.target.value
                })}
                placeholder="주석 라벨 입력"
              />
            </div>

            {/* Price */}
            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>가격</Text>
              <InputNumber
                value={editingAnnotation.price}
                onChange={(value) => setEditingAnnotation({
                  ...editingAnnotation,
                  price: value
                })}
                style={{ width: '100%' }}
                formatter={(value) => `$ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                parser={(value) => value.replace(/\$\s?|(,*)/g, '')}
              />
            </div>

            {/* Color */}
            <div>
              <Text strong style={{ display: 'block', marginBottom: 8 }}>색상</Text>
              <ColorPicker
                value={editingAnnotation.style?.color || '#1890ff'}
                onChange={(color) => setEditingAnnotation({
                  ...editingAnnotation,
                  style: { ...editingAnnotation.style, color: color.toHexString() }
                })}
              />
            </div>

            {/* Alert Toggle (price_level only) */}
            {editingAnnotation.annotation_type === 'price_level' && (
              <>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Text strong>가격 알림</Text>
                  <Switch
                    checked={editingAnnotation.alert_enabled}
                    onChange={(checked) => setEditingAnnotation({
                      ...editingAnnotation,
                      alert_enabled: checked
                    })}
                  />
                </div>

                {/* Alert triggered status */}
                {editingAnnotation.alert_triggered && (
                  <div style={{
                    padding: '8px 12px',
                    background: '#fff7e6',
                    border: '1px solid #ffd591',
                    borderRadius: '6px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                  }}>
                    <span style={{ fontSize: '12px', color: '#ad6800' }}>
                      ⚡ 이 알림은 이미 트리거되었습니다
                    </span>
                    <Button
                      size="small"
                      onClick={() => setEditingAnnotation({
                        ...editingAnnotation,
                        alert_triggered: false,
                        _reset_alert: true // 저장 시 리셋 요청 플래그
                      })}
                    >
                      리셋
                    </Button>
                  </div>
                )}
              </>
            )}

            {/* Type Info */}
            <div style={{
              padding: '8px 12px',
              background: '#f5f5f5',
              borderRadius: '6px',
              fontSize: '12px',
              color: '#666',
            }}>
              <span>타입: </span>
              <span style={{ fontWeight: 600 }}>
                {editingAnnotation.annotation_type === 'hline' ? '수평선' :
                 editingAnnotation.annotation_type === 'price_level' ? '가격 알림' :
                 editingAnnotation.annotation_type}
              </span>
            </div>
          </div>
        )}
      </Modal>

      {/* Coin Selection Modal */}
      <Modal
        title={
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            fontSize: isMobile ? '16px' : '18px',
            fontWeight: '700',
          }}>
            코인 선택
          </div>
        }
        open={coinModalOpen}
        onCancel={() => {
          setCoinModalOpen(false);
          setSearchTerm('');
        }}
        footer={null}
        width={isMobile ? '100%' : 420}
        centered
        styles={{
          body: { padding: '16px 0' },
        }}
      >
        {/* Search Input */}
        <div style={{ padding: '0 16px 16px' }}>
          <Input
            prefix={<SearchOutlined style={{ color: '#9ca3af' }} />}
            placeholder="코인 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              borderRadius: '10px',
              padding: isMobile ? '8px 12px' : '10px 14px',
              fontSize: '14px',
            }}
            autoFocus
          />
        </div>

        {/* Coin List */}
        <div style={{
          maxHeight: isMobile ? '60vh' : '400px',
          overflowY: 'auto',
          padding: '0 8px',
        }}>
          {filteredSymbols.map((sym) => {
            const symCoinId = sym.replace('USDT', '').toLowerCase();
            const symCoinInfo = COIN_DATA[symCoinId] || {
              name: symCoinId.toUpperCase(),
              symbol: symCoinId.charAt(0).toUpperCase(),
              color: '#1890ff',
              gradient: 'linear-gradient(135deg, #1890ff 0%, #40a9ff 100%)'
            };
            const isSelected = sym === symbol.replace('/USDT', '').replace('USDT', '') + 'USDT' ||
              sym === symbol.replace('/USDT', '');

            return (
              <div
                key={sym}
                onClick={() => handleCoinSelect(sym)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: isMobile ? '10px' : '14px',
                  padding: isMobile ? '12px' : '14px 16px',
                  borderRadius: '12px',
                  cursor: 'pointer',
                  background: isSelected ? '#f0f9ff' : 'transparent',
                  border: isSelected ? '1px solid #bae6fd' : '1px solid transparent',
                  transition: 'all 0.15s ease',
                  marginBottom: '4px',
                }}
                onMouseEnter={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = '#f5f5f7';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isSelected) {
                    e.currentTarget.style.background = 'transparent';
                  }
                }}
              >
                {/* Coin Icon */}
                <div style={{
                  width: isMobile ? '36px' : '44px',
                  height: isMobile ? '36px' : '44px',
                  borderRadius: '50%',
                  background: symCoinInfo.gradient,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: isMobile ? '14px' : '18px',
                  fontWeight: '700',
                  color: '#fff',
                  boxShadow: `0 4px 12px ${symCoinInfo.color}30`,
                }}>
                  {symCoinInfo.symbol}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontWeight: '600',
                    fontSize: isMobile ? '14px' : '15px',
                    color: '#111827',
                  }}>
                    {sym.replace('USDT', '')}
                  </div>
                  <div style={{ fontSize: isMobile ? '11px' : '12px', color: '#9ca3af' }}>
                    {symCoinInfo.name}
                  </div>
                </div>
                {isSelected && (
                  <div style={{
                    width: isMobile ? '20px' : '24px',
                    height: isMobile ? '20px' : '24px',
                    borderRadius: '50%',
                    background: '#0ea5e9',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    fontSize: isMobile ? '12px' : '14px',
                  }}>
                    ✓
                  </div>
                )}
              </div>
            );
          })}

          {filteredSymbols.length === 0 && (
            <div style={{
              textAlign: 'center',
              color: '#9ca3af',
              padding: '40px 20px',
              fontSize: '14px',
            }}>
              검색 결과가 없습니다
            </div>
          )}
        </div>
      </Modal>
    </div>
  );
}

export default TradingChart;
