"""KOSDAQ 150 일봉 5년치 역사적 데이터 수집 스크립트.

월 단위 배치 처리로 진행 상황을 저장하며 실행. 중간 실패 시 재실행하면
이미 적재된 달은 upsert(덮어쓰기)로 안전하게 건너뜁니다.

Usage:
    poetry run python scripts/backfill_daily.py
    poetry run python scripts/backfill_daily.py --start 20210101 --end 20260428
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
    _inject_krx_env,
)
from quant_alpha.l1_ingestion.market_price.loader import PriceLoader

log = get_logger(__name__)

DEFAULT_START = (date.today() - timedelta(days=365 * 5)).strftime("%Y%m%d")
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


def run_backfill(start: str, end: str) -> None:
    _inject_krx_env()
    create_tables()
    loader = PriceLoader()

    batches = _month_batches(start, end)
    total_batches = len(batches)
    total_rows = 0

    log.info("backfill_start", start=start, end=end, batches=total_batches)
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

        time.sleep(0.5)  # 배치 간 세션 부하 완화

    print(f"\n{'='*60}")
    print(f"백필 완료: 총 {total_rows:,}행 적재")
    print(f"{'='*60}\n")
    log.info("backfill_done", total_rows=total_rows)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="KOSDAQ 150 일봉 역사적 데이터 수집")
    parser.add_argument("--start", default=DEFAULT_START, help="시작일 YYYYMMDD (기본: 5년 전)")
    parser.add_argument("--end", default=DEFAULT_END, help="종료일 YYYYMMDD (기본: 어제)")
    args = parser.parse_args()

    run_backfill(start=args.start, end=args.end)
