# 작업 지시서 C: 프론트엔드 UI 구현

## 📌 담당 영역
- 템플릿 목록 (AI 탭)
- 템플릿 카드 (Bitget 스타일)
- Use 모달 (투자금액 입력)
- ROI 미니 차트
- 탭 UI 전환

---

## 1. 사전 요구사항

### 1.1 의존성
```bash
# Task A의 API가 동작해야 함
# GET /grid-templates
# POST /grid-templates/{id}/use
```

### 1.2 필요 파일 위치
```
frontend/src/
├── api/
│   └── gridTemplate.js          # 새로 생성
├── components/grid/
│   ├── index.js                 # 수정 (export 추가)
│   ├── templates/               # 새로 생성 (폴더)
│   │   ├── index.js
│   │   ├── TemplateList.jsx     # AI 탭 컨텐츠
│   │   ├── TemplateCard.jsx     # 템플릿 카드
│   │   ├── TemplateDetail.jsx   # 상세 페이지
│   │   ├── UseTemplateModal.jsx # Use 모달
│   │   └── MiniRoiChart.jsx     # ROI 차트
│   └── GridBotTabs.jsx          # AI/Manual 탭 전환
├── pages/
│   └── BotManagement.jsx        # 수정 (탭 추가)
```

---

## 2. 작업 1: API 클라이언트

### 2.1 파일: `frontend/src/api/gridTemplate.js` (새로 생성)

```javascript
/**
 * Grid Template API Client
 * - 템플릿 목록/상세 조회
 * - 템플릿으로 봇 생성
 */
import axios from 'axios';

const API_BASE = '/api';

// axios 인스턴스 (인증 토큰 자동 포함)
const api = axios.create({
  baseURL: API_BASE,
});

// 요청 인터셉터: 토큰 추가
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const gridTemplateAPI = {
  /**
   * 공개 템플릿 목록 조회
   * @param {Object} params - { symbol?, limit?, offset? }
   * @returns {Promise<{success, data, total}>}
   */
  async list(params = {}) {
    const response = await api.get('/grid-templates', { params });
    return response.data;
  },

  /**
   * 템플릿 상세 조회
   * @param {number} templateId
   * @returns {Promise<{success, data}>}
   */
  async getDetail(templateId) {
    const response = await api.get(`/grid-templates/${templateId}`);
    return response.data;
  },

  /**
   * 템플릿으로 봇 생성 (Use 버튼)
   * @param {number} templateId
   * @param {Object} data - { investment_amount, leverage? }
   * @returns {Promise<{bot_instance_id, grid_config_id, message}>}
   */
  async useTemplate(templateId, data) {
    const response = await api.post(`/grid-templates/${templateId}/use`, data);
    return response.data;
  },
};

export default gridTemplateAPI;
```

### 2.2 검증 체크리스트
- [ ] gridTemplate.js 파일 생성됨
- [ ] list() 함수 정상 동작
- [ ] getDetail() 함수 정상 동작
- [ ] useTemplate() 함수 정상 동작

---

## 3. 작업 2: ROI 미니 차트 컴포넌트

### 3.1 파일: `frontend/src/components/grid/templates/MiniRoiChart.jsx`

