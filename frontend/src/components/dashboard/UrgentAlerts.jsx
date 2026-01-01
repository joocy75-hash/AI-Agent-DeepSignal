import { useEffect, useState } from 'react';
import { Alert, Card, List } from 'antd';
import {
    WarningOutlined,
    CloseCircleOutlined,
    InfoCircleOutlined,
    ClockCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import 'dayjs/locale/ko';
import apiClient from '../../api/client';

dayjs.extend(relativeTime);
dayjs.locale('ko');

export default function UrgentAlerts() {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadAlerts();
        const interval = setInterval(loadAlerts, 10000); // 10초마다 갱신
        return () => clearInterval(interval);
    }, []);

    const loadAlerts = async () => {
        try {
            const response = await apiClient.get('/alerts/urgent');
            setAlerts(response.data.alerts || []);
            setLoading(false);
        } catch (error) {
            console.error('[UrgentAlerts] Error loading alerts:', error);
            setAlerts([]);
            setLoading(false);
        }
    };

    const getAlertConfig = (level) => {
        const configs = {
            ERROR: {
                type: 'error',
                icon: <CloseCircleOutlined />,
                color: '#f5222d',
            },
            WARNING: {
                type: 'warning',
                icon: <WarningOutlined />,
                color: '#faad14',
            },
            INFO: {
                type: 'info',
                icon: <InfoCircleOutlined />,
                color: '#1890ff',
            },
        };
        return configs[level] || configs.INFO;
    };

    if (loading) {
        return null;
    }

    if (alerts.length === 0) {
        return null; // 알림이 없으면 표시하지 않음
    }

    return (
        <Card
            title={
                <span>
                    <WarningOutlined style={{ marginRight: 8, color: '#faad14' }} />
                    긴급 알림
                </span>
            }
            size="small"
            style={{ marginBottom: 16 }}
        >
            <List
                dataSource={alerts}
                renderItem={(alert) => {
                    const config = getAlertConfig(alert.level);
                    return (
                        <Alert
                            message={
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <span>{alert.message}</span>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                                        <span style={{ fontSize: 12, color: '#888' }}>
                                            <ClockCircleOutlined style={{ marginRight: 4 }} />
                                            {dayjs(alert.timestamp).fromNow()}
                                        </span>
                                    </div>
                                </div>
                            }
                            type={config.type}
                            showIcon
                            icon={config.icon}
                            style={{ marginBottom: 8 }}
                        />
                    );
                }}
            />
        </Card>
    );
}
