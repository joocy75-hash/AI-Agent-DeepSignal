"""
리소스 관리 테스트
"""
import pytest

from src.utils.resource_manager import UserResourceManager


class TestUserResourceManager:
    """사용자별 리소스 관리 테스트"""

    def test_can_start_backtest_success(self):
        """백테스트 시작 가능 - 성공 케이스"""
        manager = UserResourceManager()
        user_id = 1

        can_start, error = manager.can_start_backtest(user_id)
        assert can_start is True
        assert error is None

    def test_can_start_backtest_per_user_limit(self):
        """사용자당 동시 백테스트 제한 테스트"""
        manager = UserResourceManager()
        user_id = 1

        # 제한까지 백테스트 시작
        for i in range(manager.limits["max_concurrent_backtests_per_user"]):
            can_start, error = manager.can_start_backtest(user_id)
            assert can_start is True
            manager.start_backtest(user_id, backtest_id=i)

        # 제한 초과 시도
        can_start, error = manager.can_start_backtest(user_id)
        assert can_start is False
        assert "Max concurrent backtests per user" in error

    def test_can_start_backtest_global_limit(self):
        """전체 동시 백테스트 제한 테스트"""
        manager = UserResourceManager()

        # 여러 사용자가 백테스트 시작
        backtest_count = 0
        max_total = manager.limits["max_total_concurrent_backtests"]

        for user_id in range(1, 100):  # 충분히 많은 사용자
            for _ in range(manager.limits["max_concurrent_backtests_per_user"]):
                can_start, error = manager.can_start_backtest(user_id)

                if backtest_count < max_total:
                    assert can_start is True
                    manager.start_backtest(user_id, backtest_id=backtest_count)
                    backtest_count += 1
                else:
                    assert can_start is False
                    assert "System at capacity" in error
                    return

    def test_can_start_backtest_daily_limit(self):
        """일일 백테스트 제한 테스트"""
        manager = UserResourceManager()
        user_id = 1

        # 일일 제한까지 백테스트 시작 (완료 후 다시 시작 가능하도록)
        daily_limit = manager.limits["max_daily_backtests_per_user"]

        for i in range(daily_limit):
            can_start, error = manager.can_start_backtest(user_id)
            assert can_start is True
            manager.start_backtest(user_id, backtest_id=i)
            manager.finish_backtest(user_id, backtest_id=i)  # 완료 처리

        # 일일 제한 초과 시도
        can_start, error = manager.can_start_backtest(user_id)
        assert can_start is False
        assert "Daily backtest limit reached" in error

    def test_start_and_finish_backtest(self):
        """백테스트 시작 및 완료 테스트"""
        manager = UserResourceManager()
        user_id = 1
        backtest_id = 100

        # 시작
        manager.start_backtest(user_id, backtest_id)
        assert backtest_id in manager.active_backtests[user_id]
        assert manager.daily_backtest_count[user_id] == 1

        # 완료
        manager.finish_backtest(user_id, backtest_id)
        assert backtest_id not in manager.active_backtests[user_id]
        assert manager.daily_backtest_count[user_id] == 1  # 일일 카운트는 유지

    def test_can_start_bot_success(self):
        """봇 시작 가능 - 성공 케이스"""
        manager = UserResourceManager()
        user_id = 1

        can_start, error = manager.can_start_bot(user_id)
        assert can_start is True
        assert error is None

    def test_can_start_bot_limit(self):
        """사용자당 동시 봇 제한 테스트"""
        manager = UserResourceManager()
        user_id = 1

        # 제한까지 봇 시작
        for i in range(manager.limits["max_concurrent_bots_per_user"]):
            can_start, error = manager.can_start_bot(user_id)
            assert can_start is True
            manager.start_bot(user_id, bot_id=f"bot_{i}")

        # 제한 초과 시도
        can_start, error = manager.can_start_bot(user_id)
        assert can_start is False
        assert "Max concurrent bots per user" in error

    def test_start_and_stop_bot(self):
        """봇 시작 및 중지 테스트"""
        manager = UserResourceManager()
        user_id = 1
        bot_id = "test_bot_123"

        # 시작
        manager.start_bot(user_id, bot_id)
        assert bot_id in manager.active_bots[user_id]

        # 중지
        manager.stop_bot(user_id, bot_id)
        assert bot_id not in manager.active_bots[user_id]

    def test_get_user_stats(self):
        """사용자별 통계 조회 테스트"""
        manager = UserResourceManager()
        user_id = 1

        # 백테스트 2개, 봇 1개 시작
        manager.start_backtest(user_id, backtest_id=1)
        manager.start_backtest(user_id, backtest_id=2)
        manager.start_bot(user_id, bot_id="bot_1")

        stats = manager.get_user_stats(user_id)

        assert stats["user_id"] == user_id
        assert stats["active_backtests"] == 2
        assert stats["active_bots"] == 1
        assert stats["daily_backtest_count"] == 2
        assert "limits" in stats

    def test_get_global_stats(self):
        """전체 리소스 통계 조회 테스트"""
        manager = UserResourceManager()

        # 여러 사용자 활동
        manager.start_backtest(user_id=1, backtest_id=1)
        manager.start_backtest(user_id=1, backtest_id=2)
        manager.start_backtest(user_id=2, backtest_id=3)

        manager.start_bot(user_id=1, bot_id="bot_1")
        manager.start_bot(user_id=2, bot_id="bot_2")
        manager.start_bot(user_id=3, bot_id="bot_3")

        stats = manager.get_global_stats()

        assert stats["total_active_backtests"] == 3
        assert stats["total_active_bots"] == 3
        assert stats["active_users"] == 2  # 사용자 1, 2만 백테스트 활성
        assert "limits" in stats

    def test_reset_daily_counts(self):
        """일일 카운트 초기화 테스트"""
        manager = UserResourceManager()

        # 여러 사용자가 백테스트 실행
        for user_id in range(1, 6):
            for i in range(5):
                manager.start_backtest(user_id, backtest_id=user_id * 100 + i)
                manager.finish_backtest(user_id, backtest_id=user_id * 100 + i)

        # 모든 사용자가 카운트 보유
        assert len(manager.daily_backtest_count) == 5
        for user_id in range(1, 6):
            assert manager.daily_backtest_count[user_id] == 5

        # 초기화
        manager.reset_daily_counts()

        # 카운트 리셋 확인
        assert len(manager.daily_backtest_count) == 0

    def test_user_isolation(self):
        """사용자별 격리 테스트"""
        manager = UserResourceManager()

        user1 = 1
        user2 = 2

        # 사용자 1이 제한까지 사용
        for i in range(manager.limits["max_concurrent_backtests_per_user"]):
            manager.start_backtest(user1, backtest_id=i)

        # 사용자 1은 더 이상 시작 불가
        can_start, _ = manager.can_start_backtest(user1)
        assert can_start is False

        # 사용자 2는 여전히 시작 가능 (격리됨)
        can_start, _ = manager.can_start_backtest(user2)
        assert can_start is True

    def test_multiple_finishes(self):
        """동일 백테스트 여러 번 완료 처리 테스트"""
        manager = UserResourceManager()
        user_id = 1
        backtest_id = 999

        manager.start_backtest(user_id, backtest_id)
        manager.finish_backtest(user_id, backtest_id)

        # 두 번째 완료 시도 (에러 없이 무시되어야 함)
        manager.finish_backtest(user_id, backtest_id)

        assert backtest_id not in manager.active_backtests[user_id]


