/**
 * 차트 컴포넌트 템플릿
 *
 * 의존성:
 * - lightweight-charts: npm install lightweight-charts
 * - recharts: npm install recharts
 */

import { useEffect, useRef, useState } from 'react';
import { createChart } from 'lightweight-charts';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

/**
 * 캔들스틱 차트 (Lightweight Charts)
 */
export const CandlestickChart = ({
  data = [],
  markers = [],
  height = 400,
  className = '',
}) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    // 차트 생성
    const chart = createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { type: 'solid', color: '#1a1a1a' },
        textColor: '#d1d4dc',
      },
      grid: {
        vertLines: { color: '#2B2B43' },
        horzLines: { color: '#2B2B43' },
      },
      crosshair: {
        mode: 1,
        vertLine: { color: '#6B7280', width: 1, style: 2 },
        horzLine: { color: '#6B7280', width: 1, style: 2 },
      },
      rightPriceScale: {
        borderColor: '#2B2B43',
      },
      timeScale: {
        borderColor: '#2B2B43',
        timeVisible: true,
        secondsVisible: false,
      },
    });

    // 캔들스틱 시리즈
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#26a69a',
      downColor: '#ef5350',
      borderDownColor: '#ef5350',
      borderUpColor: '#26a69a',
      wickDownColor: '#ef5350',
      wickUpColor: '#26a69a',
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;

    // 리사이즈 핸들러
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height]);

  // 데이터 업데이트
  useEffect(() => {
    if (candleSeriesRef.current && data.length > 0) {
      const formattedData = data.map((candle) => ({
        time: candle.timestamp / 1000,
        open: parseFloat(candle.open),
        high: parseFloat(candle.high),
        low: parseFloat(candle.low),
        close: parseFloat(candle.close),
      }));

      candleSeriesRef.current.setData(formattedData);
    }
  }, [data]);

  // 마커 업데이트 (진입/청산 표시)
  useEffect(() => {
    if (candleSeriesRef.current && markers.length > 0) {
      const formattedMarkers = markers.map((marker) => ({
        time: marker.time / 1000,
        position: marker.position, // 'aboveBar' or 'belowBar'
        color: marker.color,
        shape: marker.shape, // 'circle', 'square', 'arrowUp', 'arrowDown'
        text: marker.text,
      }));

      candleSeriesRef.current.setMarkers(formattedMarkers);
    }
  }, [markers]);

  return (
    <div
      ref={chartContainerRef}
      className={`w-full rounded-lg overflow-hidden ${className}`}
    />
  );
};

/**
 * 자산 곡선 차트 (Recharts)
 */
export const EquityCurveChart = ({
  data = [],
  height = 300,
  showGrid = true,
  className = '',
}) => {
  const formattedData = data.map((value, index) => ({
    index,
    value: typeof value === 'object' ? value.value : value,
    time: typeof value === 'object' ? value.time : index,
  }));

  return (
    <div className={`w-full ${className}`} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={formattedData}>
          {showGrid && (
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          )}
          <XAxis
            dataKey="index"
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={{ stroke: '#374151' }}
          />
          <YAxis
            tick={{ fill: '#9CA3AF', fontSize: 12 }}
            axisLine={{ stroke: '#374151' }}
            tickLine={{ stroke: '#374151' }}
            domain={['auto', 'auto']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            labelStyle={{ color: '#F9FAFB' }}
            itemStyle={{ color: '#10B981' }}
            formatter={(value) => [`$${value.toFixed(2)}`, '자산']}
          />
          <defs>
            <linearGradient id="colorEquity" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
            </linearGradient>
          </defs>
          <Area
            type="monotone"
            dataKey="value"
            stroke="#10B981"
            strokeWidth={2}
            fill="url(#colorEquity)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * 손익 바 차트
 */
export const PnLBarChart = ({
  data = [],
  height = 200,
  className = '',
}) => {
  // data: [{ date: '2024-01-01', pnl: 100 }, ...]

  return (
    <div className={`w-full ${className}`} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="date"
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            axisLine={{ stroke: '#374151' }}
          />
          <YAxis
            tick={{ fill: '#9CA3AF', fontSize: 10 }}
            axisLine={{ stroke: '#374151' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            formatter={(value) => [
              <span className={value >= 0 ? 'text-green-400' : 'text-red-400'}>
                ${value.toFixed(2)}
              </span>,
              'PnL',
            ]}
          />
          <Line
            type="monotone"
            dataKey="pnl"
            stroke="#60A5FA"
            strokeWidth={2}
            dot={{ fill: '#60A5FA', r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * 미니 스파크라인
 */
export const Sparkline = ({
  data = [],
  width = 100,
  height = 30,
  color = '#10B981',
}) => {
  const isPositive = data.length > 1 ? data[data.length - 1] >= data[0] : true;
  const lineColor = isPositive ? '#10B981' : '#EF4444';

  const formattedData = data.map((value, index) => ({ index, value }));

  return (
    <div style={{ width, height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={formattedData}>
          <Line
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

/**
 * 도넛 차트 (포트폴리오 분포)
 */
import { PieChart, Pie, Cell, Legend } from 'recharts';

export const PortfolioPieChart = ({
  data = [],
  height = 300,
  className = '',
}) => {
  // data: [{ name: 'BTC', value: 50 }, { name: 'ETH', value: 30 }, ...]

  const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];

  return (
    <div className={`w-full ${className}`} style={{ height }}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={80}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Legend
            verticalAlign="bottom"
            height={36}
            formatter={(value) => <span className="text-gray-300">{value}</span>}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1F2937',
              border: '1px solid #374151',
              borderRadius: '8px',
            }}
            formatter={(value) => [`${value}%`, '']}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default {
  CandlestickChart,
  EquityCurveChart,
  PnLBarChart,
  Sparkline,
  PortfolioPieChart,
};
