#!/usr/bin/env python3
"""
Binance 과거 캔들 데이터 다운로드 스크립트

바이낸스 Futures API를 사용하여 백테스트용 과거 캔들 데이터를 수집합니다.

사용법:
    # BTC, ETH만 다운로드 (권장, 테스트용)
    python3 download_binance_data.py --btc-eth

    # 모든 메이저 코인 다운로드
    python3 download_binance_data.py --all

    # 특정 코인만 다운로드
    python3 download_binance_data.py --symbols BTCUSDT ETHUSDT SOLUSDT

    # 특정 타임프레임만
    python3 download_binance_data.py --btc-eth --timeframes 1h 4h

작성일: 2025-12-13
"""

import asyncio
import sys
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# 프로젝트 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

from src.services.binance_rest import BinanceRestClient
from src.services.candle_cache import CandleCacheManager

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("binance_download.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


# =====================================================
# 코인별 바이낸스 선물 상장일
# =====================================================
# 참고: 정확한 상장일은 Binance 공식 발표 기준
# 여유있게 설정하여 누락 방지

COIN_START_DATES = {
    # 주요 코인 (초기 상장)
    "BTCUSDT": "2019-09-08",  # BTC - 바이낸스 선물 런칭
    "ETHUSDT": "2019-11-08",  # ETH
    "XRPUSDT": "2020-01-06",  # XRP
    # 2020년 상장
    "LINKUSDT": "2020-02-03",  # LINK
    "ADAUSDT": "2020-04-16",  # ADA
    "DOTUSDT": "2020-08-18",  # DOT
    # 2021년 상장
    "MATICUSDT": "2021-02-22",  # MATIC (현 POL)
    "DOGEUSDT": "2021-04-19",  # DOGE
    "SOLUSDT": "2021-06-17",  # SOL
    "AVAXUSDT": "2021-09-16",  # AVAX
    # 추가 인기 코인
    "BNBUSDT": "2020-02-10",  # BNB
    "LTCUSDT": "2019-12-24",  # LTC
    "ETCUSDT": "2019-12-02",  # ETC
    "XLMUSDT": "2020-03-13",  # XLM
    "TRXUSDT": "2019-12-24",  # TRX
}

# 안정적인 코인 (테스트용)
STABLE_COINS = ["BTCUSDT", "ETHUSDT"]

# 메이저 코인 (10개)
MAJOR_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    "XRPUSDT",
    "SOLUSDT",
    "DOGEUSDT",
    "ADAUSDT",
    "AVAXUSDT",
    "LINKUSDT",
    "DOTUSDT",
    "MATICUSDT",
]

# 기본 타임프레임
DEFAULT_TIMEFRAMES = ["1h", "4h"]


# =====================================================
# 다운로드 함수
# =====================================================


async def download_candles(
    symbols: List[str],
    timeframes: List[str],
    start_date: Optional[str] = None,
    use_coin_start_dates: bool = True,
) -> bool:
    """
    바이낸스에서 캔들 데이터 다운로드

    Args:
        symbols: 다운로드할 심볼 리스트
        timeframes: 다운로드할 타임프레임 리스트
        start_date: 시작 날짜 (None이면 코인별 상장일 사용)
        use_coin_start_dates: 코인별 상장일 사용 여부

    Returns:
        성공 여부 (True: 모두 성공, False: 일부 실패)
    """
    cache = CandleCacheManager()
    client = BinanceRestClient()

    total = len(symbols) * len(timeframes)
    completed = 0
    success_data = []
    failed = []

    end_date = datetime.now().strftime("%Y-%m-%d")

    # 헤더 출력
    print()
    logger.info("=" * 70)
    logger.info("🚀 Binance 캔들 데이터 다운로드")
    logger.info("=" * 70)
    logger.info(f"💰 코인: {', '.join(symbols)}")
    logger.info(f"⏱️ 타임프레임: {', '.join(timeframes)}")
    logger.info(f"📅 종료일: {end_date}")

    if use_coin_start_dates:
        logger.info("📅 시작일: 코인별 상장일")
        for sym in symbols:
            start = COIN_START_DATES.get(sym, "2020-01-01")
            logger.info(f"   - {sym}: {start}")
    elif start_date:
        logger.info(f"📅 시작일: {start_date} (공통)")

    logger.info("=" * 70)
    print()

    start_time = datetime.now()

    for symbol in symbols:
        # 시작 날짜 결정
        if use_coin_start_dates:
            actual_start = COIN_START_DATES.get(symbol, "2020-01-01")
        else:
            actual_start = start_date or "2020-01-01"

        for timeframe in timeframes:
            completed += 1
            progress = f"[{completed}/{total}]"

            logger.info(
                f"{progress} 📥 {symbol} {timeframe} ({actual_start} ~ {end_date})"
            )

            try:
                # Binance API로 데이터 수집
                candles = await client.get_all_historical_klines(
                    symbol=symbol,
                    interval=timeframe,
                    start_time=actual_start,
                    end_time=end_date,
                )

                if candles:
                    # 캐시에 저장
                    cache._save_to_file_cache(symbol, timeframe, candles)
                    count = len(candles)
                    logger.info(
                        f"{progress} ✅ {symbol} {timeframe}: {count:,}개 캔들 저장 완료"
                    )
                    success_data.append((symbol, timeframe, count))
                else:
                    logger.warning(f"{progress} ⚠️ {symbol} {timeframe}: 데이터 없음")
                    failed.append((symbol, timeframe, "데이터 없음"))

            except Exception as e:
                error_msg = str(e)[:100]
                logger.error(f"{progress} ❌ {symbol} {timeframe} 실패: {error_msg}")
                failed.append((symbol, timeframe, error_msg))

            # Rate Limit 방지 (코인 간)
            await asyncio.sleep(0.5)

        # 다음 코인 전 잠시 대기
        await asyncio.sleep(1)

    await client.close()

    # 완료 리포트
    elapsed = datetime.now() - start_time

    print()
    logger.info("=" * 70)
    logger.info("📊 다운로드 완료 리포트")
    logger.info("=" * 70)
    logger.info(f"✅ 성공: {len(success_data)}/{total}")
    logger.info(f"❌ 실패: {len(failed)}/{total}")
    logger.info(f"⏱️ 소요 시간: {elapsed}")

    if success_data:
        total_candles = sum(c for _, _, c in success_data)
        logger.info(f"📊 총 캔들: {total_candles:,}개")

        # 상세 결과
        logger.info("")
        logger.info("📋 성공 목록:")
        for symbol, timeframe, count in success_data:
            logger.info(f"   ✅ {symbol} {timeframe}: {count:,}개")

    if failed:
        logger.info("")
        logger.info("❌ 실패 목록:")
        for symbol, timeframe, error in failed:
            logger.info(f"   ❌ {symbol} {timeframe}: {error}")

    # 캐시 상태
    cache_info = cache.get_cache_info()
    logger.info("")
    logger.info(f"💾 캐시 디렉토리: {cache_info['cache_dir']}")
    logger.info(f"💾 총 캐시 파일: {cache_info['total_files']}개")
    logger.info("=" * 70)
    print()

    return len(failed) == 0


