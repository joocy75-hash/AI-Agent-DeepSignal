# 작업 지시서 D: 관리자 페이지 구현

## 📌 담당 영역
- 템플릿 관리 페이지
- 템플릿 생성/수정/삭제 UI
- 백테스트 실행 UI
- 통계 대시보드

---

## 1. 사전 요구사항

### 1.1 의존성
```bash
# Task A의 관리자 API가 동작해야 함
# GET /admin/grid-templates
# POST /admin/grid-templates
# PUT /admin/grid-templates/{id}
# DELETE /admin/grid-templates/{id}
# POST /admin/grid-templates/{id}/backtest
```

### 1.2 필요 파일 위치
```
frontend/src/
├── api/
│   └── adminGridTemplate.js     # 새로 생성
├── pages/
│   └── admin/
│       └── GridTemplateManager.jsx  # 새로 생성
├── components/
│   └── admin/
│       ├── index.js
│       ├── TemplateTable.jsx        # 새로 생성
│       ├── CreateTemplateModal.jsx  # 새로 생성
│       ├── EditTemplateModal.jsx    # 새로 생성
│       ├── BacktestRunner.jsx       # 새로 생성
│       └── TemplateStatsCard.jsx    # 새로 생성
```

---

## 2. 작업 1: 관리자 API 클라이언트

### 2.1 파일: `frontend/src/api/adminGridTemplate.js` (새로 생성)

```javascript
/**
 * Admin Grid Template API Client
 * - 관리자 전용 템플릿 CRUD
 * - 백테스트 실행
 */
import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const adminGridTemplateAPI = {
  /**
   * 모든 템플릿 조회 (관리자)
   * @param {boolean} includeInactive - 비활성 템플릿 포함 여부
   */
  async list(includeInactive = false) {
    const response = await api.get('/admin/grid-templates', {
      params: { include_inactive: includeInactive },
    });
    return response.data;
  },

  /**
   * 템플릿 생성
   * @param {Object} data - 템플릿 데이터
   */
  async create(data) {
    const response = await api.post('/admin/grid-templates', data);
    return response.data;
  },

  /**
   * 템플릿 수정
   * @param {number} templateId
   * @param {Object} data
   */
  async update(templateId, data) {
    const response = await api.put(`/admin/grid-templates/${templateId}`, data);
    return response.data;
  },

  /**
   * 템플릿 삭제 (비활성화)
   * @param {number} templateId
   */
  async delete(templateId) {
    const response = await api.delete(`/admin/grid-templates/${templateId}`);
    return response.data;
  },

  /**
   * 템플릿 공개/비공개 토글
   * @param {number} templateId
   */
  async toggle(templateId) {
    const response = await api.patch(`/admin/grid-templates/${templateId}/toggle`);
    return response.data;
  },

  /**
   * 백테스트 실행
   * @param {number} templateId
   * @param {Object} options - { days, granularity }
   */
  async runBacktest(templateId, options = {}) {
    const params = {
      days: options.days || 30,
      granularity: options.granularity || '5m',
    };
    const response = await api.post(
      `/admin/grid-templates/${templateId}/backtest`,
      null,
      { params }
    );
    return response.data;
  },

  /**
   * 백테스트 미리보기 (템플릿 저장 전)
   * @param {Object} data - 템플릿 설정
   */
  async previewBacktest(data) {
    const response = await api.post('/admin/grid-templates/backtest/preview', data);
    return response.data;
  },
};

export default adminGridTemplateAPI;
```

---

## 3. 작업 2: 템플릿 테이블 컴포넌트

### 3.1 파일: `frontend/src/components/admin/TemplateTable.jsx`