```jsx
/**
 * MiniRoiChart - 30일 ROI 미니 차트
 *
 * Bitget 스타일의 작은 선형 차트
 * - 녹색 선 (상승)
 * - 반응형 크기
 */
import React, { useMemo } from 'react';

const MiniRoiChart = ({
  data = [],           // ROI 데이터 배열 (30개)
  width = 100,
  height = 40,
  color = '#00b894',   // 기본 녹색
  strokeWidth = 1.5,
}) => {
  const pathData = useMemo(() => {
    if (!data || data.length < 2) return '';

    const minVal = Math.min(...data);
    const maxVal = Math.max(...data);
    const range = maxVal - minVal || 1;

    const points = data.map((val, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const y = height - ((val - minVal) / range) * height * 0.8 - height * 0.1;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  }, [data, width, height]);

  if (!data || data.length < 2) {
    return (
      <div
        style={{
          width,
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#666',
          fontSize: '10px',
        }}
      >
        No data
      </div>
    );
  }

  // 마지막 값이 시작값보다 높으면 녹색, 낮으면 빨간색
  const isPositive = data[data.length - 1] >= data[0];
  const lineColor = isPositive ? color : '#e74c3c';

  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      {/* 그라데이션 정의 */}
      <defs>
        <linearGradient id={`gradient-${isPositive ? 'green' : 'red'}`} x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stopColor={lineColor} stopOpacity="0.3" />
          <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* 영역 채우기 */}
      <path
        d={`${pathData} L ${width},${height} L 0,${height} Z`}
        fill={`url(#gradient-${isPositive ? 'green' : 'red'})`}
      />

      {/* 선 */}
      <path
        d={pathData}
        fill="none"
        stroke={lineColor}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export default MiniRoiChart;
```

---

## 4. 작업 3: 템플릿 카드 컴포넌트

### 4.1 파일: `frontend/src/components/grid/templates/TemplateCard.jsx`

```jsx
/**
 * TemplateCard - Bitget 스타일 템플릿 카드
 *
 * 표시 정보:
 * - 심볼, 방향, 레버리지 태그
 * - 30D ROI (%)
 * - 미니 차트
 * - 추천 투자 기간
 * - 최소 투자금액
 * - 사용자 수
 * - Use 버튼
 */
import React from 'react';
import { Button, Tag, Tooltip } from 'antd';
import { UserOutlined, RiseOutlined, FallOutlined } from '@ant-design/icons';
import MiniRoiChart from './MiniRoiChart';
import './TemplateCard.css';

const TemplateCard = ({
  template,
  onUse,
  loading = false,
}) => {
  const {
    id,
    symbol,
    direction,
    leverage,
    backtest_roi_30d,
    backtest_max_drawdown,
    roi_chart,
    recommended_period,
    min_investment,
    active_users,
    is_featured,
  } = template;

  const isLong = direction === 'long';
  const roiValue = backtest_roi_30d || 0;
  const isPositiveRoi = roiValue >= 0;

  return (
    <div className={`template-card ${is_featured ? 'featured' : ''}`}>
      {/* 상단 영역: 심볼 + Use 버튼 */}
      <div className="template-card-header">
        <div className="template-symbol-section">
          <h3 className="template-symbol">{symbol}</h3>
          <div className="template-tags">
            <Tag className="tag-type">Futures grid</Tag>
            <Tag className={`tag-direction ${isLong ? 'long' : 'short'}`}>
              {isLong ? 'Long' : 'Short'}
            </Tag>
            <Tag className="tag-leverage">{leverage}X</Tag>
          </div>
        </div>

        <Button
          type="default"
          className="use-button"
          onClick={() => onUse(template)}
          loading={loading}
        >
          Use
        </Button>
      </div>

      {/* 중앙 영역: ROI + 차트 */}
      <div className="template-card-body">
        <div className="roi-section">
          <span className="roi-label">30D backtested ROI</span>
          <span className={`roi-value ${isPositiveRoi ? 'positive' : 'negative'}`}>
            {isPositiveRoi ? '+' : ''}{roiValue.toFixed(2)}%
          </span>
        </div>

        <div className="chart-section">
          <MiniRoiChart
            data={roi_chart || []}
            width={120}
            height={50}
            color={isPositiveRoi ? '#00b894' : '#e74c3c'}
          />
        </div>
      </div>

      {/* 하단 영역: 추가 정보 */}
      <div className="template-card-footer">
        <div className="footer-row">
          <span className="footer-label">Recommended investment period</span>
          <span className="footer-value">{recommended_period || '7-30 days'}</span>
        </div>
        <div className="footer-row">
          <span className="footer-label">Min. investment</span>
          <span className="footer-value">{parseFloat(min_investment).toFixed(2)} USDT</span>

          <span className="user-count">
            <UserOutlined /> {active_users || 0}
          </span>
        </div>
      </div>

      {/* Featured 배지 */}
      {is_featured && (
        <div className="featured-badge">
          <RiseOutlined /> HOT
        </div>
      )}
    </div>
  );
};

export default TemplateCard;
```

### 4.2 파일: `frontend/src/components/grid/templates/TemplateCard.css`

```css
/* TemplateCard.css - Bitget 스타일 */

.template-card {
  background: #1a1a2e;
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  position: relative;
  border: 1px solid #2d2d44;
  transition: all 0.2s ease;
}

.template-card:hover {
  border-color: #3d3d5c;
  transform: translateY(-2px);
}

.template-card.featured {
  border-color: #00b894;
  box-shadow: 0 0 20px rgba(0, 184, 148, 0.1);
}

/* Header */
.template-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.template-symbol-section {
  flex: 1;
}

.template-symbol {
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 8px 0;
}

.template-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.template-tags .ant-tag {
  margin: 0;
  border-radius: 4px;
  font-size: 11px;
  padding: 2px 6px;
  border: none;
}

.tag-type {
  background: #2d2d44;
  color: #a0a0b0;
}

.tag-direction.long {
  background: rgba(0, 184, 148, 0.2);
  color: #00b894;
}

.tag-direction.short {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
}

.tag-leverage {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.use-button {
  background: #2d2d44;
  border: 1px solid #3d3d5c;
  color: #fff;
  border-radius: 8px;
  padding: 4px 20px;
  height: 32px;
  font-weight: 500;
}

.use-button:hover {
  background: #3d3d5c;
  border-color: #4d4d6c;
  color: #fff;
}

/* Body */
.template-card-body {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.roi-section {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.roi-label {
  font-size: 12px;
  color: #666;
}

.roi-value {
  font-size: 24px;
  font-weight: 700;
}

.roi-value.positive {
  color: #00b894;
}

.roi-value.negative {
  color: #e74c3c;
}

.chart-section {
  flex-shrink: 0;
}

/* Footer */
.template-card-footer {
  border-top: 1px solid #2d2d44;
  padding-top: 12px;
}

.footer-row {
  display: flex;
  align-items: center;
  font-size: 12px;
  margin-bottom: 4px;
}

.footer-label {
  color: #666;
  margin-right: 8px;
}

.footer-value {
  color: #a0a0b0;
  flex: 1;
}

.user-count {
  color: #666;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Featured Badge */
.featured-badge {
  position: absolute;
  top: 12px;
  right: 80px;
  background: linear-gradient(135deg, #00b894, #00cec9);
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 반응형 */
@media (max-width: 480px) {
  .template-card-body {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .chart-section {
    width: 100%;
  }

  .chart-section svg {
    width: 100%;
    height: auto;
  }
}
```

---

## 5. 작업 4: Use 템플릿 모달

### 5.1 파일: `frontend/src/components/grid/templates/UseTemplateModal.jsx`

```jsx
/**
 * UseTemplateModal - 투자금액 입력 모달
 *
 * Bitget 스타일:
 * - 마진 입력
 * - 레버리지 선택
 * - 슬라이더
 * - 가용 잔액 표시
 * - 파라미터 펼치기
 */
import React, { useState, useEffect } from 'react';
import {
  Modal,
  InputNumber,
  Select,
  Slider,
  Button,
  Collapse,
  Descriptions,
  message,
  Spin,
} from 'antd';
import { DownOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { gridTemplateAPI } from '../../../api/gridTemplate';
import GridVisualizer from '../GridVisualizer';
import './UseTemplateModal.css';

const { Panel } = Collapse;
const { Option } = Select;

const LEVERAGE_OPTIONS = [1, 2, 3, 5, 10, 20, 25, 50, 75, 100, 125];

const UseTemplateModal = ({
  visible,
  template,
  onClose,
  onSuccess,
  availableBalance = 0,
}) => {
  const [investmentAmount, setInvestmentAmount] = useState(0);
  const [leverage, setLeverage] = useState(5);
  const [loading, setLoading] = useState(false);
  const [sliderValue, setSliderValue] = useState(0);

  // 템플릿 변경 시 초기값 설정
  useEffect(() => {
    if (template) {
      setInvestmentAmount(parseFloat(template.min_investment) || 0);
      setLeverage(template.leverage || 5);
      updateSliderFromAmount(parseFloat(template.min_investment) || 0);
    }
  }, [template]);

  const updateSliderFromAmount = (amount) => {
    if (availableBalance > 0) {
      setSliderValue((amount / availableBalance) * 100);
    }
  };

  const handleSliderChange = (value) => {
    setSliderValue(value);
    const amount = (availableBalance * value) / 100;
    setInvestmentAmount(Math.max(amount, parseFloat(template?.min_investment || 0)));
  };

  const handleAmountChange = (value) => {
    setInvestmentAmount(value || 0);
    updateSliderFromAmount(value || 0);
  };

  const handleConfirm = async () => {
    if (!template) return;

    // 검증
    const minInv = parseFloat(template.min_investment);
    if (investmentAmount < minInv) {
      message.error(`Minimum investment is ${minInv} USDT`);
      return;
    }

    if (investmentAmount > availableBalance) {
      message.error('Insufficient balance');
      return;
    }

    setLoading(true);
    try {
      const result = await gridTemplateAPI.useTemplate(template.id, {
        investment_amount: investmentAmount,
        leverage: leverage,
      });

      message.success('Grid bot created successfully!');
      onSuccess?.(result);
      onClose();
    } catch (error) {
      console.error('Failed to create bot:', error);
      message.error(error.response?.data?.detail || 'Failed to create bot');
    } finally {
      setLoading(false);
    }
  };

  if (!template) return null;

  const minInvestment = parseFloat(template.min_investment) || 0;

  return (
    <Modal
      open={visible}
      onCancel={onClose}
      footer={null}
      width={500}
      className="use-template-modal"
      title={null}
      closable={true}
    >
      <div className="modal-content">
        {/* 헤더: 템플릿 정보 */}
        <div className="modal-header">
          <h2>{template.symbol}</h2>
          <div className="header-tags">
            <span className="tag">Futures grid</span>
            <span className={`tag ${template.direction}`}>
              {template.direction === 'long' ? 'Long' : 'Short'}
            </span>
            <span className="tag">{template.leverage}x</span>
          </div>
        </div>

        {/* 통계 정보 */}
        <div className="modal-stats">
          <div className="stat-item">
            <span className="stat-label">30D backtested ROI</span>
            <span className={`stat-value ${template.backtest_roi_30d >= 0 ? 'positive' : 'negative'}`}>
              {template.backtest_roi_30d >= 0 ? '+' : ''}{(template.backtest_roi_30d || 0).toFixed(2)}%
            </span>
          </div>
          <div className="stat-item">
            <span className="stat-label">30D max drawdown</span>
            <span className="stat-value">{(template.backtest_max_drawdown || 0).toFixed(2)}%</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Users</span>
            <span className="stat-value">{template.active_users || 0}</span>
          </div>
        </div>

        {/* 투자금액 입력 */}
        <div className="investment-section">
          <h3>Confirm investment amount</h3>

          <div className="margin-input">
            <label>Margin</label>
            <div className="input-row">
              <InputNumber
                value={investmentAmount}
                onChange={handleAmountChange}
                min={minInvestment}
                max={availableBalance}
                step={10}
                precision={2}
                prefix="≥"
                className="amount-input"
              />
              <span className="currency">USDT</span>
              <Select
                value={leverage}
                onChange={setLeverage}
                className="leverage-select"
              >
                {LEVERAGE_OPTIONS.map((lev) => (
                  <Option key={lev} value={lev}>{lev}x</Option>
                ))}
              </Select>
            </div>
          </div>

          {/* 슬라이더 */}
          <div className="slider-section">
            <Slider
              value={sliderValue}
              onChange={handleSliderChange}
              marks={{
                0: '0%',
                25: '25%',
                50: '50%',
                75: '75%',
                100: '100%',
              }}
            />
          </div>

          {/* 가용 잔액 */}
          <div className="balance-row">
            <span className="balance-label">Available</span>
            <span className="balance-value">{availableBalance.toFixed(8)} USDT</span>
          </div>

          <div className="balance-row">
            <span className="balance-label">Estimated liquidation price</span>
            <span className="balance-value">--</span>
          </div>
        </div>

        {/* 파라미터 펼치기 */}
        <Collapse
          ghost
          expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} />}
          className="parameters-collapse"
        >
          <Panel header="Parameters" key="1">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Lower Price">
                {parseFloat(template.lower_price).toFixed(4)} USDT
              </Descriptions.Item>
              <Descriptions.Item label="Upper Price">
                {parseFloat(template.upper_price).toFixed(4)} USDT
              </Descriptions.Item>
              <Descriptions.Item label="Grid Count">
                {template.grid_count} grids
              </Descriptions.Item>
              <Descriptions.Item label="Grid Mode">
                {template.grid_mode}
              </Descriptions.Item>
              <Descriptions.Item label="Min Investment">
                {parseFloat(template.min_investment).toFixed(2)} USDT
              </Descriptions.Item>
            </Descriptions>
          </Panel>
        </Collapse>

        {/* Copy to manual */}
        <div className="copy-to-manual">
          <span>Copy to manual creation</span>
          <span className="arrow">›</span>
        </div>

        {/* 확인 버튼 */}
        <Button
          type="primary"
          block
          size="large"
          onClick={handleConfirm}
          loading={loading}
          disabled={investmentAmount < minInvestment}
          className="confirm-button"
        >
          Confirm
        </Button>
      </div>
    </Modal>
  );
};

export default UseTemplateModal;
```

### 5.2 파일: `frontend/src/components/grid/templates/UseTemplateModal.css`

```css
/* UseTemplateModal.css - Bitget 스타일 */

.use-template-modal .ant-modal-content {
  background: #0d0d1a;
  border-radius: 16px;
  padding: 0;
}

.use-template-modal .ant-modal-close {
  color: #666;
}

.modal-content {
  padding: 24px;
}

/* 헤더 */
.modal-header {
  margin-bottom: 20px;
}

.modal-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  margin: 0 0 12px 0;
}

.header-tags {
  display: flex;
  gap: 8px;
}

.header-tags .tag {
  background: #1a1a2e;
  color: #a0a0b0;
  padding: 4px 10px;
  border-radius: 4px;
  font-size: 12px;
}

.header-tags .tag.long {
  background: rgba(0, 184, 148, 0.2);
  color: #00b894;
}

.header-tags .tag.short {
  background: rgba(231, 76, 60, 0.2);
  color: #e74c3c;
}

/* 통계 */
.modal-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  padding: 16px;
  background: #1a1a2e;
  border-radius: 12px;
  margin-bottom: 24px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.stat-value {
  font-size: 16px;
  font-weight: 600;
  color: #fff;
}

.stat-value.positive {
  color: #00b894;
}

.stat-value.negative {
  color: #e74c3c;
}

/* 투자금액 입력 */
.investment-section h3 {
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  margin: 0 0 16px 0;
}

.margin-input label {
  display: block;
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.input-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.amount-input {
  flex: 1;
  background: #1a1a2e;
  border: 1px solid #2d2d44;
  border-radius: 8px;
}

.amount-input .ant-input-number-input {
  color: #fff;
  font-size: 16px;
}

.currency {
  color: #a0a0b0;
  font-size: 14px;
}

.leverage-select {
  width: 80px;
}

.leverage-select .ant-select-selector {
  background: #1a1a2e !important;
  border: 1px solid #2d2d44 !important;
  border-radius: 8px !important;
  color: #fff !important;
}

/* 슬라이더 */
.slider-section {
  margin: 24px 0;
}

.slider-section .ant-slider-rail {
  background: #2d2d44;
}

.slider-section .ant-slider-track {
  background: #00b894;
}

.slider-section .ant-slider-handle {
  background: #fff;
  border-color: #00b894;
}

.slider-section .ant-slider-mark-text {
  color: #666;
  font-size: 10px;
}

/* 잔액 */
.balance-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.balance-label {
  font-size: 14px;
  color: #666;
}

.balance-value {
  font-size: 14px;
  color: #a0a0b0;
}

/* 파라미터 */
.parameters-collapse {
  margin: 16px 0;
}

.parameters-collapse .ant-collapse-header {
  color: #a0a0b0 !important;
  padding: 12px 0 !important;
}

.parameters-collapse .ant-descriptions-item-label {
  color: #666;
}

.parameters-collapse .ant-descriptions-item-content {
  color: #a0a0b0;
}

/* Copy to manual */
.copy-to-manual {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-top: 1px solid #2d2d44;
  color: #a0a0b0;
  cursor: pointer;
  margin-bottom: 16px;
}

.copy-to-manual:hover {
  color: #fff;
}

.copy-to-manual .arrow {
  font-size: 20px;
}

/* 확인 버튼 */
.confirm-button {
  background: #fff;
  color: #000;
  border: none;
  height: 48px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 8px;
}

.confirm-button:hover {
  background: #f0f0f0;
  color: #000;
}

.confirm-button:disabled {
  background: #2d2d44;
  color: #666;
}
```

---

## 6. 작업 5: 템플릿 목록 컴포넌트

### 6.1 파일: `frontend/src/components/grid/templates/TemplateList.jsx`

```jsx
/**
 * TemplateList - AI 탭의 템플릿 목록
 *
 * 기능:
 * - 템플릿 카드 목록 표시
 * - 코인 필터
 * - Use 버튼 → UseTemplateModal
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Select, Spin, Empty, message } from 'antd';
import { gridTemplateAPI } from '../../../api/gridTemplate';
import TemplateCard from './TemplateCard';
import UseTemplateModal from './UseTemplateModal';
import './TemplateList.css';

const { Option } = Select;

const POPULAR_SYMBOLS = [
  'ALL',
  'BTCUSDT',
  'ETHUSDT',
  'SOLUSDT',
  'BNBUSDT',
  'XRPUSDT',
  'DOGEUSDT',
];

const TemplateList = ({ availableBalance = 0, onBotCreated }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState('ALL');
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);

  // 템플릿 목록 로드
  const loadTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const params = {};
      if (selectedSymbol !== 'ALL') {
        params.symbol = selectedSymbol;
      }

      const response = await gridTemplateAPI.list(params);
      setTemplates(response.data || []);
    } catch (error) {
      console.error('Failed to load templates:', error);
      message.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  }, [selectedSymbol]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  const handleUseClick = (template) => {
    setSelectedTemplate(template);
    setModalVisible(true);
  };

  const handleModalClose = () => {
    setModalVisible(false);
    setSelectedTemplate(null);
  };

  const handleBotCreated = (result) => {
    loadTemplates(); // 통계 업데이트를 위해 새로고침
    onBotCreated?.(result);
  };

  return (
    <div className="template-list">
      {/* 필터 헤더 */}
      <div className="template-list-header">
        <Select
          value={selectedSymbol}
          onChange={setSelectedSymbol}
          className="symbol-filter"
          dropdownClassName="symbol-dropdown"
        >
          {POPULAR_SYMBOLS.map((sym) => (
            <Option key={sym} value={sym}>
              {sym === 'ALL' ? 'All Coins' : sym}
            </Option>
          ))}
        </Select>

        <span className="template-count">
          {templates.length} templates
        </span>
      </div>

      {/* 템플릿 목록 */}
      <div className="template-list-content">
        {loading ? (
          <div className="loading-container">
            <Spin size="large" />
          </div>
        ) : templates.length === 0 ? (
          <Empty
            description="No templates available"
            className="empty-state"
          />
        ) : (
          templates.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              onUse={handleUseClick}
            />
          ))
        )}
      </div>

      {/* Use 모달 */}
      <UseTemplateModal
        visible={modalVisible}
        template={selectedTemplate}
        onClose={handleModalClose}
        onSuccess={handleBotCreated}
        availableBalance={availableBalance}
      />
    </div>
  );
};

export default TemplateList;
```

### 6.2 파일: `frontend/src/components/grid/templates/TemplateList.css`

```css
/* TemplateList.css */

.template-list {
  padding: 16px 0;
}

.template-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 0 4px;
}

.symbol-filter {
  width: 150px;
}

.symbol-filter .ant-select-selector {
  background: #1a1a2e !important;
  border: 1px solid #2d2d44 !important;
  border-radius: 8px !important;
  color: #fff !important;
}

.symbol-dropdown {
  background: #1a1a2e !important;
}

.template-count {
  font-size: 14px;
  color: #666;
}

.template-list-content {
  min-height: 200px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.empty-state {
  margin: 40px 0;
}

.empty-state .ant-empty-description {
  color: #666;
}
```

---

## 7. 작업 6: 템플릿 컴포넌트 Export

### 7.1 파일: `frontend/src/components/grid/templates/index.js`

```javascript
/**
 * Grid Templates Components Export
 */
export { default as TemplateList } from './TemplateList';
export { default as TemplateCard } from './TemplateCard';
export { default as UseTemplateModal } from './UseTemplateModal';
export { default as MiniRoiChart } from './MiniRoiChart';
```

---

## 8. 작업 7: AI/Manual 탭 컴포넌트

### 8.1 파일: `frontend/src/components/grid/GridBotTabs.jsx` (새로 생성)

```jsx
/**
 * GridBotTabs - AI 탭과 Manual 탭 전환
 *
 * AI 탭: 관리자가 만든 템플릿 목록 (TemplateList)
 * Manual 탭: 사용자가 직접 봇 생성 (기존 CreateGridBotModal)
 */
import React, { useState } from 'react';
import { Tabs, Button } from 'antd';
import { PlusOutlined, RobotOutlined, ToolOutlined } from '@ant-design/icons';
import { TemplateList } from './templates';
import CreateGridBotModal from './CreateGridBotModal';
import GridBotCard from './GridBotCard';
import './GridBotTabs.css';

const GridBotTabs = ({
  gridBots = [],            // 사용자의 그리드봇 목록
  availableBalance = 0,     // 가용 잔액
  onBotCreated,            // 봇 생성 완료 콜백
  onBotStart,              // 봇 시작
  onBotStop,               // 봇 중지
  onBotDelete,             // 봇 삭제
  onBotEdit,               // 봇 편집
}) => {
  const [activeTab, setActiveTab] = useState('ai');
  const [manualModalVisible, setManualModalVisible] = useState(false);

  const handleTabChange = (key) => {
    setActiveTab(key);
  };

  const tabItems = [
    {
      key: 'ai',
      label: (
        <span className="tab-label">
          <RobotOutlined />
          AI
        </span>
      ),
      children: (
        <TemplateList
          availableBalance={availableBalance}
          onBotCreated={onBotCreated}
        />
      ),
    },
    {
      key: 'manual',
      label: (
        <span className="tab-label">
          <ToolOutlined />
          Manual
        </span>
      ),
      children: (
        <div className="manual-tab-content">
          {/* 직접 생성 버튼 */}
          <Button
            type="dashed"
            icon={<PlusOutlined />}
            onClick={() => setManualModalVisible(true)}
            className="create-manual-button"
          >
            Create Grid Bot Manually
          </Button>

          {/* 내 그리드봇 목록 (Manual로 생성한 것만 표시할 수도 있음) */}
          {gridBots.length > 0 && (
            <div className="my-bots-section">
              <h4>My Grid Bots</h4>
              {gridBots.map((bot) => (
                <GridBotCard
                  key={bot.id}
                  bot={bot}
                  onStart={() => onBotStart?.(bot.id)}
                  onStop={() => onBotStop?.(bot.id)}
                  onDelete={() => onBotDelete?.(bot.id)}
                  onEdit={() => onBotEdit?.(bot)}
                />
              ))}
            </div>
          )}
        </div>
      ),
    },
  ];

  return (
    <div className="grid-bot-tabs">
      <Tabs
        activeKey={activeTab}
        onChange={handleTabChange}
        items={tabItems}
        className="bitget-tabs"
      />

      {/* Manual 생성 모달 */}
      <CreateGridBotModal
        visible={manualModalVisible}
        onClose={() => setManualModalVisible(false)}
        onSuccess={onBotCreated}
        availableBalance={availableBalance}
      />
    </div>
  );
};

export default GridBotTabs;
```

### 8.2 파일: `frontend/src/components/grid/GridBotTabs.css`

```css
/* GridBotTabs.css - Bitget 스타일 탭 */

.grid-bot-tabs {
  width: 100%;
}

.bitget-tabs .ant-tabs-nav {
  margin-bottom: 0;
}

.bitget-tabs .ant-tabs-nav::before {
  border-bottom: 1px solid #2d2d44;
}

.bitget-tabs .ant-tabs-tab {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 500;
  color: #666;
  margin: 0;
}

.bitget-tabs .ant-tabs-tab:hover {
  color: #a0a0b0;
}

.bitget-tabs .ant-tabs-tab.ant-tabs-tab-active {
  color: #fff;
}

.bitget-tabs .ant-tabs-tab.ant-tabs-tab-active .ant-tabs-tab-btn {
  color: #fff;
}

.bitget-tabs .ant-tabs-ink-bar {
  background: #00b894;
  height: 3px;
}

.tab-label {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Manual 탭 콘텐츠 */
.manual-tab-content {
  padding: 20px 0;
}

.create-manual-button {
  width: 100%;
  height: 60px;
  border: 2px dashed #2d2d44;
  background: transparent;
  color: #a0a0b0;
  font-size: 16px;
  border-radius: 12px;
  margin-bottom: 24px;
}

.create-manual-button:hover {
  border-color: #00b894;
  color: #00b894;
}

.my-bots-section h4 {
  font-size: 16px;
  font-weight: 500;
  color: #fff;
  margin-bottom: 16px;
}
```

---

## 9. 작업 8: 기존 컴포넌트 Export 수정

### 9.1 파일: `frontend/src/components/grid/index.js` (수정)

```javascript
/**
 * Grid Components Export
 */
export { default as GridVisualizer } from './GridVisualizer';
export { default as GridBotCard } from './GridBotCard';
export { default as CreateGridBotModal } from './CreateGridBotModal';
export { default as GridBotTabs } from './GridBotTabs';

// Templates
export * from './templates';
```

---

## 10. 작업 9: BotManagement 페이지 수정

### 10.1 파일 수정: `frontend/src/pages/BotManagement.jsx`

기존 파일에서 그리드봇 섹션을 수정:

```jsx
// import 추가
import { GridBotTabs } from '../components/grid';

// 그리드봇 탭 섹션 (기존 그리드봇 목록 대체)
{activeMainTab === 'grid' && (
  <GridBotTabs
    gridBots={gridBots}
    availableBalance={availableBalance}
    onBotCreated={handleBotCreated}
    onBotStart={handleBotStart}
    onBotStop={handleBotStop}
    onBotDelete={handleBotDelete}
    onBotEdit={handleBotEdit}
  />
)}
```

---

## 11. 테스트 체크리스트

### 11.1 UI 테스트
- [ ] AI 탭에서 템플릿 목록 표시됨
- [ ] 템플릿 카드가 Bitget 스타일과 유사함
- [ ] ROI 미니 차트 렌더링됨
- [ ] Use 버튼 클릭 시 모달 열림
- [ ] 모달에서 투자금액 입력 가능
- [ ] 레버리지 선택 가능
- [ ] 슬라이더 동작함
- [ ] Confirm 버튼으로 봇 생성됨
- [ ] Manual 탭 전환 가능
- [ ] 반응형 디자인 동작

### 11.2 기능 테스트
- [ ] API 연동 정상 동작
- [ ] 최소 투자금액 검증
- [ ] 잔액 부족 시 에러 표시
- [ ] 봇 생성 성공 시 목록 새로고침

---

## 12. 완료 체크리스트

### Phase C 완료 조건
- [ ] gridTemplate.js API 클라이언트 생성됨
- [ ] MiniRoiChart 컴포넌트 생성됨
- [ ] TemplateCard 컴포넌트 생성됨 (Bitget 스타일)
- [ ] UseTemplateModal 컴포넌트 생성됨
- [ ] TemplateList 컴포넌트 생성됨
- [ ] GridBotTabs 컴포넌트 생성됨
- [ ] BotManagement 페이지 수정됨
- [ ] 모든 CSS 스타일 적용됨
- [ ] UI 테스트 통과
- [ ] 기능 테스트 통과

---

## 13. 다음 단계

- **Task D (관리자 페이지)**: 템플릿 관리 UI, 백테스트 실행 UI
