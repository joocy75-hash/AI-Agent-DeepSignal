# 컴포넌트 패턴 참조

## 현재 프로젝트의 컴포넌트 구조

```
components/
├── ErrorBoundary.jsx      # 에러 바운더리
├── ConnectionStatus.jsx   # WebSocket 연결 상태
├── TradingNotification.jsx # 거래 알림
├── RiskGauge.jsx          # 리스크 게이지
├── BotLogViewer.jsx       # 봇 로그 뷰어
├── OrderActivityLog.jsx   # 주문 활동 로그
│
├── layout/
│   └── MainLayout.jsx     # 메인 레이아웃
│
├── dashboard/
│   ├── SystemStatus.jsx   # 시스템 상태
│   ├── RecentTrades.jsx   # 최근 거래
│   ├── RiskMetrics.jsx    # 리스크 지표
│   ├── PerformanceChart.jsx # 성과 차트
│   └── UrgentAlerts.jsx   # 긴급 알림
│
├── backtest/
│   ├── BeginnerGuide.jsx  # 초보자 가이드
│   └── EquityCurveChart.jsx # 자산 곡선
│
├── strategy/
│   └── StrategyBuilder.jsx # 전략 빌더
│
├── settings/
│   └── TwoFactorSettings.jsx # 2FA 설정
│
└── realtime/
    └── TradingChart.jsx   # 실시간 차트
```

---

## 컴포넌트 작성 패턴

### 1. 기본 함수형 컴포넌트

```jsx
import { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const MyComponent = ({ title, onAction }) => {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = async () => {
    setIsLoading(true);
    try {
      await onAction();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 bg-gray-800 rounded-lg">
      <h2 className="text-xl font-bold text-white">{title}</h2>
      <button
        onClick={handleClick}
        disabled={isLoading}
        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded-lg disabled:opacity-50"
      >
        {isLoading ? '처리 중...' : '실행'}
      </button>
    </div>
  );
};

MyComponent.propTypes = {
  title: PropTypes.string.isRequired,
  onAction: PropTypes.func.isRequired,
};

export default MyComponent;
```

### 2. 데이터 페칭 컴포넌트

```jsx
import { useState, useEffect, useCallback } from 'react';
import apiClient from '../api/client';

const DataFetchingComponent = ({ endpoint, renderItem }) => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiClient.get(endpoint);
      setData(response.data);
    } catch (err) {
      setError(err.message || 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-32">
        <span className="loading loading-spinner loading-md" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-500/10 border border-red-500 rounded-lg">
        <p className="text-red-400">Error: {error}</p>
        <button
          onClick={fetchData}
          className="mt-2 text-sm text-blue-400 hover:underline"
        >
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div>
      {data.map((item, index) => renderItem(item, index))}
    </div>
  );
};

// 사용 예
<DataFetchingComponent
  endpoint="/api/trades"
  renderItem={(trade) => (
    <TradeCard key={trade.id} trade={trade} />
  )}
/>
```

### 3. 폼 컴포넌트

```jsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { message } from 'antd';

const FormComponent = ({ onSubmit }) => {
  const [submitting, setSubmitting] = useState(false);
  const { register, handleSubmit, formState: { errors }, reset } = useForm();

  const handleFormSubmit = async (data) => {
    setSubmitting(true);
    try {
      await onSubmit(data);
      message.success('저장되었습니다');
      reset();
    } catch (err) {
      message.error(err.message || '저장 실패');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div>
        <label className="block text-sm text-gray-400 mb-1">이름</label>
        <input
          {...register('name', { required: '이름을 입력하세요' })}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
          placeholder="이름 입력"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-400">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label className="block text-sm text-gray-400 mb-1">금액</label>
        <input
          type="number"
          {...register('amount', {
            required: '금액을 입력하세요',
            min: { value: 0, message: '0 이상 입력하세요' }
          })}
          className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
          placeholder="0.00"
        />
        {errors.amount && (
          <p className="mt-1 text-sm text-red-400">{errors.amount.message}</p>
        )}
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg disabled:opacity-50"
      >
        {submitting ? '저장 중...' : '저장'}
      </button>
    </form>
  );
};
```