```jsx
/**
 * TemplateTable - 템플릿 목록 테이블 (관리자)
 *
 * 기능:
 * - 템플릿 목록 표시
 * - 정렬/필터
 * - 액션 버튼 (편집, 삭제, 토글, 백테스트)
 */
import React from 'react';
import {
  Table,
  Tag,
  Button,
  Space,
  Switch,
  Tooltip,
  Popconfirm,
  Badge,
} from 'antd';
import {
  EditOutlined,
  DeleteOutlined,
  ExperimentOutlined,
  StarOutlined,
  StarFilled,
} from '@ant-design/icons';
import MiniRoiChart from '../grid/templates/MiniRoiChart';
import './TemplateTable.css';

const TemplateTable = ({
  templates = [],
  loading = false,
  onEdit,
  onDelete,
  onToggle,
  onBacktest,
  onFeatureToggle,
}) => {
  const columns = [
    {
      title: 'Symbol',
      dataIndex: 'symbol',
      key: 'symbol',
      width: 120,
      render: (symbol, record) => (
        <div className="symbol-cell">
          <span className="symbol-text">{symbol}</span>
          <div className="symbol-tags">
            <Tag color={record.direction === 'long' ? 'green' : 'red'}>
              {record.direction.toUpperCase()}
            </Tag>
            <Tag>{record.leverage}X</Tag>
          </div>
        </div>
      ),
    },
    {
      title: 'Grid Settings',
      key: 'gridSettings',
      width: 180,
      render: (_, record) => (
        <div className="grid-settings-cell">
          <div>Range: {parseFloat(record.lower_price).toFixed(2)} - {parseFloat(record.upper_price).toFixed(2)}</div>
          <div>Grids: {record.grid_count} ({record.grid_mode})</div>
        </div>
      ),
    },
    {
      title: '30D ROI',
      dataIndex: 'backtest_roi_30d',
      key: 'roi',
      width: 150,
      sorter: (a, b) => (a.backtest_roi_30d || 0) - (b.backtest_roi_30d || 0),
      render: (roi, record) => (
        <div className="roi-cell">
          {roi !== null && roi !== undefined ? (
            <>
              <span className={`roi-value ${roi >= 0 ? 'positive' : 'negative'}`}>
                {roi >= 0 ? '+' : ''}{roi.toFixed(2)}%
              </span>
              {record.roi_chart && (
                <MiniRoiChart
                  data={record.roi_chart}
                  width={60}
                  height={24}
                  color={roi >= 0 ? '#00b894' : '#e74c3c'}
                />
              )}
            </>
          ) : (
            <span className="no-data">Not tested</span>
          )}
        </div>
      ),
    },
    {
      title: 'MDD',
      dataIndex: 'backtest_max_drawdown',
      key: 'mdd',
      width: 80,
      render: (mdd) => (
        mdd !== null && mdd !== undefined ? (
          <span className="mdd-value">{mdd.toFixed(2)}%</span>
        ) : '-'
      ),
    },
    {
      title: 'Min Investment',
      dataIndex: 'min_investment',
      key: 'minInvestment',
      width: 120,
      render: (val) => `${parseFloat(val).toFixed(2)} USDT`,
    },
    {
      title: 'Users',
      key: 'users',
      width: 100,
      render: (_, record) => (
        <div className="users-cell">
          <div>Active: {record.active_users || 0}</div>
          <div className="total-users">Total: {record.total_users || 0}</div>
        </div>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      width: 100,
      render: (_, record) => (
        <div className="status-cell">
          <Switch
            checked={record.is_active}
            onChange={() => onToggle?.(record.id)}
            checkedChildren="Active"
            unCheckedChildren="Hidden"
          />
          {record.is_featured && (
            <Badge status="success" text="Featured" />
          )}
        </div>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 180,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title={record.is_featured ? 'Unfeature' : 'Feature'}>
            <Button
              type="text"
              icon={record.is_featured ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
              onClick={() => onFeatureToggle?.(record.id, !record.is_featured)}
            />
          </Tooltip>

          <Tooltip title="Run Backtest">
            <Button
              type="text"
              icon={<ExperimentOutlined />}
              onClick={() => onBacktest?.(record)}
            />
          </Tooltip>

          <Tooltip title="Edit">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => onEdit?.(record)}
            />
          </Tooltip>

          <Popconfirm
            title="Delete this template?"
            description="This will hide the template from users."
            onConfirm={() => onDelete?.(record.id)}
            okText="Delete"
            cancelText="Cancel"
          >
            <Tooltip title="Delete">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <Table
      columns={columns}
      dataSource={templates}
      rowKey="id"
      loading={loading}
      pagination={{ pageSize: 20 }}
      scroll={{ x: 1200 }}
      className="template-table"
    />
  );
};

export default TemplateTable;
```

### 3.2 파일: `frontend/src/components/admin/TemplateTable.css`

```css
/* TemplateTable.css */

.template-table .ant-table {
  background: #1a1a2e;
}

.template-table .ant-table-thead > tr > th {
  background: #0d0d1a;
  color: #a0a0b0;
  border-bottom: 1px solid #2d2d44;
}

.template-table .ant-table-tbody > tr > td {
  border-bottom: 1px solid #2d2d44;
  color: #fff;
}

.template-table .ant-table-tbody > tr:hover > td {
  background: #2d2d44;
}

.symbol-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.symbol-text {
  font-weight: 600;
  font-size: 14px;
}

.symbol-tags {
  display: flex;
  gap: 4px;
}

.grid-settings-cell {
  font-size: 12px;
  color: #a0a0b0;
}

.roi-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.roi-value {
  font-weight: 600;
}

.roi-value.positive {
  color: #00b894;
}

.roi-value.negative {
  color: #e74c3c;
}

.no-data {
  color: #666;
  font-style: italic;
}

.mdd-value {
  color: #e74c3c;
}

.users-cell {
  font-size: 12px;
}

.total-users {
  color: #666;
}

.status-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
```

