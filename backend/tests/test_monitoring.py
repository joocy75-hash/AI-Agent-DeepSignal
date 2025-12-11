"""
모니터링 시스템 테스트
"""
import pytest
import time

from src.utils.monitoring import SimpleMonitor


class TestSimpleMonitor:
    """모니터링 시스템 테스트"""

    def test_track_request(self):
        """요청 추적 테스트"""
        monitor = SimpleMonitor()

        endpoint = "/api/test"
        monitor.track_request(endpoint)

        assert monitor.requests_count[endpoint] == 1

        # 여러 요청
        for _ in range(9):
            monitor.track_request(endpoint)

        assert monitor.requests_count[endpoint] == 10

    def test_track_response_time(self):
        """응답 시간 추적 테스트"""
        monitor = SimpleMonitor()

        endpoint = "/api/test"
        response_time = 0.123

        monitor.track_response_time(endpoint, response_time)

        assert len(monitor.response_times[endpoint]) == 1
        assert monitor.response_times[endpoint][0] == response_time

    def test_track_response_time_max_100(self):
        """응답 시간 최대 100개 저장 테스트"""
        monitor = SimpleMonitor()

        endpoint = "/api/test"

        # 150개 추가
        for i in range(150):
            monitor.track_response_time(endpoint, i * 0.001)

        # 최대 100개만 유지
        assert len(monitor.response_times[endpoint]) == 100

    def test_track_error(self):
        """에러 추적 테스트"""
        monitor = SimpleMonitor()

        endpoint = "/api/test"
        monitor.track_error(endpoint)

        assert monitor.errors_count[endpoint] == 1

        # 여러 에러
        for _ in range(4):
            monitor.track_error(endpoint)

        assert monitor.errors_count[endpoint] == 5

    def test_track_user(self):
        """사용자 추적 테스트"""
        monitor = SimpleMonitor()

        user_id = 123
        monitor.track_user(user_id)

        assert user_id in monitor.active_users

        # 동일 사용자 중복 추적
        monitor.track_user(user_id)
        assert len(monitor.active_users) == 1

        # 다른 사용자 추적
        monitor.track_user(456)
        assert len(monitor.active_users) == 2

    def test_update_backtest_status(self):
        """백테스트 상태 업데이트 테스트"""
        monitor = SimpleMonitor()

        # queued
        monitor.update_backtest_status("queued")
        assert monitor.backtest_stats["queued"] == 1

        # running
        monitor.update_backtest_status("running")
        assert monitor.backtest_stats["running"] == 1

        # completed
        monitor.update_backtest_status("completed")
        assert monitor.backtest_stats["completed"] == 1

        # failed
        monitor.update_backtest_status("failed")
        assert monitor.backtest_stats["failed"] == 1

        # 총 개수
        total = sum(monitor.backtest_stats.values())
        assert total == 4

    def test_get_stats(self):
        """전체 통계 조회 테스트"""
        monitor = SimpleMonitor()

        # 몇 가지 활동 기록
        monitor.track_request("/api/account")
        monitor.track_request("/api/account")
        monitor.track_request("/backtest/start")

        monitor.track_response_time("/api/account", 0.050)
        monitor.track_response_time("/api/account", 0.080)

        monitor.track_error("/backtest/start")

        monitor.track_user(100)
        monitor.track_user(200)

        monitor.update_backtest_status("queued")
        monitor.update_backtest_status("running")

        # 통계 조회
        stats = monitor.get_stats()

        # 구조 확인
        assert "timestamp" in stats
        assert "system" in stats
        assert "api" in stats
        assert "users" in stats
        assert "backtest" in stats

        # API 통계
        assert stats["api"]["total_requests"] == 3
        assert stats["api"]["requests_by_endpoint"]["/api/account"] == 2
        assert stats["api"]["requests_by_endpoint"]["/backtest/start"] == 1
        assert stats["api"]["total_errors"] == 1

        # 사용자 통계
        assert stats["users"]["active_users"] == 2

        # 백테스트 통계
        assert stats["backtest"]["total"] == 2
        assert stats["backtest"]["queued"] == 1
        assert stats["backtest"]["running"] == 1

    def test_get_stats_system_resources(self):
        """시스템 리소스 통계 테스트"""
        monitor = SimpleMonitor()

        stats = monitor.get_stats()

        # 시스템 통계 확인
        assert "cpu_percent" in stats["system"]
        assert "memory_percent" in stats["system"]
        assert "memory_used_mb" in stats["system"]
        assert "disk_percent" in stats["system"]

        # 값이 합리적인 범위인지 확인
        assert 0 <= stats["system"]["cpu_percent"] <= 100
        assert 0 <= stats["system"]["memory_percent"] <= 100
        assert stats["system"]["memory_used_mb"] > 0

    def test_reset_stats(self):
        """통계 초기화 테스트"""
        monitor = SimpleMonitor()

        # 여러 활동 기록
        monitor.track_request("/api/test")
        monitor.track_error("/api/test")
        monitor.track_user(111)
        monitor.update_backtest_status("completed")

        # 초기화 전 확인
        stats_before = monitor.get_stats()
        assert stats_before["api"]["total_requests"] > 0

        # 초기화
        monitor.reset_stats()

        # 초기화 후 확인
        stats_after = monitor.get_stats()
        assert stats_after["api"]["total_requests"] == 0
        assert stats_after["api"]["total_errors"] == 0
        assert stats_after["users"]["active_users"] == 0
        assert stats_after["backtest"]["total"] == 0

    def test_multiple_endpoints_tracking(self):
        """여러 엔드포인트 동시 추적 테스트"""
        monitor = SimpleMonitor()

        endpoints = [
            "/api/account",
            "/api/order",
            "/backtest/start",
            "/backtest/result",
            "/admin/monitoring/stats"
        ]

        # 각 엔드포인트에 다른 횟수로 요청
        for i, endpoint in enumerate(endpoints):
            for _ in range(i + 1):
                monitor.track_request(endpoint)

        stats = monitor.get_stats()

        # 총 요청 수 확인 (1+2+3+4+5 = 15)
        assert stats["api"]["total_requests"] == 15

        # 각 엔드포인트별 확인
        for i, endpoint in enumerate(endpoints):
            assert stats["api"]["requests_by_endpoint"][endpoint] == i + 1


