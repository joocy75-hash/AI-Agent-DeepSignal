# 🔧 Balance API 디버깅 리포트

> **작성일**: 2025-12-09 21:12 KST  
> **작성자**: AI Assistant (Claude)  
> **상태**: 🟡 코드 수정 완료, 배포 필요

---

## 📋 목차

1. [문제 개요](#문제-개요)
2. [디버깅 과정](#디버깅-과정)
3. [발견된 문제점](#발견된-문제점)
4. [적용된 수정사항](#적용된-수정사항)
5. [다음 작업자가 해야 할 일](#다음-작업자가-해야-할-일)
6. [참고 파일 목록](#참고-파일-목록)

---

## 문제 개요

### 🎯 원래 목표

배포된 프론트엔드(`http://158.247.245.197:3000`)에서 **Balance(잔고) 조회 기능이 작동하지 않는 문제**를 해결하는 것.

### 🔴 관찰된 증상

| 위치 | API 엔드포인트 | HTTP 상태 | 에러 메시지 |
|------|---------------|-----------|-------------|
| Trading 페이지 | `/bitget/account` | 404 Not Found | API 키가 설정되지 않음 |
| Trading 페이지 | `/account/balance` | 400 Bad Request | API keys not configured |
| Settings 페이지 | 연결 테스트 버튼 | 에러 발생 | "계정 정보를 가져올 수 없습니다" |

### 🤔 이상한 점

- Settings 페이지에서는 **"API 키가 등록되어 있습니다"**라고 표시됨
- 하지만 `/bitget/account` API 호출 시 **404 Not Found** 반환
- 즉, 프론트엔드 표시 상태와 백엔드 실제 상태가 불일치

---

## 디버깅 과정

### 1단계: 서버 상태 확인 ✅

```
백엔드: http://158.247.245.197:8000 - 정상 작동
프론트엔드: http://158.247.245.197:3000 - 정상 작동
Swagger UI: http://158.247.245.197:8000/docs - 접속 가능
```

### 2단계: 브라우저 Network 탭 분석 ✅

Trading 페이지 로드 시 네트워크 요청 확인:

```
✅ GET /chart/candles/BTCUSDT - 200 OK
✅ WebSocket ws://158.247.245.197:8000/ws/user/1 - 101 연결 성공
❌ GET /bitget/account - 404 Not Found
❌ GET /account/balance - 400 Bad Request
```

### 3단계: 백엔드 API 코드 분석 ✅

**`/bitget/account` 엔드포인트** (`backend/src/api/bitget_market.py`, line 195-215):

```python
@router.get("/account")
async def get_account(...):
    client = await get_user_bitget_client(user_id, session)  # 여기서 404 발생
    account = await client.get_account_info()
    return account  # 문제: Bitget API는 리스트를 반환
```

**`get_user_bitget_client` 함수** (line 39-93):

- DB에서 `ApiKey` 테이블 조회
- API 키가 없으면 **HTTPException(404)** 발생
- API 키 복호화 실패 시 **HTTPException(500)** 발생

### 4단계: 데이터 구조 불일치 발견 🔍

**Bitget API 응답 구조**:

```json
{
  "code": "00000",
  "msg": "success",
  "data": [
    {
      "marginCoin": "USDT",
      "available": "1000.00",
      "frozen": "50.00",
      "unrealizedPL": "25.50"
    }
  ]
}
```

**백엔드 `_request` 메서드**:

- `result.get("data", {})` 반환 → **리스트 `[{...}]`** 반환

**프론트엔드 기대 구조** (`BalanceCard.jsx`, line 41-51):

```javascript
const data = await bitgetAPI.getAccount();
const formattedBalance = {
  futures: {
    total: parseFloat(data.available || 0) + parseFloat(data.frozen || 0),
    // data가 리스트이면 data.available은 undefined!
  }
};
```

**문제**: 백엔드가 `[{...}]` (리스트)를 반환하는데, 프론트엔드는 `{...}` (객체)를 기대함!

---

## 발견된 문제점

### 🔴 문제 1: API 응답 데이터 구조 불일치 (수정 완료)

| 구분 | 백엔드 반환값 | 프론트엔드 기대값 |
|------|-------------|-----------------|
| 타입 | `[{marginCoin: "USDT", available: "1000", ...}]` | `{available: "1000", ...}` |
| 접근 | `data[0].available` | `data.available` |

**원인**: Bitget API가 여러 마진 코인(USDT, BTC 등) 계좌를 리스트로 반환하는데, 그대로 전달.

### 🟡 문제 2: API 키 상태 불일치 (추가 조사 필요)

Settings 페이지에서 "API 키가 등록되어 있습니다" 표시 vs `/bitget/account`에서 404 반환

**가능한 원인들**:

1. **암호화 키 변경**: 서버 재배포 시 `SECRET_KEY` 환경변수가 변경되어 기존 암호화된 API 키 복호화 불가
2. **DB 동기화 문제**: 다른 DB 인스턴스 참조
3. **프론트엔드 캐시**: 브라우저가 오래된 상태를 캐시

### 🟢 확인된 정상 기능

- JWT 인증: 정상 작동
- WebSocket 연결: 정상 (101 Switching Protocols)
- Chart 데이터: `/chart/candles/BTCUSDT` 정상 응답

---

## 적용된 수정사항

### ✅ 수정 1: `/bitget/account` API 응답 구조 개선

**파일**: `backend/src/api/bitget_market.py` (line 195-246)

**수정 내용**:

- Bitget API 응답 리스트에서 USDT 계좌 추출
- 플랫 객체로 변환하여 반환

```python
# 수정 전
account = await client.get_account_info()
return account  # 리스트 반환 [{...}]

# 수정 후
account_data = await client.get_account_info()
if isinstance(account_data, list):
    usdt_account = None
    for account in account_data:
        if account.get("marginCoin", "").upper() == "USDT":
            usdt_account = account
            break
    
    if usdt_account:
        return {
            "marginCoin": usdt_account.get("marginCoin", "USDT"),
            "available": usdt_account.get("available", "0"),
            "frozen": usdt_account.get("frozen", "0"),
            "unrealizedPL": usdt_account.get("unrealizedPL", "0"),
            # ... 기타 필드
        }
```

**커밋**: `550dfec` - "fix: parse Bitget account API response correctly for frontend"

---

## 다음 작업자가 해야 할 일

### 📌 필수 작업 (순서대로)

#### 작업 1: 서버에 변경사항 배포 🚀

```bash
# 1. 로컬에서 Git Push
cd /Users/mr.joo/Desktop/auto-dashboard
git push origin main

# 2. 서버에 SSH 접속
ssh root@158.247.245.197
# 비밀번호 입력

# 3. 프로젝트 디렉토리로 이동
cd /root/auto-dashboard  # 또는 실제 배포 경로

# 4. 최신 코드 Pull
git pull origin main

# 5. 백엔드 Docker 컨테이너 재빌드 및 재시작
docker-compose build backend
docker-compose up -d backend

# 6. 로그 확인
docker logs backend --tail 50 -f
```

#### 작업 2: API 키 문제 해결 확인 🔑

배포 후에도 Balance가 표시되지 않으면:

1. **Settings 페이지에서 API 키 재등록**:
   - 기존 표시되는 키 정보는 캐시일 수 있음
   - Bitget 거래소에서 새 API 키 발급 후 재등록
   - API Key, Secret Key, Passphrase 모두 입력

2. **Bitget API 키 권한 확인**:
   - 거래소 API 설정에서 "선물 거래" 권한 활성화 필요
   - IP 화이트리스트에 서버 IP(`158.247.245.197`) 추가

#### 작업 3: 연결 테스트로 확인 ✅

Settings 페이지 → "연결 테스트" 버튼 클릭:

- ✅ 성공: "연결 성공! 잔고: XX.XX USDT"
- ❌ 실패 시 콘솔 로그 확인

### 📌 선택 작업 (필요 시)

#### 작업 4: 암호화 키 일관성 확인

서버의 `docker-compose.yml` 또는 `.env` 파일에서:

```yaml
backend:
  environment:
    - SECRET_KEY=your-secret-key-here
```

이 값이 API 키 암호화 시 사용된 값과 동일한지 확인. 변경되었다면 기존 암호화된 API 키는 복호화 불가.

#### 작업 5: DB에서 직접 API 키 확인

```bash
# 서버에서 실행
docker exec -it postgres psql -U postgres -d auto_trading

-- API 키 테이블 확인
SELECT id, user_id, 
       SUBSTRING(encrypted_api_key, 1, 20) as api_key_preview,
       created_at 
FROM api_keys;
```

---

## 참고 파일 목록

### 백엔드 (Python/FastAPI)

| 파일 경로 | 설명 | 주요 함수 |
|-----------|------|-----------|
| `backend/src/api/bitget_market.py` | Bitget API 엔드포인트 | `get_account()`, `get_user_bitget_client()` |
| `backend/src/api/account.py` | 계정 관련 API | `balance()`, `get_my_keys()` |
| `backend/src/services/bitget_rest.py` | Bitget REST 클라이언트 | `BitgetRestClient.get_account_info()` |
| `backend/src/services/exchange_service.py` | 거래소 서비스 | `ExchangeService.get_user_exchange_client()` |
| `backend/src/utils/crypto_secrets.py` | API 키 암호화/복호화 | `encrypt_secret()`, `decrypt_secret()` |

### 프론트엔드 (React/Vite)

| 파일 경로 | 설명 | 주요 함수 |
|-----------|------|-----------|
| `frontend/src/components/BalanceCard.jsx` | 잔고 카드 컴포넌트 | `loadBalance()` |
| `frontend/src/pages/Settings.jsx` | 설정 페이지 | `handleTestConnection()`, `checkSavedKeys()` |
| `frontend/src/api/bitget.js` | Bitget API 클라이언트 | `bitgetAPI.getAccount()` |
| `frontend/src/api/account.js` | 계정 API 클라이언트 | `accountAPI.getBalance()` |

### 배포 관련

| 파일 경로 | 설명 |
|-----------|------|
| `docker-compose.yml` | Docker 서비스 정의 |
| `DEPLOYMENT_BEGINNER_GUIDE.md` | 배포 가이드 |
| `backend/Dockerfile` | 백엔드 Docker 이미지 |

---

## 디버깅 증거 (스크린샷 위치)

브라우저 subagent가 캡처한 스크린샷들:

```
~/.gemini/antigravity/brain/38a0cbbb-950e-4423-a016-5de69f22aaac/
├── network_tab_after_reload_1765281757292.png  # 네트워크 에러 확인
├── console_tab_after_reload_1765281757785.png  # 콘솔 로그
├── settings_page_1765281916768.png              # Settings 페이지 상태
├── connection_test_result_2_1765282074652.png   # 연결 테스트 실패
└── swagger_docs_page_1765281618670.png          # Swagger UI
```

---

## 요약

| 항목 | 상태 | 비고 |
|------|------|------|
| 문제 분석 | ✅ 완료 | API 응답 구조 불일치 확인 |
| 코드 수정 | ✅ 완료 | `bitget_market.py` 수정 |
| Git 커밋 | ✅ 완료 | `550dfec` |
| 서버 배포 | ⏳ 대기 | 다음 작업자 수행 필요 |
| API 키 재등록 | ⏳ 대기 | 배포 후 테스트 필요 |
| 최종 검증 | ⏳ 대기 | Trading 페이지 잔고 표시 확인 |

---

> **💡 참고**: 이 문서는 디버깅 세션 중 발견한 내용을 기록한 것입니다.
> 서버 배포 후에도 문제가 지속되면 API 키 암호화 관련 추가 조사가 필요할 수 있습니다.