---

## 4. 작업 3: 템플릿 생성 모달

### 4.1 파일: `frontend/src/components/admin/CreateTemplateModal.jsx`

```jsx
/**
 * CreateTemplateModal - 템플릿 생성 모달 (관리자)
 *
 * 단계:
 * 1. 기본 정보 (심볼, 방향, 레버리지)
 * 2. 그리드 설정 (가격 범위, 그리드 수)
 * 3. 추가 정보 (설명, 태그)
 * 4. 백테스트 미리보기 (선택)
 */
import React, { useState } from 'react';
import {
  Modal,
  Form,
  Input,
  InputNumber,
  Select,
  Radio,
  Button,
  Steps,
  Space,
  Divider,
  message,
  Alert,
  Spin,
} from 'antd';
import { ExperimentOutlined } from '@ant-design/icons';
import { adminGridTemplateAPI } from '../../api/adminGridTemplate';
import './CreateTemplateModal.css';

const { Option } = Select;
const { TextArea } = Input;

const POPULAR_SYMBOLS = [
  'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'XRPUSDT',
  'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT',
];

const CreateTemplateModal = ({
  visible,
  onClose,
  onSuccess,
}) => {
  const [form] = Form.useForm();
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [backtestResult, setBacktestResult] = useState(null);

  const steps = [
    { title: 'Basic Info' },
    { title: 'Grid Settings' },
    { title: 'Details' },
    { title: 'Review' },
  ];

  const handleNext = async () => {
    try {
      await form.validateFields();
      setCurrentStep(currentStep + 1);
    } catch (error) {
      // Validation failed
    }
  };

  const handlePrev = () => {
    setCurrentStep(currentStep - 1);
  };

  const handleRunBacktest = async () => {
    const values = form.getFieldsValue();
    setBacktestLoading(true);
    setBacktestResult(null);

    try {
      const result = await adminGridTemplateAPI.previewBacktest({
        symbol: values.symbol,
        direction: values.direction,
        lower_price: values.lower_price.toString(),
        upper_price: values.upper_price.toString(),
        grid_count: values.grid_count,
        grid_mode: values.grid_mode || 'ARITHMETIC',
        leverage: values.leverage || 5,
        investment: values.min_investment.toString(),
        days: 30,
      });

      setBacktestResult(result);
      message.success('Backtest completed!');
    } catch (error) {
      console.error('Backtest failed:', error);
      message.error('Backtest failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setBacktestLoading(false);
    }
  };

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      const templateData = {
        name: values.name,
        symbol: values.symbol,
        direction: values.direction,
        leverage: values.leverage || 5,
        lower_price: values.lower_price.toString(),
        upper_price: values.upper_price.toString(),
        grid_count: values.grid_count,
        grid_mode: values.grid_mode || 'ARITHMETIC',
        min_investment: values.min_investment.toString(),
        recommended_investment: values.recommended_investment?.toString(),
        recommended_period: values.recommended_period || '7-30 days',
        description: values.description,
        tags: values.tags || [],
        is_active: true,
        is_featured: values.is_featured || false,
      };

      const result = await adminGridTemplateAPI.create(templateData);
      message.success('Template created successfully!');

      // 백테스트 결과가 있으면 자동 저장
      if (backtestResult) {
        try {
          await adminGridTemplateAPI.runBacktest(result.id, { days: 30 });
        } catch (e) {
          console.warn('Auto backtest failed:', e);
        }
      }

      onSuccess?.(result);
      handleClose();
    } catch (error) {
      console.error('Create failed:', error);
      message.error('Failed to create template');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    form.resetFields();
    setCurrentStep(0);
    setBacktestResult(null);
    onClose();
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="step-content">
            <Form.Item
              name="name"
              label="Template Name"
              rules={[{ required: true, message: 'Please enter template name' }]}
            >
              <Input placeholder="e.g., SOL Short Grid - High Yield" />
            </Form.Item>

            <Form.Item
              name="symbol"
              label="Symbol"
              rules={[{ required: true, message: 'Please select symbol' }]}
            >
              <Select placeholder="Select trading pair">
                {POPULAR_SYMBOLS.map((sym) => (
                  <Option key={sym} value={sym}>{sym}</Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="direction"
              label="Position Direction"
              rules={[{ required: true, message: 'Please select direction' }]}
            >
              <Radio.Group>
                <Radio.Button value="long">Long</Radio.Button>
                <Radio.Button value="short">Short</Radio.Button>
              </Radio.Group>
            </Form.Item>

            <Form.Item
              name="leverage"
              label="Leverage"
              initialValue={5}
            >
              <Select>
                {[1, 2, 3, 5, 10, 20, 25, 50, 75, 100, 125].map((lev) => (
                  <Option key={lev} value={lev}>{lev}x</Option>
                ))}
              </Select>
            </Form.Item>
          </div>
        );

      case 1:
        return (
          <div className="step-content">
            <Form.Item
              name="lower_price"
              label="Lower Price"
              rules={[{ required: true, message: 'Please enter lower price' }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="e.g., 120.00"
                min={0}
                step={0.01}
                precision={8}
              />
            </Form.Item>

            <Form.Item
              name="upper_price"
              label="Upper Price"
              rules={[{ required: true, message: 'Please enter upper price' }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="e.g., 150.00"
                min={0}
                step={0.01}
                precision={8}
              />
            </Form.Item>

            <Form.Item
              name="grid_count"
              label="Grid Count"
              rules={[{ required: true, message: 'Please enter grid count' }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="e.g., 30"
                min={2}
                max={200}
              />
            </Form.Item>

            <Form.Item
              name="grid_mode"
              label="Grid Mode"
              initialValue="ARITHMETIC"
            >
              <Radio.Group>
                <Radio.Button value="ARITHMETIC">Arithmetic</Radio.Button>
                <Radio.Button value="GEOMETRIC">Geometric</Radio.Button>
              </Radio.Group>
            </Form.Item>

            <Form.Item
              name="min_investment"
              label="Minimum Investment (USDT)"
              rules={[{ required: true, message: 'Please enter minimum investment' }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="e.g., 384.21"
                min={5}
                step={10}
                precision={2}
              />
            </Form.Item>

            <Form.Item
              name="recommended_investment"
              label="Recommended Investment (USDT)"
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="e.g., 1000.00"
                min={5}
                step={10}
                precision={2}
              />
            </Form.Item>
          </div>
        );

      case 2:
        return (
          <div className="step-content">
            <Form.Item
              name="recommended_period"
              label="Recommended Investment Period"
              initialValue="7-30 days"
            >
              <Select>
                <Option value="1-7 days">1-7 days</Option>
                <Option value="7-30 days">7-30 days</Option>
                <Option value="30-90 days">30-90 days</Option>
                <Option value="90+ days">90+ days</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="description"
              label="Description"
            >
              <TextArea
                rows={4}
                placeholder="Describe the strategy and its characteristics..."
              />
            </Form.Item>

            <Form.Item
              name="tags"
              label="Tags"
            >
              <Select mode="tags" placeholder="Add tags">
                <Option value="stable">Stable</Option>
                <Option value="high-yield">High Yield</Option>
                <Option value="low-risk">Low Risk</Option>
                <Option value="volatile">Volatile</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="is_featured"
              label="Featured"
              valuePropName="checked"
            >
              <Radio.Group>
                <Radio value={true}>Yes (Show on top)</Radio>
                <Radio value={false}>No</Radio>
              </Radio.Group>
            </Form.Item>
          </div>
        );

      case 3:
        const values = form.getFieldsValue();
        return (
          <div className="step-content review-step">
            <h4>Review Template</h4>

            <div className="review-section">
              <h5>Basic Info</h5>
              <p><strong>Name:</strong> {values.name}</p>
              <p><strong>Symbol:</strong> {values.symbol}</p>
              <p><strong>Direction:</strong> {values.direction?.toUpperCase()}</p>
              <p><strong>Leverage:</strong> {values.leverage}x</p>
            </div>

            <div className="review-section">
              <h5>Grid Settings</h5>
              <p><strong>Price Range:</strong> {values.lower_price} - {values.upper_price}</p>
              <p><strong>Grid Count:</strong> {values.grid_count}</p>
              <p><strong>Grid Mode:</strong> {values.grid_mode}</p>
              <p><strong>Min Investment:</strong> {values.min_investment} USDT</p>
            </div>

            <Divider />

            {/* 백테스트 섹션 */}
            <div className="backtest-section">
              <h5>Backtest Preview</h5>
              <Button
                type="primary"
                icon={<ExperimentOutlined />}
                onClick={handleRunBacktest}
                loading={backtestLoading}
                disabled={!values.symbol || !values.lower_price || !values.upper_price}
              >
                Run 30-Day Backtest
              </Button>

              {backtestLoading && (
                <div className="backtest-loading">
                  <Spin tip="Running backtest..." />
                </div>
              )}

              {backtestResult && (
                <Alert
                  type="success"
                  className="backtest-result"
                  message="Backtest Result"
                  description={
                    <div>
                      <p><strong>30D ROI:</strong> {backtestResult.roi_30d?.toFixed(2)}%</p>
                      <p><strong>Max Drawdown:</strong> {backtestResult.max_drawdown?.toFixed(2)}%</p>
                      <p><strong>Total Trades:</strong> {backtestResult.total_trades}</p>
                      <p><strong>Win Rate:</strong> {backtestResult.win_rate?.toFixed(2)}%</p>
                    </div>
                  }
                />
              )}
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Modal
      open={visible}
      onCancel={handleClose}
      title="Create Grid Bot Template"
      width={600}
      footer={null}
      className="create-template-modal"
    >
      <Steps current={currentStep} items={steps} className="create-steps" />

      <Form
        form={form}
        layout="vertical"
        className="create-form"
      >
        {renderStep()}
      </Form>

      <div className="modal-footer">
        <Space>
          {currentStep > 0 && (
            <Button onClick={handlePrev}>Previous</Button>
          )}
          {currentStep < steps.length - 1 && (
            <Button type="primary" onClick={handleNext}>Next</Button>
          )}
          {currentStep === steps.length - 1 && (
            <Button
              type="primary"
              onClick={handleSubmit}
              loading={loading}
            >
              Create Template
            </Button>
          )}
        </Space>
      </div>
    </Modal>
  );
};

export default CreateTemplateModal;
```

