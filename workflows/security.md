---
description: 보안 점검 수행 - 코드 취약점 검사 및 CRITICAL 이슈 확인
---

# 🔒 보안 점검 워크플로우

## 📋 수행 단계

### 1. 보안 감사 문서 확인

// turbo

- `docs/CODE_REVIEW_AND_SECURITY_AUDIT.md` 읽기

### 2. CRITICAL 이슈 상태 확인

| 이슈 | 파일 | 상태 체크 |
|------|------|----------|
| JWT Secret 기본값 | `backend/src/config.py` | `jwt_secret` 환경변수 확인 |
| 주문 금액 검증 | `backend/src/api/order.py` | 잔고 초과 검증 로직 존재 여부 |
| 포지션 청산 소유권 | `backend/src/api/order.py` | `user_id` 검증 로직 존재 여부 |
| API 키 마스킹 | `backend/src/api/account.py` | 마스킹 처리 여부 |

### 3. 민감 정보 노출 검사

```bash
# 하드코딩된 비밀번호/키 검색
grep -rn "password\|secret\|api_key" --include="*.py" backend/src/ | grep -v "\.pyc" | grep -v "__pycache__"
```

### 4. 환경변수 확인

```bash
# .env 파일에 민감 정보 설정 여부 확인
cat backend/.env 2>/dev/null || echo ".env 파일 없음"
```

### 5. Rate Limiting 확인

- `backend/src/middleware/rate_limit_improved.py` 설정 검토
- IP별, 사용자별 제한 적용 여부

## ✅ 점검 완료 조건

- [ ] 모든 CRITICAL 이슈 해결됨
- [ ] 민감 정보 하드코딩 없음
- [ ] 환경변수로 비밀 관리됨
- [ ] Rate Limiting 적용됨
