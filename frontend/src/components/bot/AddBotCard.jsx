/**
 * AddBotCard Component
 * 
 * 비트겟 스타일의 새 봇 추가 카드
 * 클릭 시 봇 생성 모달 표시
 */

import { useState } from 'react';
import {
    Card,
    Modal,
    Form,
    Input,
    Select,
    InputNumber,
    Switch,
    Button,
    Space,
    Typography,
    Divider,
    message,
    Tooltip,
    Slider
} from 'antd';
import {
    PlusOutlined,
    RobotOutlined,
    ThunderboltOutlined,
    LineChartOutlined,
    InfoCircleOutlined,
    DollarOutlined,
    PercentageOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const SYMBOLS = [
    { value: 'BTCUSDT', label: 'BTC/USDT' },
    { value: 'ETHUSDT', label: 'ETH/USDT' },
    { value: 'BNBUSDT', label: 'BNB/USDT' },
    { value: 'SOLUSDT', label: 'SOL/USDT' },
    { value: 'XRPUSDT', label: 'XRP/USDT' },
    { value: 'ADAUSDT', label: 'ADA/USDT' },
    { value: 'DOGEUSDT', label: 'DOGE/USDT' },
];

export default function AddBotCard({
    maxAllocation = 100,
    strategies = [],
    onCreate,
    style = {}
}) {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [botType, setBotType] = useState('ai_trend');
    const [form] = Form.useForm();

    const handleOpen = () => {
        form.resetFields();
        setBotType('ai_trend');
        setIsModalOpen(true);
    };

    const handleClose = () => {
        setIsModalOpen(false);
        form.resetFields();
    };

    const handleSubmit = async (values) => {
        setLoading(true);
        try {
            await onCreate?.({
                ...values,
                bot_type: botType,
            });
            message.success(`봇 "${values.name}"이(가) 생성되었습니다!`);
            handleClose();
        } catch (err) {
            message.error(err.response?.data?.detail || err.message || '봇 생성 실패');
        } finally {
            setLoading(false);
        }
    };

    return (
        <>
            {/* Add Bot 카드 */}
            <Card
                hoverable
                onClick={handleOpen}
                style={{
                    borderRadius: 16,
                    border: '2px dashed rgba(0, 168, 255, 0.3)',
                    background: 'linear-gradient(180deg, rgba(0, 168, 255, 0.05) 0%, rgba(124, 84, 255, 0.05) 100%)',
                    minHeight: 360,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.3s ease',
                    ...style
                }}
                styles={{
                    body: {
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        justifyContent: 'center',
                        width: '100%',
                        padding: '40px 20px',
                    }
                }}
            >
                <div style={{
                    width: 64,
                    height: 64,
                    borderRadius: '50%',
                    background: 'linear-gradient(135deg, #00A8FF 0%, #7C54FF 100%)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    marginBottom: 16,
                    boxShadow: '0 4px 20px rgba(0, 168, 255, 0.3)',
                }}>
                    <PlusOutlined style={{ fontSize: 28, color: '#fff' }} />
                </div>
                <Text strong style={{ fontSize: 16, color: '#fff', marginBottom: 8 }}>
                    새 봇 추가
                </Text>
                <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 13, textAlign: 'center' }}>
                    AI 추세 또는 그리드 봇 생성
                </Text>
                <div style={{ marginTop: 12 }}>
                    <Text style={{ color: '#00A8FF', fontSize: 12 }}>
                        최대 {maxAllocation.toFixed(1)}% 할당 가능
                    </Text>
                </div>
            </Card>

            {/* 봇 생성 모달 */}
            <Modal
                title={
                    <Space>
                        <RobotOutlined style={{ color: '#00A8FF' }} />
                        <span style={{ fontWeight: 600 }}>새 봇 생성</span>
                    </Space>
                }
                open={isModalOpen}
                onCancel={handleClose}
                footer={null}
                width={520}
                styles={{
                    content: {
                        background: 'linear-gradient(180deg, #1e1e2d 0%, #171725 100%)',
                        borderRadius: 16,
                    },
                    header: {
                        background: 'transparent',
                        borderBottom: '1px solid rgba(255,255,255,0.08)',
                        color: '#fff',
                    },
                    body: { padding: '24px' }
                }}
            >
                <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                    initialValues={{
                        allocation_percent: 20,
                        max_leverage: 10,
                        max_positions: 3,
                        telegram_notify: true,
                    }}
                >
                    {/* 봇 타입 선택 */}
                    <div style={{ marginBottom: 20 }}>
                        <Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: 13, marginBottom: 8, display: 'block' }}>
                            봇 타입 선택
                        </Text>
                        <Space size={12}>
                            <div
                                onClick={() => setBotType('ai_trend')}
                                style={{
                                    padding: '16px 24px',
                                    borderRadius: 12,
                                    background: botType === 'ai_trend'
                                        ? 'linear-gradient(135deg, #7C54FF 0%, #5B3CC4 100%)'
                                        : '#252538',
                                    border: botType === 'ai_trend' ? '2px solid #7C54FF' : '2px solid transparent',
                                    cursor: 'pointer',
                                    textAlign: 'center',
                                    transition: 'all 0.2s ease',
                                    flex: 1,
                                }}
                            >
                                <ThunderboltOutlined style={{ fontSize: 24, color: '#fff', display: 'block', marginBottom: 8 }} />
                                <Text style={{ color: '#fff', fontWeight: 600, display: 'block' }}>AI 추세</Text>
                                <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11 }}>전략 기반 자동매매</Text>
                            </div>
                            <div
                                onClick={() => setBotType('grid')}
                                style={{
                                    padding: '16px 24px',
                                    borderRadius: 12,
                                    background: botType === 'grid'
                                        ? 'linear-gradient(135deg, #00C076 0%, #00A060 100%)'
                                        : '#252538',
                                    border: botType === 'grid' ? '2px solid #00C076' : '2px solid transparent',
                                    cursor: 'pointer',
                                    textAlign: 'center',
                                    transition: 'all 0.2s ease',
                                    flex: 1,
                                }}
                            >
                                <LineChartOutlined style={{ fontSize: 24, color: '#fff', display: 'block', marginBottom: 8 }} />
                                <Text style={{ color: '#fff', fontWeight: 600, display: 'block' }}>그리드</Text>
                                <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11 }}>범위 내 자동매매</Text>
                            </div>
                        </Space>
                    </div>

                    <Divider style={{ borderColor: 'rgba(255,255,255,0.08)', margin: '16px 0' }} />

                    {/* 기본 정보 */}
                    <Form.Item
                        name="name"
                        label={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>봇 이름</Text>}
                        rules={[{ required: true, message: '봇 이름을 입력해주세요' }]}
                    >
                        <Input
                            placeholder="예: BTC 보수적 봇"
                            style={{
                                background: '#252538',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: 8,
                                color: '#fff',
                            }}
                        />
                    </Form.Item>

                    <Form.Item
                        name="description"
                        label={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>설명 (선택)</Text>}
                    >
                        <TextArea
                            rows={2}
                            placeholder="봇에 대한 간단한 설명"
                            style={{
                                background: '#252538',
                                border: '1px solid rgba(255,255,255,0.1)',
                                borderRadius: 8,
                                color: '#fff',
                            }}
                        />
                    </Form.Item>

                    <Form.Item
                        name="symbol"
                        label={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>거래 심볼</Text>}
                        rules={[{ required: true, message: '심볼을 선택해주세요' }]}
                    >
                        <Select
                            placeholder="심볼 선택"
                            style={{ width: '100%' }}
                            dropdownStyle={{ background: '#252538' }}
                        >
                            {SYMBOLS.map(s => (
                                <Option key={s.value} value={s.value}>{s.label}</Option>
                            ))}
                        </Select>
                    </Form.Item>

                    {/* AI 봇인 경우 전략 선택 */}
                    {botType === 'ai_trend' && (
                        <Form.Item
                            name="strategy_id"
                            label={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>전략 선택</Text>}
                            rules={[{ required: true, message: '전략을 선택해주세요' }]}
                        >
                            <Select
                                placeholder="전략 선택"
                                style={{ width: '100%' }}
                                dropdownStyle={{ background: '#252538' }}
                            >
                                {strategies.map(s => (
                                    <Option key={s.id} value={s.id}>{s.name}</Option>
                                ))}
                            </Select>
                        </Form.Item>
                    )}

                    <Divider style={{ borderColor: 'rgba(255,255,255,0.08)', margin: '16px 0' }} />

                    {/* 리스크 설정 */}
                    <Form.Item
                        name="allocation_percent"
                        label={
                            <Space>
                                <Text style={{ color: 'rgba(255,255,255,0.8)' }}>잔고 할당</Text>
                                <Tooltip title={`최대 ${maxAllocation.toFixed(1)}%까지 할당 가능`}>
                                    <InfoCircleOutlined style={{ color: 'rgba(255,255,255,0.4)' }} />
                                </Tooltip>
                            </Space>
                        }
                        rules={[
                            { required: true, message: '할당 비율을 입력해주세요' },
                            { type: 'number', min: 1, max: maxAllocation, message: `1~${maxAllocation}% 사이로 설정해주세요` }
                        ]}
                    >
                        <Slider
                            min={1}
                            max={Math.min(100, maxAllocation)}
                            marks={{
                                1: '1%',
                                [Math.round(maxAllocation / 2)]: `${Math.round(maxAllocation / 2)}%`,
                                [Math.round(maxAllocation)]: `${Math.round(maxAllocation)}%`,
                            }}
                            tooltip={{ formatter: (v) => `${v}%` }}
                        />
                    </Form.Item>

                    <Space size={16} style={{ width: '100%' }}>
                        <Form.Item
                            name="max_leverage"
                            label={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>최대 레버리지</Text>}
                            style={{ flex: 1, marginBottom: 0 }}
                        >
                            <InputNumber
                                min={1}
                                max={50}
                                style={{ width: '100%', background: '#252538' }}
                            />
                        </Form.Item>

                        <Form.Item
                            name="max_positions"
                            label={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>최대 포지션</Text>}
                            style={{ flex: 1, marginBottom: 0 }}
                        >
                            <InputNumber
                                min={1}
                                max={10}
                                style={{ width: '100%', background: '#252538' }}
                            />
                        </Form.Item>
                    </Space>

                    <div style={{ marginTop: 16 }}>
                        <Space size={16}>
                            <Form.Item
                                name="stop_loss_percent"
                                label={<Text style={{ color: '#FF4D6A' }}>손절 %</Text>}
                                style={{ marginBottom: 0 }}
                            >
                                <InputNumber
                                    min={0.5}
                                    max={50}
                                    step={0.5}
                                    placeholder="2.0"
                                    style={{ width: 100, background: '#252538' }}
                                />
                            </Form.Item>

                            <Form.Item
                                name="take_profit_percent"
                                label={<Text style={{ color: '#00C076' }}>익절 %</Text>}
                                style={{ marginBottom: 0 }}
                            >
                                <InputNumber
                                    min={0.5}
                                    max={100}
                                    step={0.5}
                                    placeholder="4.0"
                                    style={{ width: 100, background: '#252538' }}
                                />
                            </Form.Item>
                        </Space>
                    </div>

                    <Divider style={{ borderColor: 'rgba(255,255,255,0.08)', margin: '20px 0 16px' }} />

                    {/* 알림 설정 */}
                    <Form.Item
                        name="telegram_notify"
                        valuePropName="checked"
                        style={{ marginBottom: 24 }}
                    >
                        <Space>
                            <Switch />
                            <Text style={{ color: 'rgba(255,255,255,0.8)' }}>텔레그램 알림 활성화</Text>
                        </Space>
                    </Form.Item>

                    {/* 제출 버튼 */}
                    <div style={{ display: 'flex', gap: 12 }}>
                        <Button
                            onClick={handleClose}
                            style={{
                                flex: 1,
                                height: 44,
                                borderRadius: 8,
                                background: '#252538',
                                border: 'none',
                                color: '#fff',
                            }}
                        >
                            취소
                        </Button>
                        <Button
                            type="primary"
                            htmlType="submit"
                            loading={loading}
                            style={{
                                flex: 2,
                                height: 44,
                                borderRadius: 8,
                                background: 'linear-gradient(135deg, #00A8FF 0%, #7C54FF 100%)',
                                border: 'none',
                                fontWeight: 600,
                            }}
                        >
                            <RobotOutlined style={{ marginRight: 6 }} />
                            봇 생성
                        </Button>
                    </div>
                </Form>
            </Modal>
        </>
    );
}