### 4. 모달 컴포넌트

```jsx
import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

const Modal = ({ isOpen, onClose, title, children }) => {
  const modalRef = useRef(null);

  // ESC 키로 닫기
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // 외부 클릭으로 닫기
  const handleBackdropClick = (e) => {
    if (modalRef.current && !modalRef.current.contains(e.target)) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={handleBackdropClick}
    >
      <div
        ref={modalRef}
        className="bg-gray-800 rounded-xl shadow-xl max-w-md w-full mx-4 max-h-[90vh] overflow-auto"
      >
        {/* 헤더 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-700">
          <h3 className="text-lg font-semibold text-white">{title}</h3>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-700 rounded-lg transition"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* 내용 */}
        <div className="p-4">
          {children}
        </div>
      </div>
    </div>
  );
};

// 사용 예
const [isOpen, setIsOpen] = useState(false);

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="설정"
>
  <SettingsForm />
</Modal>
```

### 5. 에러 바운더리

```jsx
import { Component } from 'react';

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    // 에러 리포팅 서비스로 전송 가능
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] p-8">
          <div className="text-red-400 text-xl mb-4">⚠️ 오류가 발생했습니다</div>
          <p className="text-gray-400 text-center mb-4">
            {this.state.error?.message || '알 수 없는 오류'}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg"
          >
            페이지 새로고침
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

// 사용
<ErrorBoundary>
  <RiskyComponent />
</ErrorBoundary>
```

---

## 재사용 가능한 UI 컴포넌트

### 로딩 스피너

```jsx
const LoadingSpinner = ({ size = 'md' }) => {
  const sizeClasses = {
    sm: 'loading-sm',
    md: 'loading-md',
    lg: 'loading-lg',
  };

  return (
    <div className="flex items-center justify-center">
      <span className={`loading loading-spinner ${sizeClasses[size]}`} />
    </div>
  );
};
```

### 빈 상태 컴포넌트

```jsx
const EmptyState = ({ icon: Icon, title, description, action }) => (
  <div className="flex flex-col items-center justify-center p-8 text-center">
    {Icon && <Icon className="w-12 h-12 text-gray-500 mb-4" />}
    <h3 className="text-lg font-medium text-white mb-2">{title}</h3>
    {description && <p className="text-gray-400 mb-4">{description}</p>}
    {action}
  </div>
);

// 사용
<EmptyState
  icon={Inbox}
  title="거래 내역이 없습니다"
  description="첫 번째 거래를 시작해보세요"
  action={<button className="btn btn-primary">시작하기</button>}
/>
```

### 상태 배지

```jsx
const StatusBadge = ({ status }) => {
  const statusConfig = {
    running: { color: 'bg-green-500', text: '실행 중' },
    stopped: { color: 'bg-gray-500', text: '중지됨' },
    error: { color: 'bg-red-500', text: '오류' },
    pending: { color: 'bg-yellow-500', text: '대기 중' },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium text-white ${config.color}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-white mr-1.5 animate-pulse" />
      {config.text}
    </span>
  );
};
```

### 수익/손실 표시

```jsx
const PnLDisplay = ({ value, percent }) => {
  const isPositive = value >= 0;
  const colorClass = isPositive ? 'text-green-400' : 'text-red-400';
  const icon = isPositive ? '↑' : '↓';

  return (
    <div className={colorClass}>
      <span className="font-bold">
        {icon} ${Math.abs(value).toFixed(2)}
      </span>
      {percent !== undefined && (
        <span className="text-sm ml-1">
          ({isPositive ? '+' : ''}{percent.toFixed(2)}%)
        </span>
      )}
    </div>
  );
};
```