@pytest.mark.asyncio
class TestResourceManagerIntegration:
    """리소스 관리자 통합 테스트"""

    async def test_concurrent_backtest_scenario(self, async_session):
        """동시 백테스트 시나리오 테스트"""
        from src.database.models import User, BacktestResult

        manager = UserResourceManager()

        # 사용자 3명 생성
        users = []
        for i in range(1, 4):
            user = User(
                email=f"user{i}@example.com",
                password_hash="hashed_pw"
            )
            async_session.add(user)
            users.append(user)

        await async_session.commit()
        for user in users:
            await async_session.refresh(user)

        # 각 사용자가 백테스트 시작
        backtest_results = []
        for user in users:
            for i in range(2):  # 사용자당 2개씩
                can_start, error = manager.can_start_backtest(user.id)
                assert can_start is True

                result = BacktestResult(
                    user_id=user.id,
                    initial_balance=10000.0,
                    final_balance=12000.0,
                    status="running"
                )
                async_session.add(result)
                await async_session.commit()
                await async_session.refresh(result)

                manager.start_backtest(user.id, result.id)
                backtest_results.append(result)

        # 전체 통계 확인
        stats = manager.get_global_stats()
        assert stats["total_active_backtests"] == 6
        assert stats["active_users"] == 3

        # 백테스트 완료 처리
        for result in backtest_results:
            result.status = "completed"
            manager.finish_backtest(result.user_id, result.id)

        await async_session.commit()

        # 모든 백테스트 완료 확인
        stats = manager.get_global_stats()
        assert stats["total_active_backtests"] == 0
