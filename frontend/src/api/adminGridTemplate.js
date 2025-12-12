/**
 * Admin Grid Template API Client
 * - 관리자 전용 템플릿 CRUD
 * - 백테스트 실행
 */
import axios from 'axios';

const API_BASE = '/api/v1';

const api = axios.create({
    baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export const adminGridTemplateAPI = {
    /**
     * 모든 템플릿 조회 (관리자)
     * @param {boolean} includeInactive - 비활성 템플릿 포함 여부
     */
    async list(includeInactive = false) {
        const response = await api.get('/admin/grid-templates', {
            params: { include_inactive: includeInactive },
        });
        return response.data;
    },

    /**
     * 템플릿 상세 조회
     * @param {number} templateId
     */
    async getDetail(templateId) {
        const response = await api.get(`/admin/grid-templates/${templateId}`);
        return response.data;
    },

    /**
     * 템플릿 생성
     * @param {Object} data - 템플릿 데이터
     */
    async create(data) {
        const response = await api.post('/admin/grid-templates', data);
        return response.data;
    },

    /**
     * 템플릿 수정
     * @param {number} templateId
     * @param {Object} data
     */
    async update(templateId, data) {
        const response = await api.put(`/admin/grid-templates/${templateId}`, data);
        return response.data;
    },

    /**
     * 템플릿 삭제 (비활성화)
     * @param {number} templateId
     */
    async delete(templateId) {
        const response = await api.delete(`/admin/grid-templates/${templateId}`);
        return response.data;
    },

    /**
     * 템플릿 공개/비공개 토글
     * @param {number} templateId
     */
    async toggle(templateId) {
        const response = await api.patch(`/admin/grid-templates/${templateId}/toggle`);
        return response.data;
    },

    /**
     * 백테스트 실행
     * @param {number} templateId
     * @param {Object} options - { days, granularity }
     */
    async runBacktest(templateId, options = {}) {
        const params = {
            days: options.days || 30,
            granularity: options.granularity || '5m',
        };
        const response = await api.post(
            `/admin/grid-templates/${templateId}/backtest`,
            null,
            { params }
        );
        return response.data;
    },

    /**
     * 백테스트 미리보기 (템플릿 저장 전)
     * @param {Object} data - 템플릿 설정
     */
    async previewBacktest(data) {
        const response = await api.post('/admin/grid-templates/backtest/preview', data);
        return response.data;
    },
};

export default adminGridTemplateAPI;