async def download_btc_eth() -> bool:
    """BTC, ETH만 다운로드 (권장, 테스트용)"""
    return await download_candles(
        symbols=STABLE_COINS,
        timeframes=["1h", "4h", "1d"],
        use_coin_start_dates=True,
    )


async def download_major_coins() -> bool:
    """메이저 코인 10개 다운로드"""
    return await download_candles(
        symbols=MAJOR_COINS,
        timeframes=DEFAULT_TIMEFRAMES,
        use_coin_start_dates=True,
    )


async def download_all_coins() -> bool:
    """지원하는 모든 코인 다운로드"""
    return await download_candles(
        symbols=list(COIN_START_DATES.keys()),
        timeframes=DEFAULT_TIMEFRAMES,
        use_coin_start_dates=True,
    )


async def download_custom(
    symbols: List[str],
    timeframes: List[str],
    start_date: Optional[str] = None,
) -> bool:
    """사용자 지정 다운로드"""
    return await download_candles(
        symbols=symbols,
        timeframes=timeframes,
        start_date=start_date,
        use_coin_start_dates=(start_date is None),
    )


# =====================================================
# 캐시 상태 확인
# =====================================================


def show_cache_status():
    """현재 캐시 상태 출력"""
    cache = CandleCacheManager()
    info = cache.get_cache_info()

    print()
    print("=" * 70)
    print("💾 캐시 상태")
    print("=" * 70)
    print(f"📁 캐시 디렉토리: {info['cache_dir']}")
    print(f"📊 총 파일 수: {info['total_files']}개")
    print()

    if info["caches"]:
        print("📋 캐시 파일 목록:")
        for name, data in sorted(info["caches"].items()):
            count = data.get("count", "N/A")
            size_mb = data.get("size_mb", 0)
            updated = data.get("updated_at", "N/A")
            if updated != "N/A":
                updated = updated[:19]  # ISO 형식에서 시간까지만

            print(f"   {name}: {count:,}개 캔들, {size_mb}MB, updated: {updated}")
    else:
        print("   (캐시 파일 없음)")

    print("=" * 70)
    print()


# =====================================================
# 메인
# =====================================================


def main():
    parser = argparse.ArgumentParser(
        description="Binance 캔들 데이터 다운로드",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python3 download_binance_data.py --btc-eth
  python3 download_binance_data.py --all
  python3 download_binance_data.py --symbols BTCUSDT ETHUSDT --timeframes 1h 4h
  python3 download_binance_data.py --status
        """,
    )

    # 다운로드 모드
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--btc-eth", action="store_true", help="BTC, ETH만 다운로드 (1h, 4h, 1d)"
    )
    mode_group.add_argument(
        "--major", action="store_true", help="메이저 코인 10개 다운로드 (1h, 4h)"
    )
    mode_group.add_argument(
        "--all", action="store_true", help="모든 지원 코인 다운로드 (1h, 4h)"
    )
    mode_group.add_argument("--status", action="store_true", help="현재 캐시 상태 확인")

    # 커스텀 옵션
    parser.add_argument(
        "--symbols", nargs="+", help="다운로드할 심볼 (예: BTCUSDT ETHUSDT)"
    )
    parser.add_argument(
        "--timeframes",
        nargs="+",
        default=["1h", "4h"],
        help="다운로드할 타임프레임 (기본: 1h 4h)",
    )
    parser.add_argument(
        "--start-date", type=str, help="시작 날짜 (YYYY-MM-DD, 기본: 코인별 상장일)"
    )

    args = parser.parse_args()

    # 실행
    if args.status:
        show_cache_status()
        return 0

    if args.btc_eth:
        success = asyncio.run(download_btc_eth())
    elif args.major:
        success = asyncio.run(download_major_coins())
    elif args.all:
        success = asyncio.run(download_all_coins())
    elif args.symbols:
        success = asyncio.run(
            download_custom(
                symbols=[s.upper() for s in args.symbols],
                timeframes=args.timeframes,
                start_date=args.start_date,
            )
        )
    else:
        # 기본: 도움말 출력
        parser.print_help()
        print()
        print("💡 빠른 시작:")
        print("   python3 download_binance_data.py --btc-eth")
        return 0

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
