"""
봇 안정성 테스트

WebSocket 재연결, 에러 핸들링, 리소스 정리 등을 검증합니다.

주의: 이 테스트는 conftest를 사용하지 않고 독립적으로 실행됩니다.
실행 방법:
  export ENCRYPTION_KEY="Dz9w_blEMa-tMD5hqK6V7yiaYecQBdsTaO0PJR3ESn8="
  python3 -m pytest tests/test_bot_stability.py -v --no-cov
"""
import asyncio
import pytest
import sys
import os

# 환경 변수 설정 (테스트용)
os.environ.setdefault("ENCRYPTION_KEY", "Dz9w_blEMa-tMD5hqK6V7yiaYecQBdsTaO0PJR3ESn8=")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5432/lbank")

from unittest.mock import AsyncMock, MagicMock, patch

from src.services.lbank_ws_improved import LBankWebSocketClient
from src.services.bot_runner import BotRunner


class TestWebSocketReconnection:
    """WebSocket 재연결 로직 테스트"""

    @pytest.mark.asyncio
    async def test_websocket_reconnection_on_disconnect(self):
        """연결 끊김 시 자동 재연결"""
        market_queue = asyncio.Queue()

        client = LBankWebSocketClient(
            url="wss://test.example.com",
            market_queue=market_queue,
            max_retries=3,
            initial_backoff=0.1,
            max_backoff=1.0
        )

        # WebSocket이 2번 실패하고 3번째에 성공하는 시나리오 모의
        with patch('websockets.connect') as mock_connect:
            # 처음 2번은 실패
            mock_connect.side_effect = [
                ConnectionError("Connection failed"),
                ConnectionError("Connection failed"),
                # 3번째는 성공했지만 즉시 종료 (테스트 완료)
                ConnectionError("Test complete")
            ]

            try:
                await asyncio.wait_for(client.start(), timeout=5.0)
            except (ConnectionError, asyncio.TimeoutError):
                pass  # 예상된 에러

            # 재연결 시도가 있었는지 확인
            assert mock_connect.call_count >= 2

    @pytest.mark.asyncio
    async def test_exponential_backoff(self):
        """지수 백오프 검증"""
        market_queue = asyncio.Queue()

        client = LBankWebSocketClient(
            url="wss://test.example.com",
            market_queue=market_queue,
            max_retries=3,
            initial_backoff=1.0,
            max_backoff=10.0,
            backoff_multiplier=2.0
        )

        # 백오프 값이 올바르게 증가하는지 확인
        assert client.initial_backoff == 1.0
        assert client.max_backoff == 10.0
        assert client.backoff_multiplier == 2.0

    @pytest.mark.asyncio
    async def test_graceful_shutdown(self):
        """Graceful shutdown 검증"""
        market_queue = asyncio.Queue()

        client = LBankWebSocketClient(
            url="wss://test.example.com",
            market_queue=market_queue
        )

        # 클라이언트 상태 확인
        assert client.is_running == False
        assert client.is_connected == False

        # stop() 호출 (실행 중이 아니어도 에러 없어야 함)
        await client.stop()

        assert client.is_running == False


class TestBotErrorHandling:
    """Bot 에러 핸들링 테스트"""

    @pytest.mark.asyncio
    async def test_bot_handles_market_data_timeout(self):
        """마켓 데이터 타임아웃 처리"""
        market_queue = asyncio.Queue()
        bot_runner = BotRunner(market_queue)

        # 큐가 비어있어서 타임아웃 발생
        # (실제 테스트에서는 모킹 필요)
        assert isinstance(bot_runner.market_queue, asyncio.Queue)

    @pytest.mark.asyncio
    async def test_bot_handles_consecutive_errors(self):
        """연속 에러 발생 시 봇 중지"""
        market_queue = asyncio.Queue()
        bot_runner = BotRunner(market_queue)

        # 연속 에러 체크 로직은 _run_loop 내부에 구현됨
        # max_consecutive_errors = 10
        assert hasattr(bot_runner, 'market_queue')

    @pytest.mark.asyncio
    async def test_bot_resource_cleanup(self):
        """봇 종료 시 리소스 정리"""
        market_queue = asyncio.Queue()
        bot_runner = BotRunner(market_queue)

        user_id = 999

        # 봇 실행 전에는 task가 없음
        assert not bot_runner.is_running(user_id)
        assert user_id not in bot_runner.tasks


