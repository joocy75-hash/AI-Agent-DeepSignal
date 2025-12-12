/**
 * TemplateTable - 템플릿 목록 테이블 (관리자)
 *
 * 기능:
 * - 템플릿 목록 표시
 * - 정렬/필터
 * - 액션 버튼 (편집, 삭제, 토글, 백테스트)
 */
import React from 'react';
import {
    Table,
    Tag,
    Button,
    Space,
    Switch,
    Tooltip,
    Popconfirm,
    Badge,
} from 'antd';
import {
    EditOutlined,
    DeleteOutlined,
    ExperimentOutlined,
    StarOutlined,
    StarFilled,
} from '@ant-design/icons';
import { MiniRoiChart } from '../grid/templates';
import './TemplateTable.css';

const TemplateTable = ({
    templates = [],
    loading = false,
    onEdit,
    onDelete,
    onToggle,
    onBacktest,
    onFeatureToggle,
}) => {
    const columns = [
        {
            title: 'Symbol',
            dataIndex: 'symbol',
            key: 'symbol',
            width: 120,
            render: (symbol, record) => (
                <div className="symbol-cell">
                    <span className="symbol-text">{symbol}</span>
                    <div className="symbol-tags">
                        <Tag color={record.direction === 'long' ? 'green' : 'red'}>
                            {record.direction?.toUpperCase()}
                        </Tag>
                        <Tag>{record.leverage}X</Tag>
                    </div>
                </div>
            ),
        },
        {
            title: 'Grid Settings',
            key: 'gridSettings',
            width: 180,
            render: (_, record) => (
                <div className="grid-settings-cell">
                    <div>Range: {parseFloat(record.lower_price).toFixed(2)} - {parseFloat(record.upper_price).toFixed(2)}</div>
                    <div>Grids: {record.grid_count} ({record.grid_mode})</div>
                </div>
            ),
        },
        {
            title: '30D ROI',
            dataIndex: 'backtest_roi_30d',
            key: 'roi',
            width: 150,
            sorter: (a, b) => (a.backtest_roi_30d || 0) - (b.backtest_roi_30d || 0),
            render: (roi, record) => (
                <div className="roi-cell">
                    {roi !== null && roi !== undefined ? (
                        <>
                            <span className={`roi-value ${roi >= 0 ? 'positive' : 'negative'}`}>
                                {roi >= 0 ? '+' : ''}{roi.toFixed(2)}%
                            </span>
                            {record.backtest_roi_history && (
                                <MiniRoiChart
                                    data={record.backtest_roi_history}
                                    width={60}
                                    height={24}
                                    color={roi >= 0 ? '#00b894' : '#e74c3c'}
                                />
                            )}
                        </>
                    ) : (
                        <span className="no-data">Not tested</span>
                    )}
                </div>
            ),
        },
        {
            title: 'MDD',
            dataIndex: 'backtest_max_drawdown',
            key: 'mdd',
            width: 80,
            render: (mdd) => (
                mdd !== null && mdd !== undefined ? (
                    <span className="mdd-value">{mdd.toFixed(2)}%</span>
                ) : '-'
            ),
        },
        {
            title: 'Min Investment',
            dataIndex: 'min_investment',
            key: 'minInvestment',
            width: 120,
            render: (val) => `${parseFloat(val).toFixed(2)} USDT`,
        },
        {
            title: 'Users',
            key: 'users',
            width: 100,
            render: (_, record) => (
                <div className="users-cell">
                    <div>Active: {record.active_users || 0}</div>
                    <div className="total-users">Total: {record.total_users || 0}</div>
                </div>
            ),
        },
        {
            title: 'Status',
            key: 'status',
            width: 100,
            render: (_, record) => (
                <div className="status-cell">
                    <Switch
                        checked={record.is_active}
                        onChange={() => onToggle?.(record.id)}
                        checkedChildren="Active"
                        unCheckedChildren="Hidden"
                    />
                    {record.is_featured && (
                        <Badge status="success" text="Featured" />
                    )}
                </div>
            ),
        },
        {
            title: 'Actions',
            key: 'actions',
            width: 180,
            fixed: 'right',
            render: (_, record) => (
                <Space size="small">
                    <Tooltip title={record.is_featured ? 'Unfeature' : 'Feature'}>
                        <Button
                            type="text"
                            icon={record.is_featured ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
                            onClick={() => onFeatureToggle?.(record.id, !record.is_featured)}
                        />
                    </Tooltip>

                    <Tooltip title="Run Backtest">
                        <Button
                            type="text"
                            icon={<ExperimentOutlined />}
                            onClick={() => onBacktest?.(record)}
                        />
                    </Tooltip>

                    <Tooltip title="Edit">
                        <Button
                            type="text"
                            icon={<EditOutlined />}
                            onClick={() => onEdit?.(record)}
                        />
                    </Tooltip>

                    <Popconfirm
                        title="Delete this template?"
                        description="This will hide the template from users."
                        onConfirm={() => onDelete?.(record.id)}
                        okText="Delete"
                        cancelText="Cancel"
                    >
                        <Tooltip title="Delete">
                            <Button
                                type="text"
                                danger
                                icon={<DeleteOutlined />}
                            />
                        </Tooltip>
                    </Popconfirm>
                </Space>
            ),
        },
    ];

    return (
        <Table
            columns={columns}
            dataSource={templates}
            rowKey="id"
            loading={loading}
            pagination={{ pageSize: 20 }}
            scroll={{ x: 1200 }}
            className="template-table"
        />
    );
};

export default TemplateTable;
