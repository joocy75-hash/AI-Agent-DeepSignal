import apiClient from './client';

// Analytics API 클라이언트 (최적화 버전)
export const analyticsAPI = {
    /**
     * 대시보드 요약 데이터 가져오기 (통합 API - 권장)
     * 여러 개의 API 호출을 한번에 처리 (5개 -> 1개)
     * @returns {Promise} 대시보드 요약 데이터
     */
    getDashboardSummary: async () => {
        try {
            const response = await apiClient.get('/analytics/dashboard-summary');
            return response.data;
        } catch (error) {
            console.error('[Analytics API] Dashboard summary error:', error);
            throw error;
        }
    },

    /**
     * 자산 곡선 데이터 가져오기
     * @param {string} period - 기간 (1d, 1w, 1m, 3m, 1y, all)
     * @returns {Promise} 자산 곡선 데이터
     */
    getEquityCurve: async (period = '1m') => {
        try {
            const response = await apiClient.get('/analytics/equity-curve', {
                params: { period },
            });
            return response.data;
        } catch (error) {
            console.error('[Analytics API] Equity curve error:', error);
            throw error;
        }
    },

    /**
     * 리스크 지표 가져오기
     * @returns {Promise} 리스크 지표 데이터
     */
    getRiskMetrics: async () => {
        try {
            const response = await apiClient.get('/analytics/risk-metrics');
            return response.data;
        } catch (error) {
            console.error('[Analytics API] Risk metrics error:', error);
            throw error;
        }
    },

    /**
     * 성과 지표 가져오기
     * @param {string} period - 기간
     * @returns {Promise} 성과 지표 데이터
     */
    getPerformanceMetrics: async (period = '1m') => {
        try {
            const response = await apiClient.get('/analytics/performance', {
                params: { period },
            });
            return response.data;
        } catch (error) {
            console.error('[Analytics API] Performance metrics error:', error);
            throw error;
        }
    },

    /**
     * 기간별 보고서 가져오기
     * @param {string} reportType - 보고서 타입 (daily, weekly, monthly, quarterly, yearly)
     * @param {string} startDate - 시작일 (YYYY-MM-DD)
     * @param {string} endDate - 종료일 (YYYY-MM-DD)
     * @returns {Promise} 보고서 데이터
     */
    getReport: async (reportType = 'monthly', startDate, endDate) => {
        try {
            const response = await apiClient.get('/analytics/report', {
                params: {
                    type: reportType,
                    start_date: startDate,
                    end_date: endDate,
                },
            });
            return response.data;
        } catch (error) {
            console.error('[Analytics API] Report error:', error);
            throw error;
        }
    },
};

// 편의 함수 exports
export const getDashboardSummary = analyticsAPI.getDashboardSummary;
export const getEquityCurve = analyticsAPI.getEquityCurve;
export const getPerformance = analyticsAPI.getPerformanceMetrics;
export const getRiskMetrics = analyticsAPI.getRiskMetrics;

export default analyticsAPI;

