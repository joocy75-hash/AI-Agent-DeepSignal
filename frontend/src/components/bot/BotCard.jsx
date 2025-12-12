/**
 * BotCard Component
 * 
 * 비트겟 스타일의 봇 카드 컴포넌트
 * - 실행 상태 표시 (그린 글로우 효과)
 * - 봇 타입 / 심볼 / 전략 정보
 * - PNL 및 승률 통계
 * - 시작/중지/설정/삭제 버튼
 */

import { useState } from 'react';
import {
    Card,
    Button,
    Space,
    Tag,
    Typography,
    Tooltip,
    Modal,
    Popconfirm,
    message,
    Spin
} from 'antd';
import {
    PlayCircleOutlined,
    PauseCircleOutlined,
    SettingOutlined,
    DeleteOutlined,
    RobotOutlined,
    ThunderboltOutlined,
    LineChartOutlined,
    TrophyOutlined,
    ClockCircleOutlined,
    EditOutlined,
} from '@ant-design/icons';

const { Text, Title } = Typography;

// 봇 타입 설정
const BOT_TYPE_CONFIG = {
    ai_trend: {
        label: 'AI 추세',
        color: '#7C54FF',
        icon: <ThunderboltOutlined />,
        gradient: 'linear-gradient(135deg, #7C54FF 0%, #5B3CC4 100%)',
    },
    grid: {
        label: '그리드',
        color: '#00C076',
        icon: <LineChartOutlined />,
        gradient: 'linear-gradient(135deg, #00C076 0%, #00A060 100%)',
    },
};

