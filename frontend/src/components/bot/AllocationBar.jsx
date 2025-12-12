/**
 * AllocationBar Component
 * 
 * 잔고 할당 시각화 바 - 라이트 모드
 * 각 봇의 할당 비율을 시각적으로 표시
 */

import { Tooltip, Typography, Space } from 'antd';
import {
    WalletOutlined,
    PieChartOutlined,
} from '@ant-design/icons';

const { Text } = Typography;

// 색상 팔레트
const BOT_COLORS = [
    '#34c759', // 그린
    '#5ac8fa', // 시안
    '#007aff', // 블루
    '#5856d6', // 퍼플
    '#ff9500', // 오렌지
    '#ffcc00', // 골드
    '#ff3b30', // 레드
    '#30d158', // 민트
    '#af52de', // 라벤더
    '#32d74b', // 라임
];

export default function AllocationBar({
    bots = [],
    totalAllocation = 0,
    style = {}
}) {
    const availableAllocation = 100 - totalAllocation;

    return (
        <div style={{
            background: '#ffffff',
            borderRadius: 16,
            padding: '20px 24px',
            marginBottom: 24,
            border: '1px solid #f5f5f7',
            ...style
        }}>
            {/* Header */}
            <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: 16
            }}>
                <Space>
                    <PieChartOutlined style={{ fontSize: 18, color: '#34c759' }} />
                    <Text strong style={{ fontSize: 15, color: '#1d1d1f' }}>
                        잔고 할당 현황
                    </Text>
                </Space>
                <Space size="large">
                    <Text style={{ color: '#86868b', fontSize: 13 }}>
                        사용중 <span style={{ color: '#34c759', fontWeight: 600 }}>{totalAllocation.toFixed(1)}%</span>
                    </Text>
                    <Text style={{ color: '#86868b', fontSize: 13 }}>
                        사용가능 <span style={{ color: '#007aff', fontWeight: 600 }}>{availableAllocation.toFixed(1)}%</span>
                    </Text>
                </Space>
            </div>

            {/* Progress Bar */}
            <div style={{
                height: 12,
                background: '#f5f5f7',
                borderRadius: 6,
                overflow: 'hidden',
                display: 'flex'
            }}>
                {bots.map((bot, index) => {
                    const color = BOT_COLORS[index % BOT_COLORS.length];
                    const width = `${bot.allocation_percent}%`;

                    return (
                        <Tooltip
                            key={bot.id}
                            title={
                                <div style={{ textAlign: 'center' }}>
                                    <div style={{ fontWeight: 600 }}>{bot.name}</div>
                                    <div style={{ fontSize: 12, opacity: 0.8 }}>
                                        {bot.allocation_percent}% ({bot.symbol})
                                    </div>
                                    {bot.is_running && (
                                        <div style={{ color: '#34c759', fontSize: 11 }}>● 실행 중</div>
                                    )}
                                </div>
                            }
                        >
                            <div
                                style={{
                                    width,
                                    height: '100%',
                                    background: bot.is_running
                                        ? `linear-gradient(90deg, ${color} 0%, ${color}dd 100%)`
                                        : `${color}88`,
                                    borderRight: '1px solid rgba(255,255,255,0.5)',
                                    transition: 'all 0.3s ease',
                                    cursor: 'pointer',
                                }}
                            />
                        </Tooltip>
                    );
                })}
                {/* 남은 공간 */}
                {availableAllocation > 0 && (
                    <div style={{
                        flex: 1,
                        background: 'transparent',
                    }} />
                )}
            </div>

            {/* Legend */}
            <div style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: '12px',
                marginTop: 16
            }}>
                {bots.map((bot, index) => {
                    const color = BOT_COLORS[index % BOT_COLORS.length];
                    return (
                        <div
                            key={bot.id}
                            style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: 6,
                                padding: '4px 10px',
                                background: '#f5f5f7',
                                borderRadius: 20,
                                fontSize: 12,
                            }}
                        >
                            <div style={{
                                width: 8,
                                height: 8,
                                borderRadius: '50%',
                                background: color,
                                boxShadow: bot.is_running ? `0 0 6px ${color}` : 'none'
                            }} />
                            <span style={{ color: '#1d1d1f' }}>{bot.name}</span>
                            <span style={{ color: '#86868b' }}>{bot.allocation_percent}%</span>
                        </div>
                    );
                })}
                {bots.length === 0 && (
                    <Text style={{ color: '#86868b', fontSize: 13 }}>
                        <WalletOutlined style={{ marginRight: 6 }} />
                        등록된 봇이 없습니다. 새 봇을 추가해보세요!
                    </Text>
                )}
            </div>
        </div>
    );
}
