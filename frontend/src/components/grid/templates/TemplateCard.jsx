/**
 * TemplateCard - Bitget 스타일 템플릿 카드
 *
 * 표시 정보:
 * - 심볼, 방향, 레버리지 태그
 * - 30D ROI (%)
 * - 미니 차트
 * - 추천 투자 기간
 * - 최소 투자금액
 * - 사용자 수
 * - Use 버튼
 */
import React from 'react';
import { Button, Tag } from 'antd';
import { UserOutlined, RiseOutlined } from '@ant-design/icons';
import MiniRoiChart from './MiniRoiChart';
import './TemplateCard.css';

const TemplateCard = ({
    template,
    onUse,
    loading = false,
}) => {
    const {
        id,
        symbol,
        direction,
        leverage,
        backtest_roi_30d,
        backtest_max_drawdown,
        roi_chart,
        recommended_period,
        min_investment,
        active_users,
        is_featured,
    } = template;

    const isLong = direction === 'long';
    const roiValue = backtest_roi_30d || 0;
    const isPositiveRoi = roiValue >= 0;

    return (
        <div className={`template-card ${is_featured ? 'featured' : ''}`}>
            {/* 상단 영역: 심볼 + Use 버튼 */}
            <div className="template-card-header">
                <div className="template-symbol-section">
                    <h3 className="template-symbol">{symbol}</h3>
                    <div className="template-tags">
                        <Tag className="tag-type">Futures grid</Tag>
                        <Tag className={`tag-direction ${isLong ? 'long' : 'short'}`}>
                            {isLong ? 'Long' : 'Short'}
                        </Tag>
                        <Tag className="tag-leverage">{leverage}X</Tag>
                    </div>
                </div>

                <Button
                    type="default"
                    className="use-button"
                    onClick={() => onUse(template)}
                    loading={loading}
                >
                    Use
                </Button>
            </div>

            {/* 중앙 영역: ROI + 차트 */}
            <div className="template-card-body">
                <div className="roi-section">
                    <span className="roi-label">30D backtested ROI</span>
                    <span className={`roi-value ${isPositiveRoi ? 'positive' : 'negative'}`}>
                        {isPositiveRoi ? '+' : ''}{roiValue.toFixed(2)}%
                    </span>
                </div>

                <div className="chart-section">
                    <MiniRoiChart
                        data={roi_chart || []}
                        width={120}
                        height={50}
                        color={isPositiveRoi ? '#00b894' : '#e74c3c'}
                    />
                </div>
            </div>

            {/* 하단 영역: 추가 정보 */}
            <div className="template-card-footer">
                <div className="footer-row">
                    <span className="footer-label">Recommended investment period</span>
                    <span className="footer-value">{recommended_period || '7-30 days'}</span>
                </div>
                <div className="footer-row">
                    <span className="footer-label">Min. investment</span>
                    <span className="footer-value">{parseFloat(min_investment || 0).toFixed(2)} USDT</span>

                    <span className="user-count">
                        <UserOutlined /> {active_users || 0}
                    </span>
                </div>
            </div>

            {/* Featured 배지 */}
            {is_featured && (
                <div className="featured-badge">
                    <RiseOutlined /> HOT
                </div>
            )}
        </div>
    );
};

export default TemplateCard;
