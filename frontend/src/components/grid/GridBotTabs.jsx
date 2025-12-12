/**
 * GridBotTabs - 그리드 봇 템플릿 탭
 */
import React from 'react';
import { LineChartOutlined } from '@ant-design/icons';
import { TemplateList } from './templates';
import './GridBotTabs.css';

const GridBotTabs = ({
    availableBalance = 0,
    onBotCreated,
}) => {
    return (
        <div className="grid-bot-tabs">
            <div className="ai-tab-header">
                <LineChartOutlined style={{ marginRight: 8 }} />
                <span>AI 추천 그리드 전략</span>
            </div>
            <TemplateList
                availableBalance={availableBalance}
                onBotCreated={onBotCreated}
            />
        </div>
    );
};

export default GridBotTabs;
