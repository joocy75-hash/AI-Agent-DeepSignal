"""
Rate Limiting 미들웨어 테스트
"""
import pytest
import time
from unittest.mock import Mock, AsyncMock

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
def rate_limiter():
    """Rate Limiter 픽스처"""
    # 테스트용 앱 Mock
    app = Mock()
    middleware = RateLimitMiddleware(app)
    return middleware


class TestRateLimitMiddleware:
    """Rate Limiting 미들웨어 테스트"""

    @pytest.mark.asyncio
    async def test_general_endpoint_rate_limit(self, rate_limiter):
        """일반 엔드포인트 Rate Limiting 테스트"""
        # Mock request
        request = Mock(spec=Request)
        request.client.host = "127.0.0.1"
        request.url.path = "/api/account"

        # Mock call_next
        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # 제한(60회)까지 요청 성공
        for _ in range(60):
            response = await rate_limiter.dispatch(request, mock_call_next)
            assert response.status_code == 200

        # 61번째 요청 차단
        response = await rate_limiter.dispatch(request, mock_call_next)
        assert response.status_code == 429
        assert "rate limit exceeded" in response.body.decode().lower()

    @pytest.mark.asyncio
    async def test_backtest_endpoint_ip_rate_limit(self, rate_limiter):
        """백테스트 엔드포인트 IP 기반 Rate Limiting 테스트"""
        request = Mock(spec=Request)
        request.client.host = "192.168.1.100"
        request.url.path = "/backtest/start"

        async def mock_call_next(req):
            return JSONResponse({"status": "queued"})

        # 제한(5회)까지 요청 성공
        for _ in range(5):
            response = await rate_limiter.dispatch(request, mock_call_next)
            assert response.status_code == 200

        # 6번째 요청 차단
        response = await rate_limiter.dispatch(request, mock_call_next)
        assert response.status_code == 429

    @pytest.mark.asyncio
    async def test_ip_isolation(self, rate_limiter):
        """IP별 격리 테스트"""
        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # IP 1에서 60회 요청
        request1 = Mock(spec=Request)
        request1.client.host = "192.168.1.1"
        request1.url.path = "/api/test"

        for _ in range(60):
            response = await rate_limiter.dispatch(request1, mock_call_next)
            assert response.status_code == 200

        # IP 1 차단됨
        response = await rate_limiter.dispatch(request1, mock_call_next)
        assert response.status_code == 429

        # IP 2는 여전히 요청 가능 (격리됨)
        request2 = Mock(spec=Request)
        request2.client.host = "192.168.1.2"
        request2.url.path = "/api/test"

        response = await rate_limiter.dispatch(request2, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_window_expiry(self, rate_limiter):
        """시간 윈도우 만료 테스트"""
        request = Mock(spec=Request)
        request.client.host = "10.0.0.1"
        request.url.path = "/api/test"

        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # 60회 요청
        for _ in range(60):
            response = await rate_limiter.dispatch(request, mock_call_next)
            assert response.status_code == 200

        # 61번째 차단
        response = await rate_limiter.dispatch(request, mock_call_next)
        assert response.status_code == 429

        # 61초 대기 (윈도우 만료)
        # 실제 테스트에서는 시간을 Mock하는 것이 좋지만, 여기서는 간단히 설명
        # time.sleep(61)을 사용할 수 있지만 테스트가 느려지므로
        # rate_limiter.requests를 직접 조작

        # 요청 기록 초기화 (윈도우 만료 시뮬레이션)
        key = f"{request.client.host}:/api/test"
        rate_limiter.requests[key].clear()

        # 다시 요청 가능
        response = await rate_limiter.dispatch(request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_different_endpoints_separate_limits(self, rate_limiter):
        """엔드포인트별 독립적인 제한 테스트"""
        request = Mock(spec=Request)
        request.client.host = "172.16.0.1"

        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # 일반 엔드포인트에서 60회
        request.url.path = "/api/account"
        for _ in range(60):
            response = await rate_limiter.dispatch(request, mock_call_next)
            assert response.status_code == 200

        # 백테스트 엔드포인트는 여전히 사용 가능
        request.url.path = "/backtest/start"
        response = await rate_limiter.dispatch(request, mock_call_next)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_cleanup_old_requests(self, rate_limiter):
        """오래된 요청 기록 정리 테스트"""
        request = Mock(spec=Request)
        request.client.host = "192.168.100.1"
        request.url.path = "/api/test"

        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # 몇 개 요청
        for _ in range(10):
            await rate_limiter.dispatch(request, mock_call_next)

        key = f"{request.client.host}:/api/test"
        initial_count = len(rate_limiter.requests[key])

        # 모든 요청을 60초 이전으로 설정
        old_time = time.time() - 61
        rate_limiter.requests[key] = [old_time] * initial_count

        # 새 요청 (cleanup 발생)
        await rate_limiter.dispatch(request, mock_call_next)

        # 오래된 요청 제거됨
        assert len(rate_limiter.requests[key]) == 1  # 방금 요청만


@pytest.mark.asyncio
class TestRateLimitIntegration:
    """Rate Limiting 통합 테스트"""

    async def test_realistic_usage_pattern(self, rate_limiter):
        """실제 사용 패턴 시뮬레이션"""
        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # 여러 사용자 시뮬레이션
        users = [
            {"ip": "192.168.1.10", "requests": 30},
            {"ip": "192.168.1.11", "requests": 40},
            {"ip": "192.168.1.12", "requests": 50},
        ]

        for user in users:
            request = Mock(spec=Request)
            request.client.host = user["ip"]
            request.url.path = "/api/account"

            # 각 사용자가 지정된 횟수만큼 요청
            for _ in range(user["requests"]):
                response = await rate_limiter.dispatch(request, mock_call_next)
                assert response.status_code == 200

        # 모든 사용자 여전히 제한 이내
        for user in users:
            request = Mock(spec=Request)
            request.client.host = user["ip"]
            request.url.path = "/api/account"

            response = await rate_limiter.dispatch(request, mock_call_next)
            assert response.status_code == 200

    async def test_backtest_heavy_usage(self, rate_limiter):
        """백테스트 집중 사용 시나리오"""
        async def mock_call_next(req):
            return JSONResponse({"status": "queued"})

        # 10명의 사용자가 각각 백테스트 시작
        for user_id in range(10):
            request = Mock(spec=Request)
            request.client.host = f"192.168.1.{user_id}"
            request.url.path = "/backtest/start"

            # 각 사용자 5회까지 가능
            for _ in range(5):
                response = await rate_limiter.dispatch(request, mock_call_next)
                assert response.status_code == 200

            # 6번째 차단
            response = await rate_limiter.dispatch(request, mock_call_next)
            assert response.status_code == 429

    async def test_mixed_traffic(self, rate_limiter):
        """일반 트래픽과 백테스트 트래픽 혼합 테스트"""
        request = Mock(spec=Request)
        request.client.host = "10.0.0.100"

        async def mock_call_next(req):
            return JSONResponse({"status": "ok"})

        # 일반 API 40회
        request.url.path = "/api/account"
        for _ in range(40):
            response = await rate_limiter.dispatch(request, mock_call_next)
            assert response.status_code == 200

        # 백테스트 3회
        request.url.path = "/backtest/start"
        for _ in range(3):
            response = await rate_limiter.dispatch(request, mock_call_next)
            assert response.status_code == 200

        # 일반 API 추가 20회 (총 60회)
        request.url.path = "/api/account"
        for _ in range(20):
            response = await rate_limiter.dispatch(request, mock_call_next)
            assert response.status_code == 200

        # 일반 API 61번째 차단
        response = await rate_limiter.dispatch(request, mock_call_next)
        assert response.status_code == 429

        # 백테스트는 아직 2회 가능
        request.url.path = "/backtest/start"
        for _ in range(2):
            response = await rate_limiter.dispatch(request, mock_call_next)
            assert response.status_code == 200