### 4.2 파일: `frontend/src/components/admin/CreateTemplateModal.css`

```css
/* CreateTemplateModal.css */

.create-template-modal .ant-modal-content {
  background: #1a1a2e;
}

.create-template-modal .ant-modal-header {
  background: #1a1a2e;
  border-bottom: 1px solid #2d2d44;
}

.create-template-modal .ant-modal-title {
  color: #fff;
}

.create-steps {
  margin-bottom: 24px;
}

.create-steps .ant-steps-item-title {
  color: #a0a0b0 !important;
}

.create-steps .ant-steps-item-finish .ant-steps-item-title {
  color: #00b894 !important;
}

.create-form {
  min-height: 300px;
}

.step-content {
  padding: 16px 0;
}

.review-step h4 {
  color: #fff;
  margin-bottom: 16px;
}

.review-section {
  margin-bottom: 16px;
}

.review-section h5 {
  color: #00b894;
  margin-bottom: 8px;
}

.review-section p {
  color: #a0a0b0;
  margin: 4px 0;
}

.backtest-section {
  margin-top: 16px;
}

.backtest-section h5 {
  color: #fff;
  margin-bottom: 12px;
}

.backtest-loading {
  margin-top: 16px;
  text-align: center;
}

.backtest-result {
  margin-top: 16px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #2d2d44;
}
```

