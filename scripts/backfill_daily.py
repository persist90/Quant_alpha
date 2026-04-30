"""KOSDAQ 150 일봉(15년) + 4H봉(최대 730일) 역사적 데이터 수집 스크립트.

월 단위 배치 처리로 진행 상황을 저장하며 실행. 중간 실패 시 재실행하면
이미 적재된 달은 upsert(덮어쓰기)로 안전하게 건너뜁니다.

4H봉은 yfinance 제약으로 최대 730일(약 2년) 지원.

Usage:
    poetry run python scripts/backfill_daily.py
    poetry run python scripts/backfill_daily.py --start 20110430 --end 20260429
    poetry run python scripts/backfill_daily.py --include-4h
    poetry run python scripts/backfill_daily.py --start 20110430 --include-4h
"""

import argparse
import sys
import time
from datetime import date, timedelta

import pandas as pd

sys.path.insert(0, "src")

from quant_alpha.common.database import create_tables
from quant_alpha.common.logger import get_logger
from quant_alpha.l1_ingestion.market_price.fetcher import (
    DailyPriceFetcher,
    HistoricalIntraday4HFetcher,
    _inject_krx_env,
)
from quant_alpha.l1_ingestion.market_price.loader import PriceLoader

log = get_logger(__name__)

DEFAULT_START = (date.today() - timedelta(days=365 * 15)).strftime("%Y%m%d")
DEFAULT_END = (date.today() - timedelta(days=1)).strftime("%Y%m%d")


def _month_batches(start: str, end: str) -> list[tuple[str, str]]:
    """start~end 범위를 월 단위로 분할. 각 배치: (월 첫 영업일, 월 마지막 영업일)."""
    dates = pd.Series(pd.bdate_range(start, end))
    if dates.empty:
        return []
    months = dates.dt.to_period("M").unique()
    batches = []
    for month in months:
        month_dates = dates[dates.dt.to_period("M") == month]
        batches.append((
            month_dates.iloc[0].strftime("%Y%m%d"),
            month_dates.iloc[-1].strftime("%Y%m%d"),
        ))
    return batches


def run_daily_backfill(start: str, end: str, loader: PriceLoader) -> int:
    batches = _month_batches(start, end)
    total_batches = len(batches)
    total_rows = 0

    log.info("daily_backfill_start", start=start, end=end, batches=total_batches)
    print(f"\n{'='*60}")
    print(f"KOSDAQ 150 일봉 백필 시작")
    print(f"기간: {start} ~ {end}  |  배치: {total_batches}개월")
    print(f"예상 소요시간: {total_batches * 0.8:.0f}~{total_batches * 1.2:.0f}분")
    print(f"{'='*60}\n")

    for idx, (batch_start, batch_end) in enumerate(batches, 1):
        t0 = time.time()
        print(f"[{idx:3d}/{total_batches}] {batch_start} ~ {batch_end} 수집 중...", end=" ", flush=True)

        try:
            fetcher = DailyPriceFetcher(start_date=batch_start, end_date=batch_end)
            df = fetcher.fetch()

            if df.empty:
                print("데이터 없음 (휴장기간)")
                continue

            rows = loader.upsert_daily(df)
            total_rows += rows
            elapsed = time.time() - t0
            print(f"완료 ({rows}행, {elapsed:.1f}초)")

        except Exception as e:
            print(f"실패: {e}")
            log.error("backfill_batch_failed", batch_start=batch_start, batch_end=batch_end, error=str(e))

        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"일봉 백필 완료: 총 {total_rows:,}행 적재")
    print(f"{'='*60}\n")
    log.info("daily_backfill_done", total_rows=total_rows)
    return total_rows


def run_4h_backfill(tickers: list[str], loader: PriceLoader) -> int:
    """yfinance 기반 4H봉 역사적 수집 (최대 730일)."""
    end = date.today().strftime("%Y%m%d")
    start = (date.today() - timedelta(days=730)).strftime("%Y%m%d")

    print(f"\n{'='*60}")
    print(f"KOSDAQ 150 4H봉 역사적 수집 (yfinance)")
    print(f"기간: {start} ~ {end}  |  종목: {len(tickers)}개")
    print(f"주의: yfinance 1H 데이터 최대 730일 지원 — 그 이전 4H 데이터는 미수집")
    print(f"예상 소요시간: {len(tickers) // 20 * 1 + 5}분 내외")
    print(f"{'='*60}\n")

    fetcher = HistoricalIntraday4HFetcher(start_date=start, end_date=end)
    df = fetcher.fetch(tickers)

    if df.empty:
        print("4H 데이터 없음 (yfinance 커버리지 확인 필요)")
        log.warning("4h_backfill_empty")
        return 0

    rows = loader.upsert_intraday_4h(df)
    print(f"\n4H봉 완료: 총 {rows:,}행 적재")
    log.info("4h_backfill_done", total_rows=rows)
    return rows


def run_backfill(start: str, end: str, include_4h: bool = False) -> None:
    _inject_krx_env()
    create_tables()
    loader = PriceLoader()

    # 1) 일봉 15년 백필
    run_daily_backfill(start, end, loader)

    # 2) 4H봉 역사적 수집 (옵션)
    if include_4h:
        # KOSDAQ 150 티커 목록은 일봉 fetcher에서 재사용
        temp_fetcher = DailyPriceFetcher(start_date=end, end_date=end)
        tickers = temp_fetcher._get_kosdaq150_tickers()
        if tickers:
            run_4h_backfill(tickers, loader)
        else:
            print("KOSDAQ 150 티커 목록 조회 실패 — 4H 수집 건너뜀")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KOSDAQ 150 역사적 데이터 수집 (일봉 15년 + 4H봉)")
    parser.add_argument("--start", default=DEFAULT_START, help="시작일 YYYYMMDD (기본: 15년 전)")
    parser.add_argument("--end", default=DEFAULT_END, help="종료일 YYYYMMDD (기본: 어제)")
    parser.add_argument("--include-4h", action="store_true", help="4H봉 역사적 수집 포함 (yfinance, 최대 730일)")
    args = parser.parse_args()

    run_backfill(start=args.start, end=args.end, include_4h=args.include_4h)
