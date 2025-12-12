/**
 * BotStatsModal Component
 * 
 * 봇 상세 통계를 보여주는 모달
 */

import { useState, useEffect } from 'react';
import {
    Modal,
    Typography,
    Space,
    Row,
    Col,
    Spin,
    Progress,
    Statistic,
    Divider,
    Tag,
    message
} from 'antd';
import {
    TrophyOutlined,
    RiseOutlined,
    FallOutlined,
    ClockCircleOutlined,
    SwapOutlined,
    PercentageOutlined,
    DollarOutlined,
} from '@ant-design/icons';
import botInstancesAPI from '../../api/botInstances';

const { Text, Title } = Typography;

export default function BotStatsModal({
    botId,
    botName,
    open,
    onClose
}) {
    const [loading, setLoading] = useState(false);
    const [stats, setStats] = useState(null);

    useEffect(() => {
        if (open && botId) {
            loadStats();
        }
    }, [open, botId]);

    const loadStats = async () => {
        setLoading(true);
        try {
            const response = await botInstancesAPI.getStats(botId);
            setStats(response);
        } catch (err) {
            message.error('통계 로드 실패');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const formatPnl = (value) => {
        if (!value || value === 0) return '$0.00';
        const formatted = Math.abs(value).toFixed(2);
        return value >= 0 ? `+$${formatted}` : `-$${formatted}`;
    };

    return (
        <Modal
            title={
                <Space>
                    <TrophyOutlined style={{ color: '#F5C242' }} />
                    <span style={{ fontWeight: 600 }}>
                        {botName || `봇 #${botId}`} 상세 통계
                    </span>
                </Space>
            }
            open={open}
            onCancel={onClose}
            footer={null}
            width={600}
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
            <Spin spinning={loading}>
                {stats && (
                    <>
                        {/* 주요 통계 */}
                        <Row gutter={[16, 16]}>
                            {/* 총 손익 */}
                            <Col xs={12}>
                                <div style={{
                                    background: '#252538',
                                    borderRadius: 12,
                                    padding: 20,
                                    textAlign: 'center',
                                }}>
                                    <DollarOutlined style={{
                                        fontSize: 24,
                                        color: stats.total_pnl >= 0 ? '#00C076' : '#FF4D6A',
                                        marginBottom: 8
                                    }} />
                                    <Text style={{
                                        color: 'rgba(255,255,255,0.5)',
                                        fontSize: 12,
                                        display: 'block',
                                        marginBottom: 4
                                    }}>
                                        총 손익
                                    </Text>
                                    <Text style={{
                                        color: stats.total_pnl >= 0 ? '#00C076' : '#FF4D6A',
                                        fontSize: 24,
                                        fontWeight: 700,
                                    }}>
                                        {formatPnl(stats.total_pnl)}
                                    </Text>
                                </div>
                            </Col>

                            {/* 승률 */}
                            <Col xs={12}>
                                <div style={{
                                    background: '#252538',
                                    borderRadius: 12,
                                    padding: 20,
                                    textAlign: 'center',
                                }}>
                                    <PercentageOutlined style={{
                                        fontSize: 24,
                                        color: '#00A8FF',
                                        marginBottom: 8
                                    }} />
                                    <Text style={{
                                        color: 'rgba(255,255,255,0.5)',
                                        fontSize: 12,
                                        display: 'block',
                                        marginBottom: 4
                                    }}>
                                        승률
                                    </Text>
                                    <Text style={{
                                        color: stats.win_rate >= 50 ? '#00C076' : '#FF4D6A',
                                        fontSize: 24,
                                        fontWeight: 700,
                                    }}>
                                        {stats.win_rate?.toFixed(1)}%
                                    </Text>
                                </div>
                            </Col>
                        </Row>

                        {/* 승률 Progress */}
                        <div style={{ marginTop: 20 }}>
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                marginBottom: 8
                            }}>
                                <Space>
                                    <RiseOutlined style={{ color: '#00C076' }} />
                                    <Text style={{ color: '#00C076' }}>
                                        승리: {stats.winning_trades}
                                    </Text>
                                </Space>
                                <Space>
                                    <Text style={{ color: '#FF4D6A' }}>
                                        패배: {stats.losing_trades}
                                    </Text>
                                    <FallOutlined style={{ color: '#FF4D6A' }} />
                                </Space>
                            </div>
                            <Progress
                                percent={stats.win_rate || 0}
                                showInfo={false}
                                strokeColor="#00C076"
                                trailColor="rgba(255, 77, 106, 0.5)"
                                style={{ marginBottom: 0 }}
                            />
                        </div>

                        <Divider style={{ borderColor: 'rgba(255,255,255,0.08)' }} />

                        {/* 상세 통계 */}
                        <Row gutter={[16, 16]}>
                            <Col xs={8}>
                                <div style={{
                                    background: '#252538',
                                    borderRadius: 10,
                                    padding: 16,
                                    textAlign: 'center',
                                }}>
                                    <SwapOutlined style={{
                                        fontSize: 20,
                                        color: '#b794f6',
                                        marginBottom: 6
                                    }} />
                                    <Text style={{
                                        color: 'rgba(255,255,255,0.5)',
                                        fontSize: 11,
                                        display: 'block'
                                    }}>
                                        총 거래
                                    </Text>
                                    <Text style={{
                                        color: '#fff',
                                        fontSize: 18,
                                        fontWeight: 700,
                                    }}>
                                        {stats.total_trades || 0}
                                    </Text>
                                </div>
                            </Col>

                            <Col xs={8}>
                                <div style={{
                                    background: '#252538',
                                    borderRadius: 10,
                                    padding: 16,
                                    textAlign: 'center',
                                }}>
                                    <RiseOutlined style={{
                                        fontSize: 20,
                                        color: '#00C076',
                                        marginBottom: 6
                                    }} />
                                    <Text style={{
                                        color: 'rgba(255,255,255,0.5)',
                                        fontSize: 11,
                                        display: 'block'
                                    }}>
                                        최대 수익
                                    </Text>
                                    <Text style={{
                                        color: '#00C076',
                                        fontSize: 18,
                                        fontWeight: 700,
                                    }}>
                                        {formatPnl(stats.max_profit)}
                                    </Text>
                                </div>
                            </Col>

                            <Col xs={8}>
                                <div style={{
                                    background: '#252538',
                                    borderRadius: 10,
                                    padding: 16,
                                    textAlign: 'center',
                                }}>
                                    <FallOutlined style={{
                                        fontSize: 20,
                                        color: '#FF4D6A',
                                        marginBottom: 6
                                    }} />
                                    <Text style={{
                                        color: 'rgba(255,255,255,0.5)',
                                        fontSize: 11,
                                        display: 'block'
                                    }}>
                                        최대 손실
                                    </Text>
                                    <Text style={{
                                        color: '#FF4D6A',
                                        fontSize: 18,
                                        fontWeight: 700,
                                    }}>
                                        {formatPnl(stats.max_loss)}
                                    </Text>
                                </div>
                            </Col>
                        </Row>

                        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
                            <Col xs={12}>
                                <div style={{
                                    background: '#252538',
                                    borderRadius: 10,
                                    padding: 16,
                                    textAlign: 'center',
                                }}>
                                    <Text style={{
                                        color: 'rgba(255,255,255,0.5)',
                                        fontSize: 11,
                                        display: 'block',
                                        marginBottom: 4
                                    }}>
                                        평균 손익
                                    </Text>
                                    <Text style={{
                                        color: stats.avg_pnl >= 0 ? '#00C076' : '#FF4D6A',
                                        fontSize: 18,
                                        fontWeight: 700,
                                    }}>
                                        {formatPnl(stats.avg_pnl)}
                                    </Text>
                                </div>
                            </Col>

                            <Col xs={12}>
                                <div style={{
                                    background: '#252538',
                                    borderRadius: 10,
                                    padding: 16,
                                    textAlign: 'center',
                                }}>
                                    <ClockCircleOutlined style={{
                                        fontSize: 16,
                                        color: '#F5C242',
                                        marginRight: 6
                                    }} />
                                    <Text style={{
                                        color: 'rgba(255,255,255,0.5)',
                                        fontSize: 11,
                                        display: 'block',
                                        marginBottom: 4
                                    }}>
                                        총 실행 시간
                                    </Text>
                                    <Text style={{
                                        color: '#fff',
                                        fontSize: 18,
                                        fontWeight: 700,
                                    }}>
                                        {stats.running_time_hours?.toFixed(1) || 0}시간
                                    </Text>
                                </div>
                            </Col>
                        </Row>
                    </>
                )}

                {!stats && !loading && (
                    <div style={{ textAlign: 'center', padding: 40 }}>
                        <Text style={{ color: 'rgba(255,255,255,0.4)' }}>
                            통계 데이터가 없습니다
                        </Text>
                    </div>
                )}
            </Spin>
        </Modal>
    );
}