---

## 5. 작업 4: 백테스트 실행 모달

### 5.1 파일: `frontend/src/components/admin/BacktestRunner.jsx`

```jsx
/**
 * BacktestRunner - 백테스트 실행 및 결과 표시
 */
import React, { useState } from 'react';
import {
  Modal,
  Form,
  Select,
  InputNumber,
  Button,
  Progress,
  Descriptions,
  Statistic,
  Row,
  Col,
  message,
} from 'antd';
import {
  LineChartOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons';
import { adminGridTemplateAPI } from '../../api/adminGridTemplate';
import MiniRoiChart from '../grid/templates/MiniRoiChart';
import './BacktestRunner.css';

const { Option } = Select;

const BacktestRunner = ({
  visible,
  template,
  onClose,
  onSuccess,
}) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [days, setDays] = useState(30);
  const [granularity, setGranularity] = useState('5m');

  const handleRunBacktest = async () => {
    if (!template) return;

    setLoading(true);
    setResult(null);

    try {
      const response = await adminGridTemplateAPI.runBacktest(template.id, {
        days,
        granularity,
      });

      setResult(response);
      message.success('Backtest completed and saved!');
      onSuccess?.(response);
    } catch (error) {
      console.error('Backtest failed:', error);
      message.error('Backtest failed: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setResult(null);
    onClose();
  };

  if (!template) return null;

  return (
    <Modal
      open={visible}
      onCancel={handleClose}
      title={`Run Backtest - ${template.symbol}`}
      width={700}
      footer={null}
      className="backtest-runner-modal"
    >
      <div className="backtest-content">
        {/* 템플릿 정보 */}
        <div className="template-info">
          <Descriptions column={2} size="small">
            <Descriptions.Item label="Symbol">{template.symbol}</Descriptions.Item>
            <Descriptions.Item label="Direction">{template.direction?.toUpperCase()}</Descriptions.Item>
            <Descriptions.Item label="Leverage">{template.leverage}x</Descriptions.Item>
            <Descriptions.Item label="Grids">{template.grid_count}</Descriptions.Item>
            <Descriptions.Item label="Price Range">
              {parseFloat(template.lower_price).toFixed(4)} - {parseFloat(template.upper_price).toFixed(4)}
            </Descriptions.Item>
            <Descriptions.Item label="Min Investment">
              {parseFloat(template.min_investment).toFixed(2)} USDT
            </Descriptions.Item>
          </Descriptions>
        </div>

        {/* 백테스트 설정 */}
        <div className="backtest-settings">
          <h4>Backtest Settings</h4>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item label="Period (Days)">
                <InputNumber
                  value={days}
                  onChange={setDays}
                  min={7}
                  max={90}
                  style={{ width: '100%' }}
                />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Candle Interval">
                <Select value={granularity} onChange={setGranularity}>
                  <Option value="1m">1 minute</Option>
                  <Option value="5m">5 minutes</Option>
                  <Option value="15m">15 minutes</Option>
                  <Option value="30m">30 minutes</Option>
                  <Option value="1H">1 hour</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Button
            type="primary"
            icon={<LineChartOutlined />}
            onClick={handleRunBacktest}
            loading={loading}
            block
          >
            {loading ? 'Running Backtest...' : 'Run Backtest'}
          </Button>
        </div>

        {/* 백테스트 결과 */}
        {result && (
          <div className="backtest-result">
            <h4>Results</h4>

            <Row gutter={[16, 16]}>
              <Col span={8}>
                <Statistic
                  title="30D ROI"
                  value={result.roi_30d}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: result.roi_30d >= 0 ? '#00b894' : '#e74c3c' }}
                  prefix={result.roi_30d >= 0 ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Max Drawdown"
                  value={result.max_drawdown}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: '#e74c3c' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Win Rate"
                  value={result.win_rate}
                  precision={2}
                  suffix="%"
                  valueStyle={{ color: result.win_rate >= 50 ? '#00b894' : '#faad14' }}
                />
              </Col>
            </Row>

            <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
              <Col span={8}>
                <Statistic
                  title="Total Trades"
                  value={result.total_trades}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Total Profit"
                  value={result.total_profit}
                  precision={2}
                  suffix=" USDT"
                  valueStyle={{ color: result.total_profit >= 0 ? '#00b894' : '#e74c3c' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Avg Profit/Trade"
                  value={result.avg_profit_per_trade}
                  precision={4}
                  suffix=" USDT"
                />
              </Col>
            </Row>

            {/* ROI 차트 */}
            {result.daily_roi && result.daily_roi.length > 0 && (
              <div className="roi-chart-section">
                <h5>Cumulative ROI Chart</h5>
                <MiniRoiChart
                  data={result.daily_roi}
                  width={600}
                  height={150}
                  color={result.roi_30d >= 0 ? '#00b894' : '#e74c3c'}
                />
              </div>
            )}

            <div className="result-meta">
              <span>Candles analyzed: {result.total_candles}</span>
              <span>Grid cycles: {result.grid_cycles_completed}</span>
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
};

export default BacktestRunner;
```

