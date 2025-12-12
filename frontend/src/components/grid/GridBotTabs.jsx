/**
 * GridBotTabs - AI 탭과 Manual 탭 전환
 *
 * AI 탭: 관리자가 만든 템플릿 목록 (TemplateList)
 * Manual 탭: 사용자가 직접 봇 생성 (기존 CreateGridBotModal)
 */
import React, { useState } from 'react';
import { Tabs, Button } from 'antd';
import { PlusOutlined, RobotOutlined, ToolOutlined } from '@ant-design/icons';
import { TemplateList } from './templates';
import CreateGridBotModal from './CreateGridBotModal';
import GridBotCard from './GridBotCard';
import './GridBotTabs.css';

const GridBotTabs = ({
    gridBots = [],            // 사용자의 그리드봇 목록
    availableBalance = 0,     // 가용 잔액
    onBotCreated,            // 봇 생성 완료 콜백
    onBotStart,              // 봇 시작
    onBotStop,               // 봇 중지
    onBotDelete,             // 봇 삭제
    onBotEdit,               // 봇 편집
}) => {
    const [activeTab, setActiveTab] = useState('ai');
    const [manualModalVisible, setManualModalVisible] = useState(false);

    const handleTabChange = (key) => {
        setActiveTab(key);
    };

    const tabItems = [
        {
            key: 'ai',
            label: (
                <span className="tab-label">
                    <RobotOutlined />
                    AI
                </span>
            ),
            children: (
                <TemplateList
                    availableBalance={availableBalance}
                    onBotCreated={onBotCreated}
                />
            ),
        },
        {
            key: 'manual',
            label: (
                <span className="tab-label">
                    <ToolOutlined />
                    Manual
                </span>
            ),
            children: (
                <div className="manual-tab-content">
                    {/* 직접 생성 버튼 */}
                    <Button
                        type="dashed"
                        icon={<PlusOutlined />}
                        onClick={() => setManualModalVisible(true)}
                        className="create-manual-button"
                    >
                        Create Grid Bot Manually
                    </Button>

                    {/* 내 그리드봇 목록 (Manual로 생성한 것만 표시할 수도 있음) */}
                    {gridBots.length > 0 && (
                        <div className="my-bots-section">
                            <h4>My Grid Bots</h4>
                            {gridBots.map((bot) => (
                                <GridBotCard
                                    key={bot.id}
                                    bot={bot}
                                    onStart={() => onBotStart?.(bot.id)}
                                    onStop={() => onBotStop?.(bot.id)}
                                    onDelete={() => onBotDelete?.(bot.id)}
                                    onEdit={() => onBotEdit?.(bot)}
                                />
                            ))}
                        </div>
                    )}
                </div>
            ),
        },
    ];

    return (
        <div className="grid-bot-tabs">
            <Tabs
                activeKey={activeTab}
                onChange={handleTabChange}
                items={tabItems}
                className="bitget-tabs"
            />

            {/* Manual 생성 모달 */}
            <CreateGridBotModal
                visible={manualModalVisible}
                onClose={() => setManualModalVisible(false)}
                onSuccess={onBotCreated}
                availableBalance={availableBalance}
            />
        </div>
    );
};

export default GridBotTabs;
