/**
 * Admin Dashboard Page
 * 
 * 관리자용 메인 대시보드
 * - 그리드 템플릿 관리 링크
 * - 사용자 관리 (예정)
 * - 시스템 모니터링 (예정)
 */

import React from 'react';
import { Card, Row, Col, Typography, Button, Space, Statistic } from 'antd';
import {
    LineChartOutlined,
    UserOutlined,
    SettingOutlined,
    DashboardOutlined,
    RightOutlined,
    TeamOutlined,
    ApiOutlined,
    SafetyOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import './AdminDashboard.css';

const { Title, Text } = Typography;

const AdminDashboard = () => {
    const navigate = useNavigate();

    const menuItems = [
        {
            key: 'grid-templates',
            icon: <LineChartOutlined style={{ fontSize: 32, color: '#34c759' }} />,
            title: '그리드 템플릿 관리',
            description: 'AI 추천 그리드봇 템플릿을 생성하고 관리합니다',
            path: '/admin/grid-templates',
            available: true,
        },
        {
            key: 'users',
            icon: <TeamOutlined style={{ fontSize: 32, color: '#5856d6' }} />,
            title: '사용자 관리',
            description: '가입된 사용자를 관리하고 권한을 설정합니다',
            path: '/admin/users',
            available: false,
        },
        {
            key: 'api-status',
            icon: <ApiOutlined style={{ fontSize: 32, color: '#ff9500' }} />,
            title: 'API 상태',
            description: '외부 API 연결 상태 및 호출량을 모니터링합니다',
            path: '/admin/api-status',
            available: false,
        },
        {
            key: 'security',
            icon: <SafetyOutlined style={{ fontSize: 32, color: '#ff3b30' }} />,
            title: '보안 설정',
            description: 'IP 화이트리스트, Rate Limit 등 보안 설정 관리',
            path: '/admin/security',
            available: false,
        },
    ];

    return (
        <div className="admin-dashboard">
            {/* 헤더 */}
            <div className="admin-header">
                <div className="admin-header-content">
                    <DashboardOutlined className="admin-header-icon" />
                    <div>
                        <Title level={2} style={{ margin: 0, color: '#1d1d1f' }}>
                            관리자 대시보드
                        </Title>
                        <Text style={{ color: '#86868b' }}>
                            시스템 설정 및 템플릿을 관리합니다
                        </Text>
                    </div>
                </div>
            </div>

            {/* 메뉴 카드 그리드 */}
            <Row gutter={[20, 20]} className="admin-menu-grid">
                {menuItems.map(item => (
                    <Col xs={24} sm={12} lg={6} key={item.key}>
                        <Card
                            className={`admin-menu-card ${!item.available ? 'disabled' : ''}`}
                            hoverable={item.available}
                            onClick={() => item.available && navigate(item.path)}
                        >
                            <div className="menu-card-icon">
                                {item.icon}
                            </div>
                            <Title level={5} className="menu-card-title">
                                {item.title}
                            </Title>
                            <Text className="menu-card-description">
                                {item.description}
                            </Text>
                            {item.available ? (
                                <div className="menu-card-action">
                                    <span>관리</span>
                                    <RightOutlined />
                                </div>
                            ) : (
                                <div className="menu-card-coming-soon">
                                    Coming Soon
                                </div>
                            )}
                        </Card>
                    </Col>
                ))}
            </Row>
        </div>
    );
};

export default AdminDashboard;