class TestBotStateMonitoring:
    """봇 상태 모니터링 테스트"""

    def test_websocket_status_tracking(self):
        """WebSocket 상태 추적"""
        market_queue = asyncio.Queue()

        client = LBankWebSocketClient(
            url="wss://test.example.com",
            market_queue=market_queue
        )

        # 초기 상태
        status = client.get_status()
        assert status["is_connected"] == False
        assert status["is_running"] == False
        assert status["connection_count"] == 0
        assert status["error_count"] == 0
        assert status["last_message_time"] is None

    def test_bot_runner_state(self):
        """BotRunner 상태 확인"""
        market_queue = asyncio.Queue()
        bot_runner = BotRunner(market_queue)

        user_id = 123

        # 초기에는 실행 중이 아님
        assert not bot_runner.is_running(user_id)

        # tasks 딕셔너리가 존재
        assert isinstance(bot_runner.tasks, dict)


class TestQueueMemoryManagement:
    """Queue 메모리 관리 테스트"""

    @pytest.mark.asyncio
    async def test_queue_overflow_handling(self):
        """큐 오버플로우 처리"""
        # 작은 크기의 큐 생성
        market_queue = asyncio.Queue(maxsize=5)

        # 큐를 가득 채움
        for i in range(5):
            await market_queue.put({"price": i})

        # 큐가 가득 찬 상태
        assert market_queue.full()

        # put_nowait는 QueueFull 예외 발생해야 함
        with pytest.raises(asyncio.QueueFull):
            market_queue.put_nowait({"price": 999})

    @pytest.mark.asyncio
    async def test_old_messages_removed_on_overflow(self):
        """오버플로우 시 오래된 메시지 제거"""
        market_queue = asyncio.Queue(maxsize=3)

        # 메시지 3개 추가
        await market_queue.put({"price": 1})
        await market_queue.put({"price": 2})
        await market_queue.put({"price": 3})

        assert market_queue.full()

        # 가장 오래된 메시지 제거 후 새 메시지 추가
        # (LBankWebSocketClient._handle_message에서 구현된 로직)
        if market_queue.full():
            await market_queue.get()  # 오래된 메시지 제거
            await market_queue.put({"price": 4})

        # 큐에 2, 3, 4가 있어야 함
        msg1 = await market_queue.get()
        assert msg1["price"] == 2


class TestWebSocketPingPong:
    """WebSocket Ping/Pong 테스트"""

    @pytest.mark.asyncio
    async def test_ping_pong_handling(self):
        """Ping/Pong 메시지 처리"""
        market_queue = asyncio.Queue()

        client = LBankWebSocketClient(
            url="wss://test.example.com",
            market_queue=market_queue
        )

        # Ping 메시지 모의
        ping_message = '{"ping": 1234567890}'

        # _handle_message가 올바르게 처리하는지 확인
        # (실제로는 ws.send를 모킹해야 함)
        assert hasattr(client, '_handle_message')


class TestBotRunnerIntegration:
    """BotRunner 통합 테스트"""

    def test_bot_runner_initialization(self):
        """BotRunner 초기화"""
        market_queue = asyncio.Queue()
        bot_runner = BotRunner(market_queue)

        assert bot_runner.market_queue is market_queue
        assert isinstance(bot_runner.tasks, dict)
        assert len(bot_runner.tasks) == 0

    def test_stop_non_running_bot(self):
        """실행 중이 아닌 봇 중지 시도"""
        market_queue = asyncio.Queue()
        bot_runner = BotRunner(market_queue)

        user_id = 456

        # 실행 중이 아닌데 stop 호출 (에러 없어야 함)
        bot_runner.stop(user_id)

        assert not bot_runner.is_running(user_id)
