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
} from 'antd';
import { DownOutlined } from '@ant-design/icons';
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
    const [sliderValue, setSliderValue] = useState(0);

    // 템플릿 변경 시 초기값 설정
    useEffect(() => {
        if (template) {
            setInvestmentAmount(parseFloat(template.min_investment) || 0);
            setLeverage(template.leverage || 5);
            updateSliderFromAmount(parseFloat(template.min_investment) || 0);
        }
    }, [template, availableBalance]);

    const updateSliderFromAmount = (amount) => {
        if (availableBalance > 0) {
            setSliderValue(Math.min((amount / availableBalance) * 100, 100));
        }
    };

    const handleSliderChange = (value) => {
        setSliderValue(value);
        const amount = (availableBalance * value) / 100;
        const minInv = parseFloat(template?.min_investment || 0);
        setInvestmentAmount(Math.max(amount, minInv));
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
    const roiValue = template.backtest_roi_30d || 0;

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
                        <span className={`stat-value ${roiValue >= 0 ? 'positive' : 'negative'}`}>
                            {roiValue >= 0 ? '+' : ''}{roiValue.toFixed(2)}%
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
                        <span className="balance-value">{availableBalance.toFixed(2)} USDT</span>
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
