/**
 * TrendBotTabs - AI 추세 봇 템플릿 탭
 */
import React from 'react';
import { ThunderboltOutlined } from '@ant-design/icons';
import { TrendTemplateList } from './templates';
import './TrendBotTabs.css';

const TrendBotTabs = ({
    availableBalance = 0,
    onBotCreated,
}) => {
    return (
        <div className="trend-bot-tabs">
            <div className="ai-trend-header">
                <ThunderboltOutlined style={{ marginRight: 8 }} />
                <span>AI 추천 추세 전략</span>
            </div>
            <TrendTemplateList
                availableBalance={availableBalance}
                onBotCreated={onBotCreated}
            />
        </div>
    );
};

export default TrendBotTabs;