### 5.2 파일: `frontend/src/components/admin/BacktestRunner.css`

```css
/* BacktestRunner.css */

.backtest-runner-modal .ant-modal-content {
  background: #1a1a2e;
}

.backtest-content {
  padding: 16px 0;
}

.template-info {
  background: #0d0d1a;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 24px;
}

.backtest-settings {
  margin-bottom: 24px;
}

.backtest-settings h4 {
  color: #fff;
  margin-bottom: 16px;
}

.backtest-result {
  background: #0d0d1a;
  padding: 24px;
  border-radius: 8px;
  margin-top: 24px;
}

.backtest-result h4 {
  color: #00b894;
  margin-bottom: 16px;
}

.roi-chart-section {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #2d2d44;
}

.roi-chart-section h5 {
  color: #a0a0b0;
  margin-bottom: 12px;
}

.result-meta {
  display: flex;
  gap: 24px;
  margin-top: 16px;
  font-size: 12px;
  color: #666;
}
```

---

## 6. 작업 5: 관리자 페이지

### 6.1 파일: `frontend/src/pages/admin/GridTemplateManager.jsx`

```jsx
/**
 * GridTemplateManager - 그리드봇 템플릿 관리 페이지 (관리자)
 */
import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, Space, Switch, message, Breadcrumb } from 'antd';
import {
  PlusOutlined,
  ReloadOutlined,
  HomeOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import { Link } from 'react-router-dom';
import { adminGridTemplateAPI } from '../../api/adminGridTemplate';
import TemplateTable from '../../components/admin/TemplateTable';
import CreateTemplateModal from '../../components/admin/CreateTemplateModal';
import BacktestRunner from '../../components/admin/BacktestRunner';
import './GridTemplateManager.css';

const GridTemplateManager = () => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [includeInactive, setIncludeInactive] = useState(false);

  // 모달 상태
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [backtestTemplate, setBacktestTemplate] = useState(null);

  // 템플릿 목록 로드
  const loadTemplates = useCallback(async () => {
    setLoading(true);
    try {
      const data = await adminGridTemplateAPI.list(includeInactive);
      setTemplates(data);
    } catch (error) {
      console.error('Failed to load templates:', error);
      message.error('Failed to load templates');
    } finally {
      setLoading(false);
    }
  }, [includeInactive]);

  useEffect(() => {
    loadTemplates();
  }, [loadTemplates]);

  // 핸들러
  const handleEdit = (template) => {
    setEditingTemplate(template);
    // EditTemplateModal 열기 (CreateTemplateModal 재사용 가능)
  };

  const handleDelete = async (templateId) => {
    try {
      await adminGridTemplateAPI.delete(templateId);
      message.success('Template deleted');
      loadTemplates();
    } catch (error) {
      message.error('Failed to delete template');
    }
  };

  const handleToggle = async (templateId) => {
    try {
      const result = await adminGridTemplateAPI.toggle(templateId);
      message.success(result.message);
      loadTemplates();
    } catch (error) {
      message.error('Failed to toggle template');
    }
  };

  const handleBacktest = (template) => {
    setBacktestTemplate(template);
  };

  const handleFeatureToggle = async (templateId, isFeatured) => {
    try {
      await adminGridTemplateAPI.update(templateId, { is_featured: isFeatured });
      message.success(isFeatured ? 'Template featured' : 'Template unfeatured');
      loadTemplates();
    } catch (error) {
      message.error('Failed to update template');
    }
  };

  const handleCreateSuccess = () => {
    setCreateModalVisible(false);
    loadTemplates();
  };

  const handleBacktestSuccess = () => {
    loadTemplates();
  };

  // 통계 계산
  const stats = {
    total: templates.length,
    active: templates.filter((t) => t.is_active).length,
    featured: templates.filter((t) => t.is_featured).length,
    totalUsers: templates.reduce((sum, t) => sum + (t.active_users || 0), 0),
  };

  return (
    <div className="grid-template-manager">
      {/* 브레드크럼 */}
      <Breadcrumb className="page-breadcrumb">
        <Breadcrumb.Item>
          <Link to="/"><HomeOutlined /></Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>
          <Link to="/admin">Admin</Link>
        </Breadcrumb.Item>
        <Breadcrumb.Item>Grid Templates</Breadcrumb.Item>
      </Breadcrumb>

      {/* 페이지 헤더 */}
      <div className="page-header">
        <div className="header-title">
          <AppstoreOutlined />
          <h1>Grid Bot Templates</h1>
        </div>
        <Space>
          <span className="filter-label">Show inactive:</span>
          <Switch
            checked={includeInactive}
            onChange={setIncludeInactive}
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={loadTemplates}
          >
            Refresh
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => setCreateModalVisible(true)}
          >
            Create Template
          </Button>
        </Space>
      </div>

      {/* 통계 카드 */}
      <div className="stats-row">
        <Card className="stat-card">
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Total Templates</div>
        </Card>
        <Card className="stat-card">
          <div className="stat-value">{stats.active}</div>
          <div className="stat-label">Active</div>
        </Card>
        <Card className="stat-card">
          <div className="stat-value">{stats.featured}</div>
          <div className="stat-label">Featured</div>
        </Card>
        <Card className="stat-card">
          <div className="stat-value">{stats.totalUsers}</div>
          <div className="stat-label">Active Users</div>
        </Card>
      </div>

      {/* 템플릿 테이블 */}
      <Card className="templates-card">
        <TemplateTable
          templates={templates}
          loading={loading}
          onEdit={handleEdit}
          onDelete={handleDelete}
          onToggle={handleToggle}
          onBacktest={handleBacktest}
          onFeatureToggle={handleFeatureToggle}
        />
      </Card>

      {/* 모달들 */}
      <CreateTemplateModal
        visible={createModalVisible}
        onClose={() => setCreateModalVisible(false)}
        onSuccess={handleCreateSuccess}
      />

      <BacktestRunner
        visible={!!backtestTemplate}
        template={backtestTemplate}
        onClose={() => setBacktestTemplate(null)}
        onSuccess={handleBacktestSuccess}
      />
    </div>
  );
};

export default GridTemplateManager;
```