@pytest.mark.asyncio
class TestMonitoringIntegration:
    """모니터링 통합 테스트"""

    async def test_realistic_monitoring_scenario(self, async_session):
        """실제 모니터링 시나리오 테스트"""
        from src.database.models import User, BacktestResult

        monitor = SimpleMonitor()

        # 사용자 생성
        users = []
        for i in range(5):
            user = User(email=f"user{i}@example.com", password_hash="hashed")
            async_session.add(user)
            users.append(user)

        await async_session.commit()
        for user in users:
            await async_session.refresh(user)

        # 각 사용자 활동 시뮬레이션
        for user in users:
            # 사용자 추적
            monitor.track_user(user.id)

            # API 요청
            monitor.track_request("/api/account")
            monitor.track_response_time("/api/account", 0.05)

            # 백테스트 생성
            result = BacktestResult(
                user_id=user.id,
                initial_balance=10000.0,
                final_balance=12000.0,
                status="queued"
            )
            async_session.add(result)
            monitor.update_backtest_status("queued")

        await async_session.commit()

        # 통계 확인
        stats = monitor.get_stats()

        assert stats["users"]["active_users"] == 5
        assert stats["api"]["total_requests"] == 5
        assert stats["backtest"]["queued"] == 5
        assert stats["backtest"]["total"] == 5

    async def test_error_tracking_scenario(self):
        """에러 추적 시나리오 테스트"""
        monitor = SimpleMonitor()

        # 정상 요청
        for _ in range(50):
            monitor.track_request("/api/test")

        # 에러 발생
        for _ in range(5):
            monitor.track_request("/api/test")
            monitor.track_error("/api/test")

        stats = monitor.get_stats()

        assert stats["api"]["total_requests"] == 55
        assert stats["api"]["total_errors"] == 5

        # 에러율 계산 (약 9%)
        error_rate = stats["api"]["total_errors"] / stats["api"]["total_requests"]
        assert 0.08 < error_rate < 0.10

    async def test_backtest_lifecycle_tracking(self):
        """백테스트 라이프사이클 추적 테스트"""
        monitor = SimpleMonitor()

        # 10개 백테스트 생성
        for _ in range(10):
            monitor.update_backtest_status("queued")

        stats = monitor.get_stats()
        assert stats["backtest"]["queued"] == 10

        # 5개 실행 중으로 변경
        for _ in range(5):
            monitor.update_backtest_status("running")

        stats = monitor.get_stats()
        assert stats["backtest"]["running"] == 5

        # 3개 완료
        for _ in range(3):
            monitor.update_backtest_status("completed")

        # 1개 실패
        monitor.update_backtest_status("failed")

        stats = monitor.get_stats()
        assert stats["backtest"]["completed"] == 3
        assert stats["backtest"]["failed"] == 1
        assert stats["backtest"]["total"] == 19  # 10 + 5 + 3 + 1

    async def test_concurrent_users_monitoring(self):
        """동시 사용자 모니터링 테스트"""
        monitor = SimpleMonitor()

        # 20명의 사용자 활동
        for user_id in range(1, 21):
            monitor.track_user(user_id)

            # 각 사용자가 여러 요청
            for _ in range(3):
                monitor.track_request("/api/account")

        stats = monitor.get_stats()

        assert stats["users"]["active_users"] == 20
        assert stats["api"]["total_requests"] == 60  # 20명 × 3회

    async def test_response_time_statistics(self):
        """응답 시간 통계 테스트"""
        monitor = SimpleMonitor()

        endpoint = "/api/test"

        # 다양한 응답 시간 기록
        response_times = [0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.50, 1.00]

        for rt in response_times:
            monitor.track_response_time(endpoint, rt)

        # 응답 시간 기록 확인
        assert len(monitor.response_times[endpoint]) == len(response_times)

        # 평균 응답 시간 계산 (테스트용)
        avg_response_time = sum(monitor.response_times[endpoint]) / len(monitor.response_times[endpoint])
        assert avg_response_time > 0
