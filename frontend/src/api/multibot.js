/**
 * 멀티봇 트레이딩 API 클라이언트 v2.0
 *
 * 백엔드 엔드포인트: /multibot
 * 관련 문서: docs/MULTI_BOT_IMPLEMENTATION_PLAN.md
 *
 * v2.0 변경사항:
 * - 40% 마진 한도 제거 → 잔고 초과만 체크
 * - 최대 봇 10개 → 5개
 * - allocation_percent → allocated_amount (USDT)
 */

import apiClient from './client';

export const multibotAPI = {
    // ============================================================
    // 템플릿 API
    // ============================================================

    /**
     * 전략 템플릿 목록 조회
     * @param {Object} params - { symbol?, featured_only?, limit?, offset? }
     * @returns {Promise<{templates: Array, total: number, featured_count: number}>}
     */
    getTemplates: (params = {}) =>
        apiClient.get('/multibot/templates', { params }).then((r) => r.data),

    /**
     * 템플릿 상세 조회
     * @param {number} templateId
     * @returns {Promise<Object>} 템플릿 상세 정보
     */
    getTemplateDetail: (templateId) =>
        apiClient.get(`/multibot/templates/${templateId}`).then((r) => r.data),

    // ============================================================
    // 봇 관리 API
    // ============================================================

    /**
     * 봇 시작 (템플릿 기반)
     * @param {Object} data
     * @param {number} data.template_id - 템플릿 ID
     * @param {number} data.amount - 투자 금액 (USDT)
     * @param {string} [data.name] - 봇 이름 (선택)
     * @returns {Promise<{success: boolean, message: string, bot_id: number, data: Object}>}
     */
    startBot: (data) =>
        apiClient.post('/multibot/bots', data).then((r) => r.data),

    /**
     * 봇 중지
     * @param {number} botId - 봇 ID
     * @param {boolean} [closePositions=false] - 포지션 청산 여부
     * @returns {Promise<{success: boolean, message: string}>}
     */
    stopBot: (botId, closePositions = false) =>
        apiClient
            .delete(`/multibot/bots/${botId}`, {
                params: { close_positions: closePositions },
            })
            .then((r) => r.data),

    /**
     * 사용자 봇 목록 조회
     * @param {boolean} [runningOnly=false] - 실행 중인 봇만
     * @returns {Promise<Array>} 봇 목록
     */
    getBots: (runningOnly = false) =>
        apiClient
            .get('/multibot/bots', { params: { running_only: runningOnly } })
            .then((r) => r.data),

    /**
     * 봇 상세 조회
     * @param {number} botId
     * @returns {Promise<Object>} 봇 상세 정보
     */
    getBotDetail: (botId) =>
        apiClient.get(`/multibot/bots/${botId}`).then((r) => r.data),

    /**
     * 모든 봇 중지 (비상 정지)
     * @returns {Promise<{success: boolean, message: string, data: Object}>}
     */
    stopAllBots: () =>
        apiClient.post('/multibot/stop-all').then((r) => r.data),

    // ============================================================
    // 잔고 API
    // ============================================================

    /**
     * 잔고 요약 조회
     *
     * 반환 데이터:
     * - total_balance: 거래소 총 잔고
     * - used_amount: 활성 봇들의 할당 금액 합계
     * - available_amount: 사용 가능 금액
     * - active_bot_count: 활성 봇 개수
     * - max_bot_count: 최대 봇 개수 (5)
     * - total_pnl: 전체 수익금
     * - total_pnl_percent: 전체 수익률
     * - bots: 봇 목록 상세
     *
     * @returns {Promise<Object>} 잔고 요약
     */
    getSummary: () =>
        apiClient.get('/multibot/summary').then((r) => r.data),

    /**
     * 잔고 확인 (프리뷰용)
     *
     * 봇 시작 전 특정 금액으로 시작 가능한지 미리 확인
     *
     * @param {number} amount - 확인할 금액
     * @returns {Promise<{
     *   requested_amount: number,
     *   available: boolean,
     *   current_used: number,
     *   total_balance: number,
     *   after_used: number,
     *   message: string
     * }>}
     */
    checkBalance: (amount) =>
        apiClient.post('/multibot/check-balance', { amount }).then((r) => r.data),
};

export default multibotAPI;
