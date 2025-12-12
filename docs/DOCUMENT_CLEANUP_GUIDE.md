# 📋 프로젝트 문서 및 코드 정리 가이드

> 작성일: 2025-12-12
> 목적: 다음 작업자가 혼란 없이 작업할 수 있도록 문서/코드 구조 정리

---

## 📁 현재 문서 구조

### ✅ 현재 유효한 핵심 문서 (docs/)

| 파일 | 설명 | 상태 |
|------|------|------|
| `SECURITY_PRIORITY_TASKS.md` | **📌 메인 작업 목록** - 모든 TODO 항목 종합 | ✅ 최신 |
| `CODE_REVIEW_AND_SECURITY_AUDIT.md` | 보안 감사 상세 보고서 | ✅ 유지 |
| `PROJECT_HANDOVER.md` | 프로젝트 인수인계 문서 | ✅ 유지 |
| `TEST_IMPLEMENTATION_HANDOVER.md` | 테스트 인수인계 | ✅ 유지 |
| `MULTI_BOT_01_OVERVIEW.md` | 다중 봇 설계 개요 | ✅ 유지 |
| `MULTI_BOT_02_DATABASE.md` | 다중 봇 DB 스키마 | ✅ 유지 |
| `MULTI_BOT_03_IMPLEMENTATION.md` | 다중 봇 구현 상세 | ✅ 유지 |
| `CHART_SIGNAL_MARKERS_GUIDE.md` | 차트 시그널 마커 가이드 | ✅ 유지 |
| `BACKEND_ARCHITECTURE.md` | 백엔드 아키텍처 | ✅ 참조용 |
| `FRONTEND_ARCHITECTURE.md` | 프론트엔드 아키텍처 | ✅ 참조용 |
| `FRONTEND_CHART_IMPLEMENTATION.md` | 차트 구현 상세 | ✅ 참조용 |
| `BACKEND_IMPROVEMENT_GUIDE.md` | 백엔드 개선 가이드 | ⚠️ 일부 완료 |

### ⚠️ 아카이브 대상 문서 (이동 필요)

| 파일 | 이유 | 조치 |
|------|------|------|
| `docs/SECURITY_AUDIT_REPORT.md` | `CODE_REVIEW_AND_SECURITY_AUDIT.md`와 중복 | → `docs/archive/` 이동 |
| `docs/GRID_BOT_REMAINING_TASKS.md` | `SECURITY_PRIORITY_TASKS.md`에 통합됨 | → `docs/archive/` 이동 |

### ❌ 삭제/아카이브 대상 (루트 디렉토리)

| 파일 | 이유 | 조치 |
|------|------|------|
| `BALANCE_API_DEBUG_REPORT.md` | 문제 해결 완료 | → `docs/archive/` 이동 |
| `SECURITY_AND_CLEANUP.md` | `SECURITY_PRIORITY_TASKS.md`에 통합됨 | → `docs/archive/` 이동 |
| `STRATEGY_CLEANUP.md` | 작업 완료 | → `docs/archive/` 이동 |
| `backend/PHASE1_SECURITY_COMPLETED.md` | 작업 완료 | → `docs/archive/` 이동 |

---

## 🗑️ 정리 명령어 (수동 실행)

```bash
cd /Users/mr.joo/Desktop/auto-dashboard

# docs/archive 디렉토리가 없으면 생성
mkdir -p docs/archive

# 중복/완료된 문서 아카이브로 이동
mv docs/SECURITY_AUDIT_REPORT.md docs/archive/SECURITY_AUDIT_REPORT_OLD_20251210.md
mv docs/GRID_BOT_REMAINING_TASKS.md docs/archive/GRID_BOT_REMAINING_TASKS_OLD.md

# 루트 디렉토리 문서 정리
mv BALANCE_API_DEBUG_REPORT.md docs/archive/BALANCE_API_DEBUG_REPORT_RESOLVED.md
mv SECURITY_AND_CLEANUP.md docs/archive/SECURITY_AND_CLEANUP_OLD.md
mv STRATEGY_CLEANUP.md docs/archive/STRATEGY_CLEANUP_COMPLETED.md
mv backend/PHASE1_SECURITY_COMPLETED.md docs/archive/PHASE1_SECURITY_COMPLETED.md

echo "문서 정리 완료!"
```

---

## 🧹 중복 코드 정리

### 1. Rate Limit 미들웨어 중복

