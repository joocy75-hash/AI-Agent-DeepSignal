import { useState, useEffect, useRef } from 'react';
import { Card, Button, Typography, Space, Tag, Divider, Switch } from 'antd';
import {
    FileTextOutlined,
    ClearOutlined,
    DownloadOutlined,
    PauseCircleOutlined,
    PlayCircleOutlined,
} from '@ant-design/icons';
import { useWebSocket } from '../context/WebSocketContext';

const { Text } = Typography;

// 로그 레벨별 색상
const LOG_LEVEL_COLORS = {
    DEBUG: '#8c8c8c',
    INFO: '#1890ff',
    WARNING: '#faad14',
    ERROR: '#ff4d4f',
    CRITICAL: '#cf1322',
};

export default function BotLogViewer({ maxLogs = 500, height = 400, compact = false, showHeader = true }) {
    const { isConnected, subscribe, send } = useWebSocket();
    const [logs, setLogs] = useState([]);
    const [isPaused, setIsPaused] = useState(false);
    const [autoScroll, setAutoScroll] = useState(true);
    const logContainerRef = useRef(null);
    const pausedLogsRef = useRef([]);

    // WebSocket으로 실시간 로그 수신
    useEffect(() => {
        if (!isConnected) {
            console.log('[BotLogViewer] WebSocket not connected');
            return;
        }

        console.log('[BotLogViewer] WebSocket connected, requesting recent logs');
        // 최근 로그 요청
        const sent = send({ action: 'get_recent_logs', limit: 100 });
        console.log('[BotLogViewer] Sent get_recent_logs request:', sent);

        // 실시간 로그 구독
        const unsubscribe = subscribe('bot_log', (data) => {
            console.log('[BotLogViewer] Received bot_log:', data);
            if (!isPaused) {
                setLogs((prevLogs) => {
                    const newLogs = [...prevLogs, data.data];
                    // 최대 로그 개수 제한
                    if (newLogs.length > maxLogs) {
                        return newLogs.slice(-maxLogs);
                    }
                    return newLogs;
                });
            } else {
                // 일시정지 중이면 버퍼에 저장
                pausedLogsRef.current.push(data.data);
            }
        });

        // 최근 로그 응답 처리
        const unsubscribeRecentLogs = subscribe('recent_logs', (data) => {
            console.log('[BotLogViewer] Received recent_logs:', data);
            if (data.logs && Array.isArray(data.logs)) {
                console.log('[BotLogViewer] Setting logs, count:', data.logs.length);
                setLogs(data.logs);
            }
        });

        return () => {
            console.log('[BotLogViewer] Cleaning up subscriptions');
            unsubscribe();
            unsubscribeRecentLogs();
        };
    }, [isConnected, isPaused, subscribe, send, maxLogs]);

    // 자동 스크롤
    useEffect(() => {
        if (autoScroll && logContainerRef.current) {
            logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
        }
    }, [logs, autoScroll]);

    // 일시정지 토글
    const handlePauseToggle = () => {
        if (isPaused) {
            // 재개: 버퍼에 있던 로그를 추가
            if (pausedLogsRef.current.length > 0) {
                setLogs((prevLogs) => {
                    const newLogs = [...prevLogs, ...pausedLogsRef.current];
                    pausedLogsRef.current = [];
                    if (newLogs.length > maxLogs) {
                        return newLogs.slice(-maxLogs);
                    }
                    return newLogs;
                });
            }
        }
        setIsPaused(!isPaused);
    };

    // 로그 클리어
    const handleClear = () => {
        setLogs([]);
        pausedLogsRef.current = [];
    };

    // 로그 다운로드
    const handleDownload = () => {
        const logText = logs
            .map(
                (log) =>
                    `[${log.timestamp}] [${log.level}] ${log.logger} - ${log.message}`
            )
            .join('\n');

        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bot_logs_${new Date().toISOString().replace(/[:.]/g, '-')}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    // 로그 레벨별 필터링 (향후 확장 가능)
    const getLogColor = (level) => {
        return LOG_LEVEL_COLORS[level] || '#000';
    };

    // 로그 콘텐츠 렌더링
    const renderLogContent = () => (
        <div
            ref={logContainerRef}
            style={{
                height: height,
                overflowY: 'auto',
                background: compact ? 'rgba(0, 0, 0, 0.03)' : '#1e1e1e',
                padding: compact ? '8px' : '12px',
                borderRadius: compact ? 6 : 4,
                fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                fontSize: compact ? 11 : 12,
                lineHeight: '1.4',
            }}
        >
            {logs.length === 0 ? (
                <div
                    style={{
                        color: compact ? '#999' : '#888',
                        textAlign: 'center',
                        padding: compact ? '16px 8px' : '20px',
                        fontSize: compact ? 12 : 13,
                    }}
                >
                    {compact ? (
                        <>
                            <div style={{ marginBottom: 4 }}>AI가 시장을 분석하고 있습니다...</div>
                            <div style={{ fontSize: 11, color: '#bbb' }}>투자 판단 로그가 여기에 표시됩니다</div>
                        </>
                    ) : (
                        '로그가 없습니다. 봇을 시작하면 로그가 표시됩니다.'
                    )}
                </div>
            ) : (
                logs.map((log, index) => (
                    <div
                        key={index}
                        style={{
                            marginBottom: compact ? 3 : 4,
                            padding: compact ? '3px 6px' : '4px 8px',
                            borderLeft: `3px solid ${getLogColor(log.level)}`,
                            background: compact ? 'rgba(255, 255, 255, 0.5)' : 'rgba(255, 255, 255, 0.05)',
                            borderRadius: 2,
                        }}
                    >
                        {compact ? (
                            // Compact mode: 시간 + 메시지만
                            <div style={{ display: 'flex', gap: 6, alignItems: 'flex-start' }}>
                                <Text
                                    style={{
                                        color: '#888',
                                        fontSize: 10,
                                        flexShrink: 0,
                                    }}
                                >
                                    {new Date(log.timestamp).toLocaleTimeString('ko-KR', {
                                        hour12: false,
                                        hour: '2-digit',
                                        minute: '2-digit',
                                        second: '2-digit',
                                    })}
                                </Text>
                                <Text
                                    style={{
                                        color: getLogColor(log.level),
                                        flex: 1,
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                        fontSize: 11,
                                    }}
                                >
                                    {log.message}
                                </Text>
                            </div>
                        ) : (
                            // Full mode: 시간 + 레벨 태그 + 메시지
                            <Space size={8} style={{ width: '100%' }}>
                                <Text
                                    style={{
                                        color: '#666',
                                        fontSize: 11,
                                        minWidth: 80,
                                    }}
                                >
                                    {new Date(log.timestamp).toLocaleTimeString('ko-KR', {
                                        hour12: false,
                                    })}
                                </Text>
                                <Tag
                                    color={
                                        log.level === 'ERROR' || log.level === 'CRITICAL'
                                            ? 'red'
                                            : log.level === 'WARNING'
                                            ? 'orange'
                                            : log.level === 'INFO'
                                            ? 'blue'
                                            : 'default'
                                    }
                                    style={{ margin: 0, fontSize: 10, minWidth: 60, textAlign: 'center' }}
                                >
                                    {log.level}
                                </Tag>
                                <Text
                                    style={{
                                        color: getLogColor(log.level),
                                        flex: 1,
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word',
                                    }}
                                >
                                    {log.message}
                                </Text>
                            </Space>
                        )}
                    </div>
                ))
            )}
        </div>
    );

    // Compact mode: Card 없이 로그만 표시
    if (compact) {
        return (
            <div style={{ marginBottom: 12 }}>
                {renderLogContent()}
                {logs.length > 0 && (
                    <div style={{
                        display: 'flex',
                        justifyContent: 'flex-end',
                        marginTop: 6,
                        paddingRight: 4,
                    }}>
                        <Text type="secondary" style={{ fontSize: 10 }}>
                            {logs.length}개 로그
                        </Text>
                    </div>
                )}
            </div>
        );
    }

    // Full mode: Card로 감싸서 표시
    return (
        <Card
            title={
                showHeader ? (
                    <Space>
                        <FileTextOutlined />
                        <span>실시간 봇 로그</span>
                        {isPaused && <Tag color="orange">일시정지</Tag>}
                        {!isConnected && <Tag color="red">연결 끊김</Tag>}
                    </Space>
                ) : null
            }
            extra={
                showHeader ? (
                    <Space size="small">
                        <Text type="secondary" style={{ fontSize: 12 }}>
                            자동 스크롤
                        </Text>
                        <Switch
                            size="small"
                            checked={autoScroll}
                            onChange={setAutoScroll}
                        />
                        <Button
                            size="small"
                            icon={isPaused ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
                            onClick={handlePauseToggle}
                        >
                            {isPaused ? '재개' : '일시정지'}
                        </Button>
                        <Button
                            size="small"
                            icon={<ClearOutlined />}
                            onClick={handleClear}
                        >
                            클리어
                        </Button>
                        <Button
                            size="small"
                            icon={<DownloadOutlined />}
                            onClick={handleDownload}
                            disabled={logs.length === 0}
                        >
                            다운로드
                        </Button>
                    </Space>
                ) : null
            }
            size="small"
        >
            {renderLogContent()}

            <Divider style={{ margin: '12px 0' }} />

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <Text type="secondary" style={{ fontSize: 12 }}>
                    총 {logs.length}개 로그
                    {pausedLogsRef.current.length > 0 && (
                        <span style={{ color: '#faad14', marginLeft: 8 }}>
                            (버퍼: {pausedLogsRef.current.length}개)
                        </span>
                    )}
                </Text>
                <Space size="small">
                    {logs.length > 0 && (
                        <Text type="secondary" style={{ fontSize: 11 }}>
                            최근 업데이트: {new Date(logs[logs.length - 1]?.timestamp).toLocaleString('ko-KR')}
                        </Text>
                    )}
                </Space>
            </div>
        </Card>
    );
}
