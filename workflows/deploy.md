---
description: 배포 절차 - 로컬에서 서버로 코드 배포
---

# 🚀 배포 워크플로우

## 📋 사전 확인

### 1. 보안 점검 완료 확인

- `docs/CODE_REVIEW_AND_SECURITY_AUDIT.md`의 CRITICAL 이슈 해결 여부

### 2. 테스트 확인

```bash
# 백엔드 테스트
cd backend && pytest -v

# 프론트엔드 빌드 테스트
cd frontend && npm run build
```

## 📦 배포 단계

### Step 1: Git 커밋 & 푸시

```bash
# 변경사항 확인
git status

# 스테이징
git add .

# 커밋
git commit -m "feat: [작업 내용 요약]"

# 푸시
git push origin main
```

### Step 2: 서버 접속

```bash
# SSH 접속 (IP와 키 파일은 환경에 맞게 수정)
ssh -i ~/.ssh/your-key.pem user@your-server-ip
```

### Step 3: 서버에서 코드 업데이트

```bash
# 프로젝트 디렉토리 이동
cd /path/to/auto-dashboard

# 최신 코드 Pull
git pull origin main

# Docker 컨테이너 재빌드 & 재시작
docker-compose down
docker-compose up -d --build
```

### Step 4: 배포 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f backend
```

## ⚠️ 롤백 절차

```bash
# 이전 커밋으로 되돌리기
git revert HEAD

# 또는 특정 커밋으로
git checkout <commit-hash>

# Docker 재시작
docker-compose down
docker-compose up -d --build
```

## 📝 배포 체크리스트

- [ ] 로컬 테스트 통과
- [ ] 보안 이슈 해결
- [ ] Git 커밋 완료
- [ ] 서버 배포 완료
- [ ] 서비스 정상 동작 확인
