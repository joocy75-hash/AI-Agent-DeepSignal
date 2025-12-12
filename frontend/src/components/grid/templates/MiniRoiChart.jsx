/**
 * MiniRoiChart - 30일 ROI 미니 차트
 *
 * Bitget 스타일의 작은 선형 차트
 * - 녹색 선 (상승)
 * - 빨간색 선 (하락)
 * - 반응형 크기
 */
import React, { useMemo } from 'react';

const MiniRoiChart = ({
    data = [],           // ROI 데이터 배열 (30개)
    width = 100,
    height = 40,
    color = '#00b894',   // 기본 녹색
    strokeWidth = 1.5,
}) => {
    const pathData = useMemo(() => {
        if (!data || data.length < 2) return '';

        const minVal = Math.min(...data);
        const maxVal = Math.max(...data);
        const range = maxVal - minVal || 1;

        const points = data.map((val, idx) => {
            const x = (idx / (data.length - 1)) * width;
            const y = height - ((val - minVal) / range) * height * 0.8 - height * 0.1;
            return `${x},${y}`;
        });

        return `M ${points.join(' L ')}`;
    }, [data, width, height]);

    if (!data || data.length < 2) {
        return (
            <div
                style={{
                    width,
                    height,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#666',
                    fontSize: '10px',
                }}
            >
                No data
            </div>
        );
    }

    // 마지막 값이 시작값보다 높으면 녹색, 낮으면 빨간색
    const isPositive = data[data.length - 1] >= data[0];
    const lineColor = isPositive ? color : '#e74c3c';

    // 유니크 ID 생성 (같은 페이지에 여러 차트가 있을 수 있음)
    const gradientId = `gradient-${isPositive ? 'green' : 'red'}-${Math.random().toString(36).substr(2, 9)}`;

    return (
        <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
            {/* 그라데이션 정의 */}
            <defs>
                <linearGradient id={gradientId} x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stopColor={lineColor} stopOpacity="0.3" />
                    <stop offset="100%" stopColor={lineColor} stopOpacity="0" />
                </linearGradient>
            </defs>

            {/* 영역 채우기 */}
            <path
                d={`${pathData} L ${width},${height} L 0,${height} Z`}
                fill={`url(#${gradientId})`}
            />

            {/* 선 */}
            <path
                d={pathData}
                fill="none"
                stroke={lineColor}
                strokeWidth={strokeWidth}
                strokeLinecap="round"
                strokeLinejoin="round"
            />
        </svg>
    );
};

export default MiniRoiChart;
