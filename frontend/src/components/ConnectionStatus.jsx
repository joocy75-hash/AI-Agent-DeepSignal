import { memo } from 'react';
import { useWebSocket } from '../context/WebSocketContext';
import { useAuth } from '../context/AuthContext';

/**
 * WebSocket 연결 상태 표시 컴포넌트
 * 화면 우측 하단에 연결 상태를 표시하고, 재연결 버튼 제공
 * 로그인한 사용자에게만 표시됨
 */
function ConnectionStatus() {
    const { user, isAuthenticated } = useAuth();
    const {
        isConnected,
        connectionState,
        retryCount,
        nextRetryIn,
        maxRetries,
        reconnect
    } = useWebSocket();

    // 로그인하지 않은 상태에서는 표시하지 않음
    if (!user || !isAuthenticated) {
        return null;
    }

    // 연결된 상태에서는 표시하지 않음 (선택적)
    // if (isConnected) return null;

    const getStatusConfig = () => {
        switch (connectionState) {
            case 'connected':
                return {
                    icon: '🟢',
                    color: '#4caf50',
                    bgColor: 'rgba(76, 175, 80, 0.1)',
                    borderColor: '#4caf50',
                    text: '연결됨',
                    showReconnect: false,
                };
            case 'connecting':
                return {
                    icon: '🔄',
                    color: '#2196f3',
                    bgColor: 'rgba(33, 150, 243, 0.1)',
                    borderColor: '#2196f3',
                    text: '연결 중...',
                    showReconnect: false,
                };
            case 'reconnecting':
                return {
                    icon: '🔄',
                    color: '#ff9800',
                    bgColor: 'rgba(255, 152, 0, 0.1)',
                    borderColor: '#ff9800',
                    text: nextRetryIn
                        ? `재연결 중... (${nextRetryIn}초 후 시도 ${retryCount}/${maxRetries})`
                        : `재연결 중... (${retryCount}/${maxRetries})`,
                    showReconnect: true,
                };
            case 'failed':
                return {
                    icon: '❌',
                    color: '#f44336',
                    bgColor: 'rgba(244, 67, 54, 0.1)',
                    borderColor: '#f44336',
                    text: '연결 실패',
                    showReconnect: true,
                };
            case 'disconnected':
            default:
                return {
                    icon: '⚪',
                    color: '#9e9e9e',
                    bgColor: 'rgba(158, 158, 158, 0.1)',
                    borderColor: '#9e9e9e',
                    text: '연결 끊김',
                    showReconnect: true,
                };
        }
    };

    const config = getStatusConfig();

    // 연결된 상태에서는 작은 인디케이터만 표시
    if (isConnected) {
        return (
            <div
                style={{
                    position: 'fixed',
                    bottom: '20px',
                    right: '20px',
                    padding: '10px 16px',
                    background: 'rgba(255, 255, 255, 0.95)',
                    backdropFilter: 'blur(10px)',
                    border: '1px solid #e8e8ed',
                    borderRadius: '12px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    fontSize: '13px',
                    fontWeight: '500',
                    color: '#1d1d1f',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.08)',
                    zIndex: 9999,
                    transition: 'all 0.3s ease',
                }}
            >
                <span
                    style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: '#34c759',
                        animation: 'pulse 2s infinite',
                        boxShadow: '0 0 8px rgba(52, 199, 89, 0.4)',
                    }}
                />
                <span style={{ color: '#34c759', fontWeight: 600 }}>실시간 연결</span>
            </div>
        );
    }

    return (
        <div
            style={{
                position: 'fixed',
                bottom: '20px',
                right: '20px',
                padding: '16px 20px',
                background: 'rgba(255, 255, 255, 0.95)',
                backdropFilter: 'blur(10px)',
                border: '1px solid #e8e8ed',
                borderRadius: '16px',
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
                minWidth: '240px',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
                zIndex: 9999,
                animation: 'slideIn 0.3s ease',
            }}
        >
            <div
                style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px',
                }}
            >
                <span
                    style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: config.color,
                        flexShrink: 0,
                    }}
                />
                <span
                    style={{
                        fontWeight: 600,
                        color: '#1d1d1f',
                        fontSize: '14px',
                        flex: 1,
                    }}
                >
                    {config.text}
                </span>
            </div>

            {config.showReconnect && (
                <button
                    onClick={reconnect}
                    style={{
                        padding: '10px 16px',
                        background: '#0071e3',
                        color: 'white',
                        border: 'none',
                        borderRadius: '10px',
                        fontSize: '13px',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '6px',
                        transition: 'all 0.2s',
                    }}
                    onMouseEnter={(e) => {
                        e.currentTarget.style.background = '#0066cc';
                        e.currentTarget.style.transform = 'scale(1.02)';
                    }}
                    onMouseLeave={(e) => {
                        e.currentTarget.style.background = '#0071e3';
                        e.currentTarget.style.transform = 'scale(1)';
                    }}
                >
                    지금 재연결
                </button>
            )}

            {connectionState === 'failed' && (
                <div
                    style={{
                        fontSize: '12px',
                        color: '#86868b',
                        textAlign: 'center',
                        lineHeight: 1.5,
                    }}
                >
                    네트워크 상태를 확인하세요
                </div>
            )}

            <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
        </div>
    );
}

export default memo(ConnectionStatus);
