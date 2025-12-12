---
description: 프로젝트 시작 시 컨텍스트 로드 - 문서 확인 및 현재 상태 파악
---

# 🚀 프로젝트 컨텍스트 로드

이 워크플로우는 새로운 작업 세션을 시작할 때 사용합니다.

## 📋 수행 단계

### 1. 필수 문서 읽기

- `docs/MULTI_BOT_01_OVERVIEW.md` - 프로젝트 개요 및 작업 체크리스트
- `docs/CODE_REVIEW_AND_SECURITY_AUDIT.md` - 보안 이슈 (CRITICAL 항목 확인)

### 2. SKILL 파일 확인

- 백엔드 작업 시: `skills/backend-trading-api/SKILL.md`
- 프론트엔드 작업 시: `skills/frontend-trading-dashboard/SKILL.md`

### 3. 현재 상태 파악

- 실행 중인 서버 확인 (backend: 8000, frontend: 3000)
- 미완료 작업 확인 (MULTI_BOT_01_OVERVIEW.md 체크리스트)

### 4. 우선순위 확인

- 🔴 CRITICAL 보안 이슈 먼저 해결
- 🟠 차트 시그널 마커 구현 (`docs/CHART_SIGNAL_MARKERS_GUIDE.md`)
- 🟡 그리드 봇 UI 개발

## 🔑 테스트 계정

- 이메일: `admin@admin.com`
- 비밀번호: `admin123`

## ⚡ Quick Start

```bash
# 백엔드 실행
cd backend && python -m uvicorn src.main:app --reload --port 8000

# 프론트엔드 실행
cd frontend && npm run dev
```

## 📁 주요 파일 위치

| 구분 | 위치 |
|------|------|
| 봇 관리 페이지 | `frontend/src/pages/BotManagement.jsx` |
| 봇 API | `backend/src/api/bot_instances.py` |
| 잔고 할당 | `backend/src/services/allocation_manager.py` |
| 차트 | `frontend/src/components/TradingChart.jsx` |
