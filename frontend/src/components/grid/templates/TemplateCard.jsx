/**
 * TemplateCard - 그리드 봇 템플릿 카드
 * 
 * 라이트 모드 + 한국어 UI
 */
import React from 'react';
import { Button, Tag, Tooltip } from 'antd';
import { UserOutlined, RiseOutlined, ArrowUpOutlined, ArrowDownOutlined } from '@ant-design/icons';
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

    const getPeriodLabel = (period) => {
        if (!period) return '7-30일';
        return period.replace('days', '일').replace('-', '~');
    };

    return (
        <div className={`template-card ${is_featured ? 'featured' : ''}`}>
            {/* 상단: 심볼 + 사용 버튼 */}
            <div className="template-card-header">
                <div className="template-symbol-section">
                    <h3 className="template-symbol">{symbol}</h3>
                    <div className="template-tags">
                        <Tag className="tag-type">그리드 봇</Tag>
                        <Tag className={`tag-direction ${isLong ? 'long' : 'short'}`}>
                            {isLong ? <><ArrowUpOutlined /> 롱</> : <><ArrowDownOutlined /> 숏</>}
                        </Tag>
                        <Tag className="tag-leverage">{leverage}배</Tag>
                    </div>
                </div>

                <Button
                    type="primary"
                    className="use-button"
                    onClick={() => onUse(template)}
                    loading={loading}
                >
                    사용하기
                </Button>
            </div>

            {/* 중앙: 수익률 + 차트 */}
            <div className="template-card-body">
                <div className="roi-section">
                    <span className="roi-label">30일 예상 수익률</span>
                    <span className={`roi-value ${isPositiveRoi ? 'positive' : 'negative'}`}>
                        {isPositiveRoi ? '+' : ''}{roiValue.toFixed(1)}%
                    </span>
                </div>

                <div className="chart-section">
                    <MiniRoiChart
                        data={roi_chart || []}
                        width={120}
                        height={50}
                        color={isPositiveRoi ? '#34c759' : '#ff3b30'}
                    />
                </div>
            </div>

            {/* 하단: 추가 정보 */}
            <div className="template-card-footer">
                <div className="footer-row">
                    <span className="footer-label">권장 운용 기간</span>
                    <span className="footer-value">{getPeriodLabel(recommended_period)}</span>
                </div>
                <div className="footer-row">
                    <span className="footer-label">최소 금액</span>
                    <span className="footer-value">{parseFloat(min_investment || 0).toFixed(0)} USDT</span>
                    <span className="user-count">
                        <UserOutlined /> {active_users || 0}명
                    </span>
                </div>
            </div>

            {/* 추천 배지 */}
            {is_featured && (
                <div className="featured-badge">
                    <RiseOutlined /> 추천
                </div>
            )}
        </div>
    );
};

export default TemplateCard;
