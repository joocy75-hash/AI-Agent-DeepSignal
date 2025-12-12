/**
 * BacktestRunner - 백테스트 실행 모달 (관리자)
 *
 * 기능:
 * - 백테스트 기간 설정
 * - 캔들 간격 선택
 * - 실행 및 결과 표시
 */
import React, { useState } from 'react';
import {
    Modal,
    Form,
    Select,
    Button,
    Card,
    Statistic,
    Row,
    Col,
    Spin,
    message,
    Progress,
} from 'antd';
import {
    ExperimentOutlined,
    RiseOutlined,
    FallOutlined,
    SwapOutlined,
    TrophyOutlined,
} from '@ant-design/icons';
import { adminGridTemplateAPI } from '../../api/adminGridTemplate';
import { MiniRoiChart } from '../grid/templates';
import './BacktestRunner.css';

const { Option } = Select;

const BacktestRunner = ({
    visible,
    template,
    onClose,
    onComplete,
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
            message.success('Backtest completed successfully!');
            onComplete?.(response);
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
            title={`Backtest: ${template.symbol}`}
            onCancel={handleClose}
            width={600}
            className="backtest-runner-modal"
            footer={
                <div className="modal-footer">
                    <Button onClick={handleClose}>Close</Button>
                    <Button
                        type="primary"
                        icon={<ExperimentOutlined />}
                        onClick={handleRunBacktest}
                        loading={loading}
                    >
                        {result ? 'Run Again' : 'Run Backtest'}
                    </Button>
                </div>
            }
        >
            {/* 템플릿 정보 */}
            <div className="template-info">
                <h4>{template.name || template.symbol}</h4>
                <div className="template-tags">
                    <span className={`tag direction ${template.direction}`}>
                        {template.direction?.toUpperCase()}
                    </span>
                    <span className="tag leverage">{template.leverage}x</span>
                    <span className="tag range">
                        {parseFloat(template.lower_price).toFixed(2)} - {parseFloat(template.upper_price).toFixed(2)}
                    </span>
                </div>
            </div>

            {/* 백테스트 설정 */}
            <Form layout="inline" className="backtest-settings">
                <Form.Item label="Period">
                    <Select value={days} onChange={setDays} style={{ width: 120 }}>
                        <Option value={7}>7 days</Option>
                        <Option value={14}>14 days</Option>
                        <Option value={30}>30 days</Option>
                        <Option value={60}>60 days</Option>
                        <Option value={90}>90 days</Option>
                    </Select>
                </Form.Item>

                <Form.Item label="Candle Interval">
                    <Select value={granularity} onChange={setGranularity} style={{ width: 100 }}>
                        <Option value="1m">1m</Option>
                        <Option value="5m">5m</Option>
                        <Option value="15m">15m</Option>
                        <Option value="1H">1H</Option>
                        <Option value="4H">4H</Option>
                    </Select>
                </Form.Item>
            </Form>

            {/* 로딩 상태 */}
            {loading && (
                <div className="loading-container">
                    <Spin size="large" />
                    <p>Running backtest simulation...</p>
                    <p className="loading-info">This may take a few seconds</p>
                </div>
            )}

            {/* 결과 표시 */}
            {result && !loading && (
                <div className="backtest-results">
                    {/* 주요 지표 */}
                    <Row gutter={[16, 16]}>
                        <Col span={6}>
                            <Card size="small" className="stat-card">
                                <Statistic
                                    title="30D ROI"
                                    value={result.roi_30d}
                                    prefix={result.roi_30d >= 0 ? <RiseOutlined /> : <FallOutlined />}
                                    suffix="%"
                                    valueStyle={{
                                        color: result.roi_30d >= 0 ? '#00b894' : '#e74c3c'
                                    }}
                                    formatter={(value) => (value >= 0 ? '+' : '') + value.toFixed(2)}
                                />
                            </Card>
                        </Col>
                        <Col span={6}>
                            <Card size="small" className="stat-card">
                                <Statistic
                                    title="Max Drawdown"
                                    value={result.max_drawdown}
                                    suffix="%"
                                    valueStyle={{ color: '#e74c3c' }}
                                    formatter={(value) => value.toFixed(2)}
                                />
                            </Card>
                        </Col>
                        <Col span={6}>
                            <Card size="small" className="stat-card">
                                <Statistic
                                    title="Total Trades"
                                    value={result.total_trades}
                                    prefix={<SwapOutlined />}
                                />
                            </Card>
                        </Col>
                        <Col span={6}>
                            <Card size="small" className="stat-card">
                                <Statistic
                                    title="Win Rate"
                                    value={result.win_rate}
                                    prefix={<TrophyOutlined />}
                                    suffix="%"
                                    valueStyle={{
                                        color: result.win_rate >= 50 ? '#00b894' : '#e74c3c'
                                    }}
                                    formatter={(value) => value.toFixed(1)}
                                />
                            </Card>
                        </Col>
                    </Row>

                    {/* 추가 정보 */}
                    <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                        <Col span={8}>
                            <Card size="small" className="stat-card">
                                <Statistic
                                    title="Total Profit"
                                    value={result.total_profit}
                                    prefix="$"
                                    valueStyle={{
                                        color: result.total_profit >= 0 ? '#00b894' : '#e74c3c',
                                        fontSize: 16,
                                    }}
                                    formatter={(value) => (value >= 0 ? '+' : '') + value.toFixed(2)}
                                />
                            </Card>
                        </Col>
                        <Col span={8}>
                            <Card size="small" className="stat-card">
                                <Statistic
                                    title="Avg Profit/Trade"
                                    value={result.avg_profit_per_trade}
                                    prefix="$"
                                    valueStyle={{ fontSize: 16 }}
                                    formatter={(value) => value.toFixed(4)}
                                />
                            </Card>
                        </Col>
                        <Col span={8}>
                            <Card size="small" className="stat-card">
                                <Statistic
                                    title="Grid Cycles"
                                    value={result.grid_cycles_completed}
                                    valueStyle={{ fontSize: 16 }}
                                />
                            </Card>
                        </Col>
                    </Row>

                    {/* ROI 차트 */}
                    {result.daily_roi && result.daily_roi.length > 0 && (
                        <div className="roi-chart-section">
                            <h5>ROI Curve</h5>
                            <MiniRoiChart
                                data={result.daily_roi}
                                width={520}
                                height={80}
                                color={result.roi_30d >= 0 ? '#00b894' : '#e74c3c'}
                            />
                        </div>
                    )}

                    {/* 메타 정보 */}
                    <div className="meta-info">
                        <span>Backtest Period: {result.backtest_days} days</span>
                        <span>•</span>
                        <span>Candles Analyzed: {result.total_candles?.toLocaleString()}</span>
                    </div>
                </div>
            )}
        </Modal>
    );
};

export default BacktestRunner;
