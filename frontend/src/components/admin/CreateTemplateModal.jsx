/**
 * CreateTemplateModal - 템플릿 생성 모달 (관리자)
 *
 * 단계:
 * 1. 기본 정보 (심볼, 방향, 레버리지)
 * 2. 그리드 설정 (가격 범위, 그리드 수)
 * 3. 추가 정보 (설명, 태그)
 * 4. 백테스트 미리보기 (선택)
 */
import React, { useState, useEffect } from 'react';
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
    Card,
    Statistic,
    Row,
    Col,
} from 'antd';
import { ExperimentOutlined, CheckCircleOutlined } from '@ant-design/icons';
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
    editTemplate = null,  // 편집 모드일 때 기존 템플릿 데이터
}) => {
    const [form] = Form.useForm();
    const [currentStep, setCurrentStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [backtestLoading, setBacktestLoading] = useState(false);
    const [backtestResult, setBacktestResult] = useState(null);

    const isEdit = !!editTemplate;

    // 편집 모드일 때 초기값 설정
    useEffect(() => {
        if (visible && editTemplate) {
            form.setFieldsValue({
                name: editTemplate.name,
                symbol: editTemplate.symbol,
                direction: editTemplate.direction,
                leverage: editTemplate.leverage,
                lower_price: parseFloat(editTemplate.lower_price),
                upper_price: parseFloat(editTemplate.upper_price),
                grid_count: editTemplate.grid_count,
                grid_mode: editTemplate.grid_mode,
                min_investment: parseFloat(editTemplate.min_investment),
                recommended_investment: editTemplate.recommended_investment
                    ? parseFloat(editTemplate.recommended_investment)
                    : null,
                recommended_period: editTemplate.recommended_period,
                description: editTemplate.description,
                tags: editTemplate.tags,
                is_featured: editTemplate.is_featured,
            });
        }
    }, [visible, editTemplate, form]);

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

            let result;
            if (isEdit) {
                result = await adminGridTemplateAPI.update(editTemplate.id, templateData);
                message.success('Template updated successfully!');
            } else {
                result = await adminGridTemplateAPI.create(templateData);
                message.success('Template created successfully!');
            }

            // 백테스트 결과가 있으면 자동 저장
            if (backtestResult && !isEdit) {
                try {
                    await adminGridTemplateAPI.runBacktest(result.id, { days: 30 });
                } catch (e) {
                    console.warn('Auto backtest failed:', e);
                }
            }

            onSuccess?.(result);
            handleClose();
        } catch (error) {
            console.error('Save failed:', error);
            message.error('Failed to save template');
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

                        <div className="backtest-section">
                            <h5>Backtest Preview</h5>
                            <Button
                                type="primary"
                                icon={<ExperimentOutlined />}
                                onClick={handleRunBacktest}
                                loading={backtestLoading}
                                disabled={backtestResult}
                            >
                                {backtestResult ? 'Backtest Complete' : 'Run Backtest'}
                            </Button>

                            {backtestLoading && (
                                <div className="backtest-loading">
                                    <Spin /> Running backtest...
                                </div>
                            )}

                            {backtestResult && (
                                <Card className="backtest-result-card">
                                    <Row gutter={16}>
                                        <Col span={6}>
                                            <Statistic
                                                title="30D ROI"
                                                value={backtestResult.roi_30d}
                                                suffix="%"
                                                valueStyle={{
                                                    color: backtestResult.roi_30d >= 0 ? '#00b894' : '#e74c3c'
                                                }}
                                                prefix={backtestResult.roi_30d >= 0 ? '+' : ''}
                                            />
                                        </Col>
                                        <Col span={6}>
                                            <Statistic
                                                title="Max Drawdown"
                                                value={backtestResult.max_drawdown}
                                                suffix="%"
                                                valueStyle={{ color: '#e74c3c' }}
                                            />
                                        </Col>
                                        <Col span={6}>
                                            <Statistic
                                                title="Total Trades"
                                                value={backtestResult.total_trades}
                                            />
                                        </Col>
                                        <Col span={6}>
                                            <Statistic
                                                title="Win Rate"
                                                value={backtestResult.win_rate}
                                                suffix="%"
                                            />
                                        </Col>
                                    </Row>
                                </Card>
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
            title={isEdit ? 'Edit Template' : 'Create New Template'}
            onCancel={handleClose}
            width={700}
            className="create-template-modal"
            footer={
                <div className="modal-footer">
                    {currentStep > 0 && (
                        <Button onClick={handlePrev}>
                            Previous
                        </Button>
                    )}
                    {currentStep < steps.length - 1 ? (
                        <Button type="primary" onClick={handleNext}>
                            Next
                        </Button>
                    ) : (
                        <Button
                            type="primary"
                            onClick={handleSubmit}
                            loading={loading}
                            icon={<CheckCircleOutlined />}
                        >
                            {isEdit ? 'Save Changes' : 'Create Template'}
                        </Button>
                    )}
                </div>
            }
        >
            <Steps
                current={currentStep}
                items={steps}
                className="template-steps"
            />

            <Form
                form={form}
                layout="vertical"
                className="template-form"
            >
                {renderStep()}
            </Form>
        </Modal>
    );
};

export default CreateTemplateModal;