| 파일 | 설명 | 조치 |
|------|------|------|
| `middleware/rate_limit.py` | 레거시 (IP 기반만) | ❌ 삭제 대상 |
| `middleware/rate_limit_improved.py` | 개선판 (IP + JWT) | ✅ 사용 중 |

**현재 main.py에서 사용 중인 것**: `rate_limit_improved.py`
**rate_limit.py는 사용되지 않음** → 삭제 가능

```bash
# rate_limit.py 삭제 (선택사항)
rm backend/src/middleware/rate_limit.py
rm backend/src/middleware/__pycache__/rate_limit.cpython-311.pyc
```

### 2. LBank WebSocket 파일 (이미 삭제됨)

이전에 `lbank_ws.py`와 `lbank_ws_improved.py` 중복이 있었으나 정리 완료됨.

---

## 📂 최종 권장 문서 구조

```
/Users/mr.joo/Desktop/auto-dashboard/
├── README.md                          # 프로젝트 개요
├── docs/
│   ├── SECURITY_PRIORITY_TASKS.md     # ⭐ 메인 작업 목록 (가장 중요!)
│   ├── CODE_REVIEW_AND_SECURITY_AUDIT.md  # 보안 감사 상세
│   ├── PROJECT_HANDOVER.md            # 인수인계
│   ├── TEST_IMPLEMENTATION_HANDOVER.md # 테스트 인수인계
│   ├── MULTI_BOT_01_OVERVIEW.md       # 다중 봇 설계
│   ├── MULTI_BOT_02_DATABASE.md       # 다중 봇 DB
│   ├── MULTI_BOT_03_IMPLEMENTATION.md # 다중 봇 구현
│   ├── CHART_SIGNAL_MARKERS_GUIDE.md  # 차트 가이드
│   ├── BACKEND_ARCHITECTURE.md        # 백엔드 구조 (참조)
│   ├── FRONTEND_ARCHITECTURE.md       # 프론트엔드 구조 (참조)
│   ├── DOCUMENT_CLEANUP_GUIDE.md      # 이 파일
│   └── archive/                       # 아카이브 (오래된 문서)
│       ├── SECURITY_AUDIT_REPORT_OLD_20251210.md
│       ├── GRID_BOT_REMAINING_TASKS_OLD.md
│       ├── BALANCE_API_DEBUG_REPORT_RESOLVED.md
│       └── ...
├── skills/
│   ├── backend-trading-api/SKILL.md   # 백엔드 개발 가이드
│   └── frontend-trading-dashboard/SKILL.md # 프론트엔드 개발 가이드
├── workflows/
│   ├── start.md                       # 시작 워크플로우
│   ├── backend.md                     # 백엔드 워크플로우
│   ├── frontend.md                    # 프론트엔드 워크플로우
│   ├── deploy.md                      # 배포 워크플로우
│   └── security.md                    # 보안 워크플로우
└── ...
```

---

## 📌 다음 작업자 안내

### 1. 작업 시작 전 필수 확인

1. **`docs/SECURITY_PRIORITY_TASKS.md`** - 현재 작업 목록 확인
2. **`skills/backend-trading-api/SKILL.md`** - 백엔드 개발 가이드
3. **`skills/frontend-trading-dashboard/SKILL.md`** - 프론트엔드 개발 가이드

### 2. 우선순위

1. 🔴 **CRITICAL**: 즉시 조치 (JWT Secret 등)
2. 🟠 **HIGH**: 1주일 내 (그리드봇 API, Refresh Token 등)
3. 🟡 **MEDIUM**: 1개월 내 (테스트 추가, 감사 로그 등)
4. 🟢 **LOW**: 장기 개선

### 3. 테스트 실행

```bash
cd backend
python -m pytest tests/unit/ tests/integration/ -v --no-cov
# 예상: 72 passed, 2 skipped
```

---

## ✅ 정리 완료 체크리스트

| 항목 | 상태 |
|------|------|
| 중복 보안 문서 아카이브 | ⬜ 수동 실행 필요 |
| 완료된 작업 문서 아카이브 | ⬜ 수동 실행 필요 |
| 레거시 rate_limit.py 삭제 | ⬜ 선택사항 |
| SKILL.md 업데이트 | ✅ 완료 |
| SECURITY_PRIORITY_TASKS.md 통합 | ✅ 완료 |

---

**작성자**: Claude AI  
**최종 수정**: 2025-12-12
