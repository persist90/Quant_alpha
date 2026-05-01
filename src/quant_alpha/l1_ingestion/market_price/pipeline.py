"""L1 시장 데이터 수집 Prefect Flow: 일봉 + 4H봉 통합 파이프라인."""

import json
import urllib.request
from datetime import date
from zoneinfo import ZoneInfo

from prefect import flow, task
from prefect.logging import get_run_logger

from quant_alpha.common.config import settings
from quant_alpha.common.database import create_tables
from quant_alpha.l1_ingestion.market_price.fetcher import (
    DailyPriceFetcher,
    Intraday4HFetcher,
)
from quant_alpha.l1_ingestion.market_price.loader import PriceLoader

KST = ZoneInfo("Asia/Seoul")


def _default_date_range() -> tuple[str, str]:
    """기본 수집 범위: 오늘 (15:40 장 마감 후 실행 기준)."""
    ds = date.today().strftime("%Y%m%d")
    return ds, ds


def _notify_slack(message: str) -> None:
    """Slack Webhook 알림. slack_webhook_url 미설정 시 silent skip."""
    if not settings.slack_webhook_url:
        return
    try:
        payload = json.dumps({"text": message}).encode()
        req = urllib.request.Request(
            settings.slack_webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # 알림 실패가 파이프라인을 멈추면 안 됨


@task(
    name="fetch_daily_prices",
    retries=3,
    retry_delay_seconds=60,
    timeout_seconds=600,
    tags=["layer:L1", "source:pykrx"],
)
def fetch_daily_prices_task(start_date: str, end_date: str):  # type: ignore[return]
    """pykrx로 KOSDAQ 150 일봉 수집."""
    logger = get_run_logger()
    logger.info(f"일봉 수집 시작: {start_date} ~ {end_date}")
    fetcher = DailyPriceFetcher(start_date=start_date, end_date=end_date)
    return fetcher.fetch()


@task(
    name="fetch_intraday_4h_prices",
    retries=3,
    retry_delay_seconds=60,
    timeout_seconds=900,
    tags=["layer:L1", "source:kis"],
)
def fetch_intraday_4h_task(tickers: list[str], start_date: str, end_date: str):  # type: ignore[return]
    """한투 API로 4시간봉 수집."""
    logger = get_run_logger()
    logger.info(f"4H봉 수집 시작: {len(tickers)}종목, {start_date} ~ {end_date}")
    fetcher = Intraday4HFetcher(start_date=start_date, end_date=end_date)
    return fetcher.fetch(tickers)


@task(
    name="load_daily_prices",
    tags=["layer:L1", "target:timescaledb"],
)
def load_daily_task(df) -> int:  # type: ignore[return]
    """일봉 데이터 TimescaleDB Upsert."""
    loader = PriceLoader()
    return loader.upsert_daily(df)


@task(
    name="load_intraday_4h_prices",
    tags=["layer:L1", "target:timescaledb"],
)
def load_intraday_task(df) -> int:  # type: ignore[return]
    """4H봉 데이터 TimescaleDB Upsert."""
    loader = PriceLoader()
    return loader.upsert_intraday_4h(df)


@flow(
    name="l1_market_price_pipeline",
    description="KOSDAQ 150 일봉(pykrx) + 4H봉(한투 API) 수집 후 TimescaleDB 적재. 매일 15:40 이후 실행.",
)
def market_price_pipeline(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, int]:
    """L1 시장 데이터 수집 메인 Flow.

    Args:
        start_date: 수집 시작일 (YYYYMMDD). None이면 오늘(장 마감 후 실행 기준).
        end_date: 수집 종료일 (YYYYMMDD). None이면 오늘.

    Returns:
        {"daily_rows": N, "intraday_rows": M}
    """
    create_tables()

    if start_date is None or end_date is None:
        start_date, end_date = _default_date_range()

    try:
        # 일봉 수집 → 적재
        daily_df = fetch_daily_prices_task(start_date, end_date)
        daily_rows = load_daily_task(daily_df)

        # 4H봉: 일봉에서 종목 리스트 추출 후 수집 → 적재
        tickers: list[str] = []
        if not daily_df.empty and "ticker" in daily_df.columns:
            tickers = daily_df["ticker"].unique().tolist()

        intraday_df = fetch_intraday_4h_task(tickers, start_date, end_date)
        intraday_rows = load_intraday_task(intraday_df)

        result = {"daily_rows": daily_rows, "intraday_rows": intraday_rows}
        _notify_slack(
            f"✅ L1 파이프라인 완료 [{start_date}]\n"
            f"• 일봉: {daily_rows:,}행\n"
            f"• 4H봉: {intraday_rows:,}행"
        )
        return result

    except Exception as exc:
        _notify_slack(f"❌ L1 파이프라인 실패 [{start_date}]\n오류: {exc}")
        raise


if __name__ == "__main__":
    market_price_pipeline()