export default function BotCard({
    bot,
    onStart,
    onStop,
    onEdit,
    onDelete,
    onViewStats,
    loading = false
}) {
    const [actionLoading, setActionLoading] = useState(false);

    const isRunning = bot.is_running;
    const botTypeConfig = BOT_TYPE_CONFIG[bot.bot_type] || BOT_TYPE_CONFIG.ai_trend;

    // PNL 포맷팅
    const formatPnl = (value) => {
        if (!value || value === 0) return '$0.00';
        const formatted = Math.abs(value).toFixed(2);
        return value >= 0 ? `+$${formatted}` : `-$${formatted}`;
    };

    // 승률 계산
    const winRate = bot.total_trades > 0
        ? ((bot.winning_trades / bot.total_trades) * 100).toFixed(1)
        : '0.0';

    // 시작/중지 핸들러
    const handleToggle = async () => {
        setActionLoading(true);
        try {
            if (isRunning) {
                await onStop?.(bot.id);
            } else {
                await onStart?.(bot.id);
            }
        } catch (err) {
            message.error(err.message || '작업 실패');
        } finally {
            setActionLoading(false);
        }
    };

    // 삭제 핸들러
    const handleDelete = async () => {
        setActionLoading(true);
        try {
            await onDelete?.(bot.id);
            message.success(`봇 "${bot.name}" 삭제됨`);
        } catch (err) {
            message.error(err.message || '삭제 실패');
        } finally {
            setActionLoading(false);
        }
    };

    return (
        <Card
            style={{
                borderRadius: 16,
                border: isRunning
                    ? '1px solid rgba(0, 192, 118, 0.3)'
                    : '1px solid rgba(255, 255, 255, 0.08)',
                background: 'linear-gradient(180deg, #1e1e2d 0%, #171725 100%)',
                overflow: 'hidden',
                transition: 'all 0.3s ease',
                boxShadow: isRunning
                    ? '0 0 20px rgba(0, 192, 118, 0.15)'
                    : '0 4px 12px rgba(0, 0, 0, 0.3)',
            }}
            styles={{
                body: { padding: 0 }
            }}
            hoverable
        >
            <Spin spinning={loading || actionLoading}>
                {/* Header - 봇 타입 배지 & 상태 */}
                <div style={{
                    background: botTypeConfig.gradient,
                    padding: '12px 16px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                }}>
                    <Space>
                        <div style={{
                            width: 32,
                            height: 32,
                            borderRadius: 8,
                            background: 'rgba(255,255,255,0.2)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: 16,
                            color: '#fff',
                        }}>
                            {botTypeConfig.icon}
                        </div>
                        <div>
                            <Text style={{ color: '#fff', fontWeight: 600, fontSize: 15 }}>
                                {bot.name}
                            </Text>
                            <div>
                                <Tag style={{
                                    background: 'rgba(255,255,255,0.2)',
                                    border: 'none',
                                    color: '#fff',
                                    fontSize: 11,
                                    marginTop: 2,
                                }}>
                                    {botTypeConfig.label}
                                </Tag>
                            </div>
                        </div>
                    </Space>

                    {/* 상태 표시 */}
                    <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                        padding: '4px 10px',
                        background: isRunning ? 'rgba(0, 192, 118, 0.3)' : 'rgba(255,255,255,0.1)',
                        borderRadius: 20,
                    }}>
                        <div style={{
                            width: 8,
                            height: 8,
                            borderRadius: '50%',
                            background: isRunning ? '#00FF94' : '#6b7280',
                            boxShadow: isRunning ? '0 0 8px #00FF94' : 'none',
                            animation: isRunning ? 'pulse 2s infinite' : 'none',
                        }} />
                        <Text style={{ color: '#fff', fontSize: 12, fontWeight: 500 }}>
                            {isRunning ? '실행 중' : '중지됨'}
                        </Text>
                    </div>
                </div>

                {/* Body */}
                <div style={{ padding: 16 }}>
                    {/* 심볼 & 전략 */}
                    <div style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginBottom: 16,
                    }}>
                        <Space size={8}>
                            <Tag style={{
                                background: '#2d2d44',
                                border: 'none',
                                color: '#00A8FF',
                                fontWeight: 600,
                                fontSize: 13,
                            }}>
                                {bot.symbol}
                            </Tag>
                            {bot.strategy_name && (
                                <Tooltip title={`전략: ${bot.strategy_name}`}>
                                    <Tag style={{
                                        background: '#2d2d44',
                                        border: 'none',
                                        color: '#b794f6',
                                        fontSize: 11,
                                        maxWidth: 100,
                                        overflow: 'hidden',
                                        textOverflow: 'ellipsis',
                                    }}>
                                        {bot.strategy_name}
                                    </Tag>
                                </Tooltip>
                            )}
                        </Space>
                        <Tag style={{
                            background: 'rgba(0, 168, 255, 0.15)',
                            border: 'none',
                            color: '#00A8FF',
                            fontSize: 12,
                        }}>
                            {bot.allocation_percent}% 할당
                        </Tag>
                    </div>

                    {/* 통계 그리드 */}
                    <div style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(2, 1fr)',
                        gap: 12,
                        marginBottom: 16,
                    }}>
                        {/* 총 손익 */}
                        <div style={{
                            background: '#252538',
                            borderRadius: 10,
                            padding: 12,
                            textAlign: 'center',
                        }}>
                            <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, display: 'block' }}>
                                총 손익
                            </Text>
                            <Text style={{
                                color: bot.total_pnl >= 0 ? '#00C076' : '#FF4D6A',
                                fontSize: 16,
                                fontWeight: 700,
                            }}>
                                {formatPnl(bot.total_pnl)}
                            </Text>
                        </div>

                        {/* 승률 */}
                        <div style={{
                            background: '#252538',
                            borderRadius: 10,
                            padding: 12,
                            textAlign: 'center',
                        }}>
                            <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, display: 'block' }}>
                                승률
                            </Text>
                            <Text style={{
                                color: parseFloat(winRate) >= 50 ? '#00C076' : '#FF4D6A',
                                fontSize: 16,
                                fontWeight: 700,
                            }}>
                                {winRate}%
                            </Text>
                        </div>

                        {/* 총 거래 */}
                        <div style={{
                            background: '#252538',
                            borderRadius: 10,
                            padding: 12,
                            textAlign: 'center',
                        }}>
                            <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, display: 'block' }}>
                                총 거래
                            </Text>
                            <Text style={{ color: '#fff', fontSize: 16, fontWeight: 700 }}>
                                {bot.total_trades || 0}
                            </Text>
                        </div>

                        {/* 레버리지 */}
                        <div style={{
                            background: '#252538',
                            borderRadius: 10,
                            padding: 12,
                            textAlign: 'center',
                        }}>
                            <Text style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, display: 'block' }}>
                                레버리지
                            </Text>
                            <Text style={{ color: '#F5C242', fontSize: 16, fontWeight: 700 }}>
                                x{bot.max_leverage || 1}
                            </Text>
                        </div>
                    </div>

                    {/* 액션 버튼 */}
                    <div style={{
                        display: 'flex',
                        gap: 8,
                    }}>
                        {/* 시작/중지 토글 버튼 */}
                        <Button
                            type="primary"
                            icon={isRunning ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
                            onClick={handleToggle}
                            loading={actionLoading}
                            style={{
                                flex: 2,
                                height: 40,
                                borderRadius: 8,
                                background: isRunning
                                    ? 'linear-gradient(135deg, #FF4D6A 0%, #d63c57 100%)'
                                    : 'linear-gradient(135deg, #00C076 0%, #00A060 100%)',
                                border: 'none',
                                fontWeight: 600,
                            }}
                        >
                            {isRunning ? 'Stop' : 'Start'}
                        </Button>

                        {/* 설정 버튼 */}
                        <Tooltip title="설정 편집">
                            <Button
                                icon={<EditOutlined />}
                                onClick={() => onEdit?.(bot)}
                                disabled={isRunning}
                                style={{
                                    height: 40,
                                    width: 40,
                                    borderRadius: 8,
                                    background: '#2d2d44',
                                    border: 'none',
                                    color: isRunning ? 'rgba(255,255,255,0.3)' : '#fff',
                                }}
                            />
                        </Tooltip>

                        {/* 통계 버튼 */}
                        <Tooltip title="상세 통계">
                            <Button
                                icon={<TrophyOutlined />}
                                onClick={() => onViewStats?.(bot.id)}
                                style={{
                                    height: 40,
                                    width: 40,
                                    borderRadius: 8,
                                    background: '#2d2d44',
                                    border: 'none',
                                    color: '#F5C242',
                                }}
                            />
                        </Tooltip>

                        {/* 삭제 버튼 */}
                        <Popconfirm
                            title="봇 삭제"
                            description={`"${bot.name}" 봇을 삭제하시겠습니까?`}
                            onConfirm={handleDelete}
                            okText="삭제"
                            cancelText="취소"
                            okButtonProps={{ danger: true }}
                        >
                            <Tooltip title="삭제">
                                <Button
                                    icon={<DeleteOutlined />}
                                    danger
                                    style={{
                                        height: 40,
                                        width: 40,
                                        borderRadius: 8,
                                        background: 'rgba(255, 77, 106, 0.15)',
                                        border: 'none',
                                    }}
                                />
                            </Tooltip>
                        </Popconfirm>
                    </div>
                </div>

                {/* Footer - 마지막 활동 */}
                {(bot.last_trade_at || bot.last_started_at) && (
                    <div style={{
                        padding: '10px 16px',
                        borderTop: '1px solid rgba(255,255,255,0.05)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 6,
                    }}>
                        <ClockCircleOutlined style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12 }} />
                        <Text style={{ color: 'rgba(255,255,255,0.4)', fontSize: 11 }}>
                            {bot.last_trade_at
                                ? `마지막 거래: ${new Date(bot.last_trade_at).toLocaleDateString()}`
                                : bot.last_started_at
                                    ? `마지막 시작: ${new Date(bot.last_started_at).toLocaleDateString()}`
                                    : '활동 없음'
                            }
                        </Text>
                    </div>
                )}
            </Spin>

            {/* 펄스 애니메이션 스타일 */}
            <style>{`
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            `}</style>
        </Card>
    );
}
