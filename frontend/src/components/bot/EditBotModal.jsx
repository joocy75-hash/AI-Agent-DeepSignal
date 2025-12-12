/**
 * EditBotModal Component
 * 
 * 봇 설정 수정 모달
 */

import { useState, useEffect } from 'react';
import {
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
    Slider,
    message
} from 'antd';
import {
    EditOutlined,
    InfoCircleOutlined,
} from '@ant-design/icons';

const { Text } = Typography;
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

export default function EditBotModal({
    bot,
    strategies = [],
    maxAllocation = 100,
    open,
    onClose,
    onUpdate
}) {
    const [loading, setLoading] = useState(false);
    const [form] = Form.useForm();

    // 수정 가능한 최대 할당량 (현재 봇의 할당량 + 남은 할당량)
    const availableAllocation = maxAllocation + (bot?.allocation_percent || 0);

    useEffect(() => {
        if (open && bot) {
            form.setFieldsValue({
                name: bot.name,
                description: bot.description,
                symbol: bot.symbol,
                strategy_id: bot.strategy_id,
                allocation_percent: bot.allocation_percent,
                max_leverage: bot.max_leverage,
                max_positions: bot.max_positions,
                stop_loss_percent: bot.stop_loss_percent,
                take_profit_percent: bot.take_profit_percent,
                telegram_notify: bot.telegram_notify,
            });
        }
    }, [open, bot, form]);

    const handleSubmit = async (values) => {
        setLoading(true);
        try {
            await onUpdate?.(bot.id, values);
            message.success('봇 설정이 수정되었습니다');
            onClose();
        } catch (err) {
            message.error(err.response?.data?.detail || err.message || '수정 실패');
        } finally {
            setLoading(false);
        }
    };

    if (!bot) return null;

    return (
        <Modal
            title={
                <Space>
                    <EditOutlined style={{ color: '#00A8FF' }} />
                    <span style={{ fontWeight: 600 }}>봇 설정 수정</span>
                </Space>
            }
            open={open}
            onCancel={onClose}
            footer={null}
            width={500}
            styles={{
                content: {
                    background: 'linear-gradient(180deg, #1e1e2d 0%, #171725 100%)',
                    borderRadius: 16,
                },
                header: {
                    background: 'transparent',
                    borderBottom: '1px solid rgba(255,255,255,0.08)',
                },
                body: { padding: '24px' }
            }}
        >
            <Form
                form={form}
                layout="vertical"
                onFinish={handleSubmit}
            >
                {/* 기본 정보 */}
                <Form.Item
                    name="name"
                    label={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>봇 이름</Text>}
                    rules={[{ required: true, message: '봇 이름을 입력해주세요' }]}
                >
                    <Input
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
                    label={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>설명</Text>}
                >
                    <TextArea
                        rows={2}
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
                        style={{ width: '100%' }}
                        dropdownStyle={{ background: '#252538' }}
                    >
                        {SYMBOLS.map(s => (
                            <Option key={s.value} value={s.value}>{s.label}</Option>
                        ))}
                    </Select>
                </Form.Item>

                {/* AI 봇인 경우 전략 선택 */}
                {bot.bot_type === 'ai_trend' && (
                    <Form.Item
                        name="strategy_id"
                        label={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>전략</Text>}
                        rules={[{ required: true, message: '전략을 선택해주세요' }]}
                    >
                        <Select
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
                    label={<Text style={{ color: 'rgba(255,255,255,0.8)' }}>잔고 할당 (%)</Text>}
                    rules={[
                        { required: true, message: '할당 비율을 입력해주세요' },
                    ]}
                >
                    <Slider
                        min={1}
                        max={Math.min(100, availableAllocation)}
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
                        <Text style={{ color: 'rgba(255,255,255,0.8)' }}>텔레그램 알림</Text>
                    </Space>
                </Form.Item>

                {/* 제출 버튼 */}
                <div style={{ display: 'flex', gap: 12 }}>
                    <Button
                        onClick={onClose}
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
                        저장
                    </Button>
                </div>
            </Form>
        </Modal>
    );
}
