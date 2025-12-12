import apiClient from './client';

/**
 * Chart Annotations API
 *
 * 차트에 사용자 정의 어노테이션(메모, 선, 도형 등)을 관리하는 API
 */
export const annotationsAPI = {
  /**
   * 특정 심볼의 어노테이션 목록 조회
   * @param {string} symbol - 심볼 (예: BTCUSDT)
   * @param {boolean} includeInactive - 비활성 어노테이션 포함 여부
   * @returns {Promise<{symbol: string, annotations: Array, count: number}>}
   */
  getAnnotations: async (symbol, includeInactive = false) => {
    const response = await apiClient.get(`/annotations/${symbol}`, {
      params: { include_inactive: includeInactive }
    });
    return response.data;
  },

  /**
   * 단일 어노테이션 조회
   * @param {number} annotationId - 어노테이션 ID
   * @returns {Promise<Object>}
   */
  getAnnotation: async (annotationId) => {
    const response = await apiClient.get(`/annotations/detail/${annotationId}`);
    return response.data;
  },

  /**
   * 새 어노테이션 생성
   * @param {Object} data - 어노테이션 데이터
   * @param {string} data.symbol - 심볼
   * @param {string} data.annotation_type - 타입 (note, hline, vline, trendline, rectangle, price_level)
   * @param {string} [data.label] - 라벨
   * @param {string} [data.text] - 메모 내용
   * @param {number} [data.timestamp] - 시간 위치 (Unix timestamp)
   * @param {number} [data.price] - 가격 위치
   * @param {Object} [data.style] - 스타일 설정
   * @returns {Promise<Object>}
   */
  createAnnotation: async (data) => {
    const response = await apiClient.post('/annotations', data);
    return response.data;
  },

  /**
   * 어노테이션 수정
   * @param {number} annotationId - 어노테이션 ID
   * @param {Object} data - 수정할 데이터
   * @returns {Promise<Object>}
   */
  updateAnnotation: async (annotationId, data) => {
    const response = await apiClient.put(`/annotations/${annotationId}`, data);
    return response.data;
  },

  /**
   * 어노테이션 삭제
   * @param {number} annotationId - 어노테이션 ID
   * @returns {Promise<{success: boolean, message: string, deleted_id: number}>}
   */
  deleteAnnotation: async (annotationId) => {
    const response = await apiClient.delete(`/annotations/${annotationId}`);
    return response.data;
  },

  /**
   * 어노테이션 표시/숨김 토글
   * @param {number} annotationId - 어노테이션 ID
   * @returns {Promise<Object>}
   */
  toggleVisibility: async (annotationId) => {
    const response = await apiClient.post(`/annotations/${annotationId}/toggle`);
    return response.data;
  },

  /**
   * 어노테이션 잠금/해제 토글
   * @param {number} annotationId - 어노테이션 ID
   * @returns {Promise<Object>}
   */
  toggleLock: async (annotationId) => {
    const response = await apiClient.post(`/annotations/${annotationId}/lock`);
    return response.data;
  },

  /**
   * 특정 심볼의 모든 어노테이션 삭제 (잠금되지 않은 것만)
   * @param {string} symbol - 심볼
   * @returns {Promise<{success: boolean, symbol: string, deleted_count: number}>}
   */
  deleteAllForSymbol: async (symbol) => {
    const response = await apiClient.delete(`/annotations/symbol/${symbol}`);
    return response.data;
  },

  /**
   * 가격 알림 리셋 (다시 트리거 가능하도록)
   * @param {number} annotationId - 어노테이션 ID
   * @returns {Promise<Object>}
   */
  resetAlert: async (annotationId) => {
    const response = await apiClient.post(`/annotations/${annotationId}/reset-alert`);
    return response.data;
  },
};

/**
 * 어노테이션 타입 상수
 */
export const ANNOTATION_TYPES = {
  NOTE: 'note',              // 텍스트 메모
  HORIZONTAL_LINE: 'hline',  // 수평선 (지지/저항선)
  VERTICAL_LINE: 'vline',    // 수직선 (이벤트 마커)
  TRENDLINE: 'trendline',    // 추세선
  RECTANGLE: 'rectangle',    // 사각형 영역
  PRICE_LEVEL: 'price_level' // 가격 알림 레벨
};

/**
 * 기본 스타일 설정
 */
export const DEFAULT_STYLES = {
  [ANNOTATION_TYPES.NOTE]: {
    color: '#1890ff',
    fontSize: 12,
    backgroundColor: 'rgba(24, 144, 255, 0.1)'
  },
  [ANNOTATION_TYPES.HORIZONTAL_LINE]: {
    color: '#52c41a',
    lineWidth: 1,
    lineDash: [5, 5]
  },
  [ANNOTATION_TYPES.VERTICAL_LINE]: {
    color: '#faad14',
    lineWidth: 1,
    lineDash: [3, 3]
  },
  [ANNOTATION_TYPES.TRENDLINE]: {
    color: '#722ed1',
    lineWidth: 2
  },
  [ANNOTATION_TYPES.RECTANGLE]: {
    color: '#13c2c2',
    lineWidth: 1,
    backgroundColor: 'rgba(19, 194, 194, 0.1)'
  },
  [ANNOTATION_TYPES.PRICE_LEVEL]: {
    color: '#ff4d4f',
    lineWidth: 2,
    lineDash: [10, 5]
  }
};