### 6.2 파일: `frontend/src/pages/admin/GridTemplateManager.css`

```css
/* GridTemplateManager.css */

.grid-template-manager {
  padding: 24px;
  min-height: 100vh;
  background: #0d0d1a;
}

.page-breadcrumb {
  margin-bottom: 16px;
}

.page-breadcrumb .ant-breadcrumb-link,
.page-breadcrumb .ant-breadcrumb-separator {
  color: #a0a0b0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title h1 {
  font-size: 24px;
  font-weight: 600;
  color: #fff;
  margin: 0;
}

.header-title .anticon {
  font-size: 24px;
  color: #00b894;
}

.filter-label {
  color: #a0a0b0;
  font-size: 14px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #1a1a2e;
  border: 1px solid #2d2d44;
  border-radius: 12px;
}

.stat-card .ant-card-body {
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.templates-card {
  background: #1a1a2e;
  border: 1px solid #2d2d44;
  border-radius: 12px;
}

.templates-card .ant-card-body {
  padding: 0;
}

/* 반응형 */
@media (max-width: 1024px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}
```

---

## 7. 작업 6: 컴포넌트 Export

### 7.1 파일: `frontend/src/components/admin/index.js`

```javascript
/**
 * Admin Components Export
 */
export { default as TemplateTable } from './TemplateTable';
export { default as CreateTemplateModal } from './CreateTemplateModal';
export { default as BacktestRunner } from './BacktestRunner';
```

