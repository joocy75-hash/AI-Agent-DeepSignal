/**
 * 거래 카드 컴포넌트 템플릿
 *
 * 사용처:
 * - 대시보드 통계 카드
 * - 포지션 요약 카드
 * - 성과 지표 카드
 */

import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

/**
 * 통계 카드 컴포넌트
 */
export const StatsCard = ({
  title,
  value,
  icon: Icon,
  trend,
  trendValue,
  className = '',
}) => {
  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-400';
    if (trend === 'down') return 'text-red-400';
    return 'text-gray-400';
  };

  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp className="w-4 h-4" />;
    if (trend === 'down') return <TrendingDown className="w-4 h-4" />;
    return <Minus className="w-4 h-4" />;
  };

  return (
    <div className={`bg-gray-800 rounded-xl p-4 border border-gray-700 ${className}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-400 mb-1">{title}</p>
          <p className="text-2xl font-bold text-white">{value}</p>
          {trendValue !== undefined && (
            <div className={`flex items-center gap-1 mt-2 text-sm ${getTrendColor()}`}>
              {getTrendIcon()}
              <span>{trendValue}</span>
            </div>
          )}
        </div>
        {Icon && (
          <div className="p-3 bg-blue-500/10 rounded-lg">
            <Icon className="w-6 h-6 text-blue-400" />
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * 포지션 카드 컴포넌트
 */
export const PositionCard = ({
  symbol,
  side,
  entryPrice,
  currentPrice,
  pnl,
  pnlPercent,
  size,
  leverage,
  onClose,
}) => {
  const isLong = side === 'long';
  const isProfit = pnl >= 0;

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      {/* 헤더 */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-white">{symbol}</span>
          <span
            className={`px-2 py-0.5 rounded text-xs font-medium ${
              isLong ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
            }`}
          >
            {isLong ? 'LONG' : 'SHORT'}
          </span>
          <span className="px-2 py-0.5 rounded text-xs font-medium bg-yellow-500/10 text-yellow-400">
            {leverage}x
          </span>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="px-3 py-1 text-sm text-red-400 hover:bg-red-500/10 rounded transition"
          >
            청산
          </button>
        )}
      </div>

      {/* 가격 정보 */}
      <div className="grid grid-cols-2 gap-4 mb-3">
        <div>
          <p className="text-xs text-gray-500 mb-1">진입가</p>
          <p className="text-white font-mono">${entryPrice.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 mb-1">현재가</p>
          <p className="text-white font-mono">${currentPrice.toLocaleString()}</p>
        </div>
      </div>

      {/* PnL */}
      <div className="flex items-center justify-between pt-3 border-t border-gray-700">
        <div>
          <p className="text-xs text-gray-500 mb-1">수량</p>
          <p className="text-white">{size}</p>
        </div>
        <div className="text-right">
          <p className="text-xs text-gray-500 mb-1">손익</p>
          <p className={`text-lg font-bold ${isProfit ? 'text-green-400' : 'text-red-400'}`}>
            {isProfit ? '+' : ''}{pnl.toFixed(2)} ({isProfit ? '+' : ''}{pnlPercent.toFixed(2)}%)
          </p>
        </div>
      </div>
    </div>
  );
};

/**
 * 거래 내역 카드 컴포넌트
 */
export const TradeCard = ({
  symbol,
  side,
  entryPrice,
  exitPrice,
  pnl,
  pnlPercent,
  exitReason,
  time,
}) => {
  const isProfit = pnl >= 0;

  const getExitReasonLabel = () => {
    switch (exitReason) {
      case 'take_profit':
        return { label: '익절', color: 'text-green-400' };
      case 'stop_loss':
        return { label: '손절', color: 'text-red-400' };
      case 'signal_reverse':
        return { label: '반전', color: 'text-yellow-400' };
      case 'manual':
        return { label: '수동', color: 'text-gray-400' };
      default:
        return { label: exitReason, color: 'text-gray-400' };
    }
  };

  const exitReasonInfo = getExitReasonLabel();

  return (
    <div className="bg-gray-800 rounded-lg p-3 border border-gray-700 hover:border-gray-600 transition">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* 심볼 및 방향 */}
          <div>
            <div className="flex items-center gap-2">
              <span className="font-medium text-white">{symbol}</span>
              <span
                className={`text-xs ${
                  side === 'buy' ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {side === 'buy' ? 'LONG' : 'SHORT'}
              </span>
            </div>
            <p className="text-xs text-gray-500 mt-0.5">
              {new Date(time).toLocaleString()}
            </p>
          </div>
        </div>

        {/* 가격 */}
        <div className="text-right">
          <p className="text-xs text-gray-500">
            ${entryPrice.toFixed(2)} → ${exitPrice.toFixed(2)}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={exitReasonInfo.color + ' text-xs'}>
              {exitReasonInfo.label}
            </span>
            <span
              className={`font-medium ${
                isProfit ? 'text-green-400' : 'text-red-400'
              }`}
            >
              {isProfit ? '+' : ''}${pnl.toFixed(2)}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

/**
 * 리스크 게이지 컴포넌트
 */
export const RiskGauge = ({ value, max, label }) => {
  const percentage = Math.min((value / max) * 100, 100);

  const getColor = () => {
    if (percentage < 50) return 'bg-green-500';
    if (percentage < 75) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-400">{label}</span>
        <span className="text-sm font-medium text-white">
          {value.toFixed(2)} / {max.toFixed(2)}
        </span>
      </div>
      <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${getColor()} transition-all duration-500`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      <p className="text-xs text-gray-500 mt-1 text-right">
        {percentage.toFixed(1)}% 사용
      </p>
    </div>
  );
};

export default {
  StatsCard,
  PositionCard,
  TradeCard,
  RiskGauge,
};
