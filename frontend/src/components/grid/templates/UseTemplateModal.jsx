/**
 * UseTemplateModal - 그리드 봇 생성 모달
 * 
 * 라이트 모드 + 한국어 UI
 */
import React, { useState, useEffect } from 'react';
import {
    Modal,
    InputNumber,
    Select,
    Button,
    Collapse,
    Descriptions,
    message,
} from 'antd';
import { DownOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
import { gridTemplateAPI } from '../../../api/gridTemplate';
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

    useEffect(() => {
        if (template) {
            const minInv = Math.ceil(parseFloat(template.min_investment) || 0);
            setInvestmentAmount(minInv);
            setLeverage(template.leverage || 5);
        }
    }, [template]);

    const handleAmountChange = (value) => {
        setInvestmentAmount(Math.floor(value || 0));
    };

    const handleConfirm = async () => {
        if (!template) return;

        const minInv = Math.ceil(parseFloat(template.min_investment));
        if (investmentAmount < minInv) {
            message.error(`최소 ${minInv} USDT 이상 입력해주세요`);
            return;
        }

        if (investmentAmount > availableBalance) {
            message.error('잔액이 부족합니다');
            return;
        }

        setLoading(true);
        try {
            const result = await gridTemplateAPI.useTemplate(template.id, {
                investment_amount: investmentAmount,
                leverage: leverage,
            });

            message.success('🎉 그리드 봇이 생성되었습니다!');
            onSuccess?.(result);
            onClose();
        } catch (error) {
            console.error('Failed to create bot:', error);
            message.error(error.response?.data?.detail || '봇 생성에 실패했습니다. 다시 시도해주세요.');
        } finally {
            setLoading(false);
        }
    };

    if (!template) return null;

    const minInvestment = Math.ceil(parseFloat(template.min_investment) || 0);
    const roiValue = template.backtest_roi_30d || 0;
    const isLong = template.direction === 'long';

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
                {/* 헤더 */}
                <div className="modal-header">
                    <h2>{template.symbol}</h2>
                    <div className="header-tags">
                        <span className="tag">그리드 봇</span>
                        <span className={`tag ${template.direction}`}>
                            {isLong ? <><ArrowUpOutlined /> 롱</> : <><ArrowDownOutlined /> 숏</>}
                        </span>
                        <span className="tag">{template.leverage}배 레버리지</span>
                    </div>
                </div>

                {/* 예상 성과 */}
                <div className="modal-stats">
                    <div className="stat-item">
                        <span className="stat-label">30일 예상 수익률</span>
                        <span className={`stat-value ${roiValue >= 0 ? 'positive' : 'negative'}`}>
                            {roiValue >= 0 ? '+' : ''}{roiValue.toFixed(1)}%
                        </span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">최대 손실</span>
                        <span className="stat-value">-{(template.backtest_max_drawdown || 0).toFixed(1)}%</span>
                    </div>
                    <div className="stat-item">
                        <span className="stat-label">사용자</span>
                        <span className="stat-value">{template.active_users || 0}명</span>
                    </div>
                </div>

                {/* 투자 설정 */}
                <div className="investment-section">
                    <h3>💰 투자 금액 설정</h3>

                    <div className="margin-input">
                        <label>투자할 금액 (USDT)</label>
                        <div className="input-row">
                            <InputNumber
                                value={investmentAmount}
                                onChange={handleAmountChange}
                                min={minInvestment}
                                max={Math.floor(availableBalance)}
                                step={10}
                                precision={0}
                                className="amount-input"
                                style={{ width: '100%' }}
                                placeholder={`최소 ${minInvestment} USDT`}
                            />
                        </div>
                    </div>

                    <div className="margin-input" style={{ marginTop: 16 }}>
                        <label>레버리지 (배율)</label>
                        <div className="input-row">
                            <Select
                                value={leverage}
                                onChange={setLeverage}
                                className="leverage-select"
                                style={{ width: '100%' }}
                            >
                                {LEVERAGE_OPTIONS.map((lev) => (
                                    <Option key={lev} value={lev}>{lev}배</Option>
                                ))}
                            </Select>
                        </div>
                    </div>

                    {/* 사용 가능 잔액 */}
                    <div className="balance-row" style={{ marginTop: 16 }}>
                        <span className="balance-label">사용 가능 금액</span>
                        <span className="balance-value">{Math.floor(availableBalance).toLocaleString()} USDT</span>
                    </div>
                </div>

                {/* 상세 정보 */}
                <Collapse
                    ghost
                    expandIcon={({ isActive }) => <DownOutlined rotate={isActive ? 180 : 0} />}
                    className="parameters-collapse"
                >
                    <Panel header="📋 그리드 설정 보기" key="1">
                        <Descriptions column={1} size="small">
                            <Descriptions.Item label="가격 하한선">
                                {parseFloat(template.lower_price).toLocaleString()} USDT
                            </Descriptions.Item>
                            <Descriptions.Item label="가격 상한선">
                                {parseFloat(template.upper_price).toLocaleString()} USDT
                            </Descriptions.Item>
                            <Descriptions.Item label="그리드 개수">
                                {template.grid_count}개 (자동 분할 매매)
                            </Descriptions.Item>
                            <Descriptions.Item label="그리드 방식">
                                {template.grid_mode === 'arithmetic' ? '등차 (균등 간격)' : '등비 (비율 간격)'}
                            </Descriptions.Item>
                            <Descriptions.Item label="최소 투자금">
                                {minInvestment.toLocaleString()} USDT
                            </Descriptions.Item>
                        </Descriptions>
                    </Panel>
                </Collapse>

                {/* 시작 버튼 */}
                <Button
                    type="primary"
                    block
                    size="large"
                    onClick={handleConfirm}
                    loading={loading}
                    disabled={investmentAmount < minInvestment}
                    className="confirm-button"
                    style={{ marginTop: 20 }}
                >
                    🚀 그리드 봇 시작하기
                </Button>
            </div>
        </Modal>
    );
};

export default UseTemplateModal;
