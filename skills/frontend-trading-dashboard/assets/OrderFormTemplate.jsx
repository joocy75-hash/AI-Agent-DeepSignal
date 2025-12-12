/**
 * 주문 폼 컴포넌트 템플릿
 *
 * 의존성:
 * - lucide-react: npm install lucide-react
 * - antd (선택): npm install antd
 */

import { useState, useEffect } from 'react';
import { AlertCircle, TrendingUp, TrendingDown, Calculator } from 'lucide-react';

/**
 * 기본 주문 폼
 */
export const BasicOrderForm = ({
  symbol = 'BTCUSDT',
  currentPrice = 0,
  balance = 0,
  onSubmit,
  loading = false,
}) => {
  const [side, setSide] = useState('buy'); // 'buy' or 'sell'
  const [orderType, setOrderType] = useState('market'); // 'market' or 'limit'
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState('');
  const [leverage, setLeverage] = useState(5);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit({
      symbol,
      side,
      orderType,
      amount: parseFloat(amount),
      price: orderType === 'limit' ? parseFloat(price) : currentPrice,
      leverage,
    });
  };

  const percentageButtons = [25, 50, 75, 100];

  const handlePercentage = (percent) => {
    const maxAmount = (balance * leverage) / currentPrice;
    setAmount((maxAmount * (percent / 100)).toFixed(6));
  };

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      <h3 className="text-lg font-semibold text-white mb-4">주문</h3>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 매수/매도 탭 */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setSide('buy')}
            className={`flex-1 py-2 rounded-lg font-medium transition ${
              side === 'buy'
                ? 'bg-green-500 text-white'
                : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
            }`}
          >
            <TrendingUp className="w-4 h-4 inline mr-1" />
            매수
          </button>
          <button
            type="button"
            onClick={() => setSide('sell')}
            className={`flex-1 py-2 rounded-lg font-medium transition ${
              side === 'sell'
                ? 'bg-red-500 text-white'
                : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
            }`}
          >
            <TrendingDown className="w-4 h-4 inline mr-1" />
            매도
          </button>
        </div>

        {/* 주문 유형 */}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => setOrderType('market')}
            className={`flex-1 py-1.5 text-sm rounded-lg transition ${
              orderType === 'market'
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500'
                : 'bg-gray-700 text-gray-400 border border-transparent'
            }`}
          >
            시장가
          </button>
          <button
            type="button"
            onClick={() => setOrderType('limit')}
            className={`flex-1 py-1.5 text-sm rounded-lg transition ${
              orderType === 'limit'
                ? 'bg-blue-500/20 text-blue-400 border border-blue-500'
                : 'bg-gray-700 text-gray-400 border border-transparent'
            }`}
          >
            지정가
          </button>
        </div>

        {/* 레버리지 */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">
            레버리지: {leverage}x
          </label>
          <input
            type="range"
            min="1"
            max="50"
            value={leverage}
            onChange={(e) => setLeverage(parseInt(e.target.value))}
            className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer"
          />
          <div className="flex justify-between text-xs text-gray-500 mt-1">
            <span>1x</span>
            <span>10x</span>
            <span>25x</span>
            <span>50x</span>
          </div>
        </div>

        {/* 가격 (지정가만) */}
        {orderType === 'limit' && (
          <div>
            <label className="block text-sm text-gray-400 mb-1">가격 (USDT)</label>
            <input
              type="number"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
              placeholder={currentPrice.toFixed(2)}
            />
          </div>
        )}

        {/* 수량 */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">수량</label>
          <input
            type="number"
            step="0.000001"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white"
            placeholder="0.00"
          />
          <div className="flex gap-2 mt-2">
            {percentageButtons.map((percent) => (
              <button
                key={percent}
                type="button"
                onClick={() => handlePercentage(percent)}
                className="flex-1 py-1 text-xs bg-gray-700 text-gray-400 rounded hover:bg-gray-600 transition"
              >
                {percent}%
              </button>
            ))}
          </div>
        </div>

        {/* 예상 비용 */}
        <div className="p-3 bg-gray-700/50 rounded-lg">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">예상 비용</span>
            <span className="text-white">
              ${((parseFloat(amount) || 0) * currentPrice / leverage).toFixed(2)} USDT
            </span>
          </div>
          <div className="flex justify-between text-sm mt-1">
            <span className="text-gray-400">예상 수수료</span>
            <span className="text-white">
              ${((parseFloat(amount) || 0) * currentPrice * 0.0006).toFixed(4)} USDT
            </span>
          </div>
        </div>

        {/* 제출 버튼 */}
        <button
          type="submit"
          disabled={loading || !amount}
          className={`w-full py-3 rounded-lg font-semibold transition ${
            side === 'buy'
              ? 'bg-green-500 hover:bg-green-600 text-white'
              : 'bg-red-500 hover:bg-red-600 text-white'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="loading loading-spinner loading-sm" />
              처리 중...
            </span>
          ) : (
            `${side === 'buy' ? '롱' : '숏'} ${orderType === 'market' ? '시장가' : '지정가'}`
          )}
        </button>
      </form>
    </div>
  );
};

/**
 * TP/SL 설정 폼
 */
export const TPSLForm = ({
  entryPrice,
  side = 'long',
  onChange,
  values = {},
}) => {
  const [tpPercent, setTpPercent] = useState(values.tpPercent || '');
  const [slPercent, setSlPercent] = useState(values.slPercent || '');

  const calculatePrice = (percent, isTP) => {
    if (!percent || !entryPrice) return '-';

    const multiplier = parseFloat(percent) / 100;
    if (side === 'long') {
      return isTP
        ? (entryPrice * (1 + multiplier)).toFixed(2)
        : (entryPrice * (1 - multiplier)).toFixed(2);
    } else {
      return isTP
        ? (entryPrice * (1 - multiplier)).toFixed(2)
        : (entryPrice * (1 + multiplier)).toFixed(2);
    }
  };

  useEffect(() => {
    onChange?.({
      tpPercent: parseFloat(tpPercent) || null,
      slPercent: parseFloat(slPercent) || null,
      tpPrice: parseFloat(calculatePrice(tpPercent, true)) || null,
      slPrice: parseFloat(calculatePrice(slPercent, false)) || null,
    });
  }, [tpPercent, slPercent]);

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      <h4 className="text-sm font-medium text-gray-400 mb-3">TP/SL 설정</h4>

      <div className="space-y-3">
        {/* Take Profit */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            익절 (%)
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              step="0.1"
              value={tpPercent}
              onChange={(e) => setTpPercent(e.target.value)}
              className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm"
              placeholder="2.0"
            />
            <div className="px-3 py-2 bg-green-500/10 border border-green-500/20 rounded-lg text-green-400 text-sm min-w-[80px] text-center">
              ${calculatePrice(tpPercent, true)}
            </div>
          </div>
        </div>

        {/* Stop Loss */}
        <div>
          <label className="block text-xs text-gray-500 mb-1">
            손절 (%)
          </label>
          <div className="flex gap-2">
            <input
              type="number"
              step="0.1"
              value={slPercent}
              onChange={(e) => setSlPercent(e.target.value)}
              className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white text-sm"
              placeholder="1.0"
            />
            <div className="px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg text-red-400 text-sm min-w-[80px] text-center">
              ${calculatePrice(slPercent, false)}
            </div>
          </div>
        </div>
      </div>

      {/* 손익비 */}
      {tpPercent && slPercent && (
        <div className="mt-3 pt-3 border-t border-gray-700">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">손익비</span>
            <span className="text-white">
              1:{(parseFloat(tpPercent) / parseFloat(slPercent)).toFixed(1)}
            </span>
          </div>
        </div>
      )}
    </div>
  );
};

/**
 * 포지션 크기 계산기
 */
export const PositionCalculator = ({
  balance = 0,
  currentPrice = 0,
}) => {
  const [riskPercent, setRiskPercent] = useState(2);
  const [stopLossPercent, setStopLossPercent] = useState(1);
  const [leverage, setLeverage] = useState(5);

  const calculatePosition = () => {
    if (!riskPercent || !stopLossPercent || !currentPrice) {
      return { size: 0, value: 0 };
    }

    // 리스크 금액 = 잔고 × 리스크%
    const riskAmount = balance * (riskPercent / 100);

    // 포지션 크기 = 리스크 금액 / 손절%
    const positionValue = riskAmount / (stopLossPercent / 100);

    // 필요 마진 = 포지션 크기 / 레버리지
    const marginRequired = positionValue / leverage;

    // 수량 = 포지션 가치 / 현재가
    const size = positionValue / currentPrice;

    return {
      size: size.toFixed(6),
      value: positionValue.toFixed(2),
      margin: marginRequired.toFixed(2),
      riskAmount: riskAmount.toFixed(2),
    };
  };

  const result = calculatePosition();

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
      <div className="flex items-center gap-2 mb-4">
        <Calculator className="w-5 h-5 text-blue-400" />
        <h3 className="text-lg font-semibold text-white">포지션 계산기</h3>
      </div>

      <div className="space-y-4">
        {/* 잔고 표시 */}
        <div className="p-3 bg-gray-700/50 rounded-lg">
          <p className="text-xs text-gray-500">가용 잔고</p>
          <p className="text-lg font-bold text-white">${balance.toFixed(2)}</p>
        </div>

        {/* 리스크 % */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">
            리스크: {riskPercent}%
          </label>
          <input
            type="range"
            min="0.5"
            max="10"
            step="0.5"
            value={riskPercent}
            onChange={(e) => setRiskPercent(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>

        {/* 손절 % */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">
            손절: {stopLossPercent}%
          </label>
          <input
            type="range"
            min="0.5"
            max="5"
            step="0.5"
            value={stopLossPercent}
            onChange={(e) => setStopLossPercent(parseFloat(e.target.value))}
            className="w-full"
          />
        </div>

        {/* 레버리지 */}
        <div>
          <label className="block text-sm text-gray-400 mb-1">
            레버리지: {leverage}x
          </label>
          <input
            type="range"
            min="1"
            max="20"
            value={leverage}
            onChange={(e) => setLeverage(parseInt(e.target.value))}
            className="w-full"
          />
        </div>

        {/* 결과 */}
        <div className="space-y-2 pt-3 border-t border-gray-700">
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">리스크 금액</span>
            <span className="text-red-400">${result.riskAmount}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">포지션 크기</span>
            <span className="text-white">{result.size}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">포지션 가치</span>
            <span className="text-white">${result.value}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-400">필요 마진</span>
            <span className="text-blue-400">${result.margin}</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default {
  BasicOrderForm,
  TPSLForm,
  PositionCalculator,
};
