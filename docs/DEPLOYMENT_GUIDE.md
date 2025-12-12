# 🚀 배포 가이드

> Auto Dashboard 프로젝트 배포 절차 (2025-12-12 업데이트)

## 📋 빠른 배포 (체크리스트)

```bash
# 1. 로컬에서 변경사항 커밋
git add -A
git commit -m "배포: [변경내용 요약]"
git push origin main

# 2. 서버 SSH 접속
ssh root@158.247.245.197

# 3. 프로젝트 디렉토리 이동
cd /root/auto-dashboard

# 4. 최신 코드 가져오기
git pull origin main

# 5. Docker 컨테이너 재빌드 및 재시작
docker-compose down
docker-compose up -d --build

# 6. 로그 확인
docker-compose logs -f --tail=50
```

---

## 🔧 상세 배포 절차

### 1단계: 로컬 변경사항 커밋

```bash
# 현재 상태 확인
git status

# 모든 변경사항 스테이징
git add -A

# 커밋 (의미 있는 메시지 작성)
git commit -m "feat: [기능명] - 상세 설명"

# 원격 저장소에 푸시
git push origin main
```

### 2단계: 서버 접속

```bash
# SSH 접속
ssh root@158.247.245.197
# 비밀번호: Vc8,xn7j_fjdnNGy
```

### 3단계: 코드 업데이트

```bash
# 프로젝트 디렉토리 이동
cd /root/auto-dashboard

# 최신 코드 가져오기
git pull origin main
```

### 4단계: Docker 컨테이너 재빌드

```bash
# 방법 1: 안전한 재시작 (권장)
docker-compose down
docker-compose up -d --build

# 방법 2: 특정 서비스만 재시작
docker-compose up -d --build backend   # 백엔드만
docker-compose up -d --build frontend  # 프론트엔드만
docker-compose up -d --build nginx     # Nginx만
```

### 5단계: 배포 확인

```bash
# 컨테이너 상태 확인
docker-compose ps

# 로그 확인 (최근 50줄)
docker-compose logs -f --tail=50

# 백엔드 로그만
docker-compose logs -f backend --tail=50

# 헬스 체크
curl -s http://localhost:8000/health | jq
```

---

## 🔑 환경 변수 설정

서버의 `/root/auto-dashboard/.env` 파일:

```bash
# 필수 (프로덕션)
JWT_SECRET=your-super-secret-jwt-key-change-me
ENCRYPTION_KEY=your-fernet-encryption-key
POSTGRES_PASSWORD=your-db-password
REDIS_PASSWORD=your-redis-password

# 선택
CORS_ORIGINS=https://your-domain.com
ENVIRONMENT=production
DEEPSEEK_API_KEY=your-deepseek-key
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_CHAT_ID=your-chat-id
```

---

## 🐳 Docker 서비스 구조

| 서비스 | 포트 | 설명 |
|--------|------|------|
| `nginx` | 80, 443 | 리버스 프록시 |
| `frontend` | 3000 | React 앱 |
| `backend` | 8000 | FastAPI 서버 |
| `postgres` | 5432 | PostgreSQL DB |
| `redis` | 6379 | 캐시/세션 |

---

## 🚨 문제 해결

### 컨테이너가 시작되지 않을 때

```bash
# 상세 로그 확인
docker-compose logs backend

# 컨테이너 직접 실행 (디버그)
docker-compose run --rm backend bash
```

### 데이터베이스 마이그레이션

```bash
# 컨테이너 내부에서 마이그레이션 실행
docker-compose exec backend alembic upgrade head
```

### 포트 충돌

```bash
# 사용 중인 포트 확인
sudo lsof -i :8000
sudo lsof -i :3000

# 해당 프로세스 종료
sudo kill -9 [PID]
```

### 디스크 공간 부족

```bash
# Docker 정리
docker system prune -a
docker volume prune
```

---

## 📂 서버 디렉토리 구조

```
/root/auto-dashboard/
├── backend/           # FastAPI 백엔드
├── frontend/          # React 프론트엔드
├── nginx/             # Nginx 설정
├── docker-compose.yml # Docker 구성
├── .env               # 환경 변수 (서버에만 존재)
└── docs/              # 문서
```

---

## ✅ 배포 후 체크리스트

| 항목 | 확인 방법 |
|------|----------|
| 프론트엔드 접속 | 브라우저에서 `http://158.247.245.197` |
| 백엔드 API | `curl http://158.247.245.197/api/health` |
| 로그인 테스트 | 대시보드에서 로그인 |
| 봇 상태 확인 | Trading 페이지에서 봇 상태 조회 |

---

## 📝 커밋 메시지 규칙

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 수정
style: 코드 포맷팅
refactor: 코드 리팩토링
test: 테스트 추가
chore: 빌드, 설정 변경
security: 보안 관련 변경
```

예시:

```bash
git commit -m "feat: Refresh Token 구현"
git commit -m "fix: 봇 상태 동기화 오류 수정"
git commit -m "security: 로그인 Brute-force 방지 추가"
```