---

## 8. 작업 7: 라우팅 설정

### 8.1 파일 수정: `frontend/src/App.jsx` (또는 라우터 설정 파일)

```jsx
// import 추가
import GridTemplateManager from './pages/admin/GridTemplateManager';

// 라우트 추가 (관리자 전용)
<Route
  path="/admin/grid-templates"
  element={
    <ProtectedRoute requireAdmin>
      <GridTemplateManager />
    </ProtectedRoute>
  }
/>
```

---

## 9. 테스트 체크리스트

### 9.1 기능 테스트
- [ ] 관리자 로그인 후 /admin/grid-templates 접근 가능
- [ ] 템플릿 목록 표시됨
- [ ] 템플릿 생성 모달 동작
- [ ] 4단계 폼 이동 정상
- [ ] 백테스트 미리보기 동작
- [ ] 템플릿 생성 성공
- [ ] 템플릿 편집 가능
- [ ] 템플릿 삭제 가능
- [ ] 활성/비활성 토글 동작
- [ ] Featured 토글 동작
- [ ] 백테스트 실행 및 결과 표시
- [ ] 결과가 템플릿에 저장됨

### 9.2 UI 테스트
- [ ] 다크 테마 일관성
- [ ] 테이블 정렬/페이지네이션 동작
- [ ] 통계 카드 표시됨
- [ ] 로딩 상태 표시됨
- [ ] 에러 메시지 표시됨

---

## 10. 완료 체크리스트

### Phase D 완료 조건
- [ ] adminGridTemplate.js API 클라이언트 생성됨
- [ ] TemplateTable 컴포넌트 생성됨
- [ ] CreateTemplateModal 컴포넌트 생성됨
- [ ] BacktestRunner 컴포넌트 생성됨
- [ ] GridTemplateManager 페이지 생성됨
- [ ] 라우팅 설정됨
- [ ] 모든 CSS 스타일 적용됨
- [ ] 기능 테스트 통과
- [ ] UI 테스트 통과

---

## 11. 전체 통합 테스트

모든 Task 완료 후:

1. **관리자 플로우**
   - 관리자 로그인
   - /admin/grid-templates 이동
   - 템플릿 생성 (SOL Short Grid)
   - 백테스트 실행
   - Featured 설정
   - 활성화 확인

2. **사용자 플로우**
   - 일반 사용자 로그인
   - BotManagement 페이지 이동
   - AI 탭 선택
   - 생성된 템플릿 확인
   - Use 버튼 클릭
   - 투자금액 입력
   - 봇 생성 확인
   - 봇 시작 테스트

3. **실시간 업데이트**
   - 템플릿 active_users 증가 확인
   - total_funds_in_use 증가 확인
