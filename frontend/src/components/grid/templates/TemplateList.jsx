/**
 * TemplateList - AI 탭 컨텐츠
 *
 * 템플릿 목록 표시:
 * - 로딩 상태
 * - 에러 처리
 * - 빈 상태
 * - 템플릿 카드 그리드
 */
import React, { useState, useEffect } from 'react';
import { Spin, Empty, Alert, Input, Select, Row, Col } from 'antd';
import { SearchOutlined } from '@ant-design/icons';
import { gridTemplateAPI } from '../../../api/gridTemplate';
import TemplateCard from './TemplateCard';
import UseTemplateModal from './UseTemplateModal';
import './TemplateList.css';

const { Option } = Select;

const TemplateList = ({ availableBalance = 0 }) => {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [sortBy, setSortBy] = useState('roi');

    // 모달 상태
    const [selectedTemplate, setSelectedTemplate] = useState(null);
    const [modalVisible, setModalVisible] = useState(false);

    // 템플릿 목록 로드
    useEffect(() => {
        loadTemplates();
    }, []);

    const loadTemplates = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await gridTemplateAPI.list({ limit: 50 });

            if (response.success) {
                setTemplates(response.data || []);
            } else {
                throw new Error(response.message || 'Failed to load templates');
            }
        } catch (err) {
            console.error('Failed to load templates:', err);
            setError(err.response?.data?.detail || err.message || 'Failed to load templates');
        } finally {
            setLoading(false);
        }
    };

    // Use 버튼 클릭
    const handleUse = (template) => {
        setSelectedTemplate(template);
        setModalVisible(true);
    };

    // 모달 닫기
    const handleModalClose = () => {
        setModalVisible(false);
        setSelectedTemplate(null);
    };

    // 봇 생성 성공
    const handleSuccess = (result) => {
        console.log('Bot created:', result);
        // 성공 시 목록 새로고침하거나 상세 페이지로 이동
        loadTemplates();
    };

    // 필터링 및 정렬
    const filteredTemplates = templates
        .filter(t =>
            t.symbol.toLowerCase().includes(searchTerm.toLowerCase())
        )
        .sort((a, b) => {
            switch (sortBy) {
                case 'roi':
                    return (b.backtest_roi_30d || 0) - (a.backtest_roi_30d || 0);
                case 'users':
                    return (b.active_users || 0) - (a.active_users || 0);
                case 'symbol':
                    return a.symbol.localeCompare(b.symbol);
                default:
                    return 0;
            }
        });

    if (loading) {
        return (
            <div className="template-list-loading">
                <Spin size="large" />
                <p>Loading AI strategies...</p>
            </div>
        );
    }

    if (error) {
        return (
            <Alert
                type="error"
                message="Error"
                description={error}
                showIcon
                action={
                    <a onClick={loadTemplates}>Retry</a>
                }
            />
        );
    }

    return (
        <div className="template-list">
            {/* 필터 바 */}
            <div className="template-list-header">
                <Input
                    placeholder="Search by symbol..."
                    prefix={<SearchOutlined />}
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                    className="search-input"
                    allowClear
                />
                <Select
                    value={sortBy}
                    onChange={setSortBy}
                    className="sort-select"
                >
                    <Option value="roi">Highest ROI</Option>
                    <Option value="users">Most Users</Option>
                    <Option value="symbol">Symbol A-Z</Option>
                </Select>
            </div>

            {/* 템플릿 카드 그리드 */}
            {filteredTemplates.length === 0 ? (
                <Empty
                    description="No templates found"
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
            ) : (
                <Row gutter={[16, 16]}>
                    {filteredTemplates.map(template => (
                        <Col key={template.id} xs={24} sm={24} md={12} lg={8} xl={8}>
                            <TemplateCard
                                template={template}
                                onUse={handleUse}
                            />
                        </Col>
                    ))}
                </Row>
            )}

            {/* Use 모달 */}
            <UseTemplateModal
                visible={modalVisible}
                template={selectedTemplate}
                onClose={handleModalClose}
                onSuccess={handleSuccess}
                availableBalance={availableBalance}
            />
        </div>
    );
};

export default TemplateList;
