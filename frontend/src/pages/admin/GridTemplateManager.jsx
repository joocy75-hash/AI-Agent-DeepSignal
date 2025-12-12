/**
 * GridTemplateManager - 관리자용 템플릿 관리 페이지
 *
 * 기능:
 * - 템플릿 목록 조회/검색
 * - 템플릿 CRUD
 * - 백테스트 실행
 * - 통계 대시보드
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
    Typography,
    Button,
    Space,
    Card,
    Row,
    Col,
    Statistic,
    message,
    Spin,
    Switch,
} from 'antd';
import {
    PlusOutlined,
    ReloadOutlined,
    RobotOutlined,
    UserOutlined,
    DollarOutlined,
    StarFilled,
} from '@ant-design/icons';
import {
    TemplateTable,
    CreateTemplateModal,
    BacktestRunner,
} from '../../components/admin';
import { adminGridTemplateAPI } from '../../api/adminGridTemplate';
import './GridTemplateManager.css';

const { Title, Text } = Typography;

const GridTemplateManager = () => {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(false);
    const [includeInactive, setIncludeInactive] = useState(false);

    // 모달 상태
    const [createModalVisible, setCreateModalVisible] = useState(false);
    const [editTemplate, setEditTemplate] = useState(null);
    const [backtestTemplate, setBacktestTemplate] = useState(null);

    // 통계
    const [stats, setStats] = useState({
        total: 0,
        active: 0,
        featured: 0,
        totalUsers: 0,
        totalFunds: 0,
    });

    // 템플릿 목록 로드
    const loadTemplates = useCallback(async () => {
        setLoading(true);
        try {
            const data = await adminGridTemplateAPI.list(includeInactive);
            setTemplates(data);

            // 통계 계산
            const activeCount = data.filter((t) => t.is_active).length;
            const featuredCount = data.filter((t) => t.is_featured).length;
            const totalUsers = data.reduce((sum, t) => sum + (t.active_users || 0), 0);
            const totalFunds = data.reduce((sum, t) => sum + parseFloat(t.total_funds_in_use || 0), 0);

            setStats({
                total: data.length,
                active: activeCount,
                featured: featuredCount,
                totalUsers,
                totalFunds,
            });
        } catch (error) {
            console.error('Failed to load templates:', error);
            message.error('Failed to load templates');
        } finally {
            setLoading(false);
        }
    }, [includeInactive]);

    useEffect(() => {
        loadTemplates();
    }, [loadTemplates]);

    // 템플릿 생성/수정 완료
    const handleSaveComplete = () => {
        loadTemplates();
        setCreateModalVisible(false);
        setEditTemplate(null);
    };

    // 템플릿 삭제
    const handleDelete = async (templateId) => {
        try {
            await adminGridTemplateAPI.delete(templateId);
            message.success('Template deleted');
            loadTemplates();
        } catch (error) {
            console.error('Delete failed:', error);
            message.error('Failed to delete template');
        }
    };

    // 템플릿 토글
    const handleToggle = async (templateId) => {
        try {
            const result = await adminGridTemplateAPI.toggle(templateId);
            message.success(result.message);
            loadTemplates();
        } catch (error) {
            console.error('Toggle failed:', error);
            message.error('Failed to toggle template');
        }
    };

    // Featured 토글
    const handleFeatureToggle = async (templateId, isFeatured) => {
        try {
            await adminGridTemplateAPI.update(templateId, { is_featured: isFeatured });
            message.success(isFeatured ? 'Template featured' : 'Template unfeatured');
            loadTemplates();
        } catch (error) {
            console.error('Feature toggle failed:', error);
            message.error('Failed to update template');
        }
    };

    // 백테스트 완료
    const handleBacktestComplete = () => {
        loadTemplates();
    };

    return (
        <div className="grid-template-manager">
            {/* 페이지 헤더 */}
            <div className="page-header">
                <div className="header-left">
                    <Title level={2} className="page-title">
                        <RobotOutlined /> Grid Template Manager
                    </Title>
                    <Text className="page-subtitle">
                        Manage AI grid trading templates for users
                    </Text>
                </div>

                <Space className="header-actions">
                    <Space>
                        <Text className="switch-label">Show inactive:</Text>
                        <Switch
                            checked={includeInactive}
                            onChange={setIncludeInactive}
                        />
                    </Space>
                    <Button
                        icon={<ReloadOutlined />}
                        onClick={loadTemplates}
                        loading={loading}
                    >
                        Refresh
                    </Button>
                    <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => setCreateModalVisible(true)}
                    >
                        Create Template
                    </Button>
                </Space>
            </div>

            {/* 통계 카드 */}
            <Row gutter={[16, 16]} className="stats-row">
                <Col xs={12} sm={6}>
                    <Card className="stat-card">
                        <Statistic
                            title="Total Templates"
                            value={stats.total}
                            prefix={<RobotOutlined />}
                        />
                    </Card>
                </Col>
                <Col xs={12} sm={6}>
                    <Card className="stat-card">
                        <Statistic
                            title="Active Templates"
                            value={stats.active}
                            valueStyle={{ color: '#00b894' }}
                        />
                    </Card>
                </Col>
                <Col xs={12} sm={6}>
                    <Card className="stat-card">
                        <Statistic
                            title="Featured"
                            value={stats.featured}
                            prefix={<StarFilled style={{ color: '#faad14' }} />}
                        />
                    </Card>
                </Col>
                <Col xs={12} sm={6}>
                    <Card className="stat-card">
                        <Statistic
                            title="Active Users"
                            value={stats.totalUsers}
                            prefix={<UserOutlined />}
                        />
                    </Card>
                </Col>
            </Row>

            {/* 템플릿 테이블 */}
            <Card className="table-card">
                <Spin spinning={loading}>
                    <TemplateTable
                        templates={templates}
                        loading={loading}
                        onEdit={(template) => {
                            setEditTemplate(template);
                            setCreateModalVisible(true);
                        }}
                        onDelete={handleDelete}
                        onToggle={handleToggle}
                        onBacktest={(template) => setBacktestTemplate(template)}
                        onFeatureToggle={handleFeatureToggle}
                    />
                </Spin>
            </Card>

            {/* 생성/편집 모달 */}
            <CreateTemplateModal
                visible={createModalVisible}
                editTemplate={editTemplate}
                onClose={() => {
                    setCreateModalVisible(false);
                    setEditTemplate(null);
                }}
                onSuccess={handleSaveComplete}
            />

            {/* 백테스트 모달 */}
            <BacktestRunner
                visible={!!backtestTemplate}
                template={backtestTemplate}
                onClose={() => setBacktestTemplate(null)}
                onComplete={handleBacktestComplete}
            />
        </div>
    );
};

export default GridTemplateManager;
