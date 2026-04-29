"""TimescaleDB Upsert 적재기: daily_price / intraday_price_4h."""

from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy.engine import Engine

from quant_alpha.common.database import get_engine
from quant_alpha.common.logger import get_logger
from quant_alpha.common.models.market_data import DailyPrice, IntradayPrice4H

log = get_logger(__name__)

_DAILY_UPSERT_COLS = ["open", "high", "low", "close", "volume",
                      "trading_value", "shares_outstanding", "last_updated"]
_INTRADAY_UPSERT_COLS = ["open", "high", "low", "close", "volume", "fetched_at"]


def _dialect_insert(engine: Engine, model: Any):
    """SQLAlchemy dialect-aware insert factory (PostgreSQL / SQLite)."""
    dialect = engine.dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as pg_insert
        return pg_insert(model)
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert
    return sqlite_insert(model)


class PriceLoader:
    """수집된 DataFrame을 TimescaleDB에 Upsert하는 적재기."""

    def __init__(self, engine: Engine | None = None) -> None:
        self.engine = engine or get_engine()

    def upsert_daily(self, df: pd.DataFrame) -> int:
        """일봉 DataFrame을 daily_price 테이블에 Upsert.

        Args:
            df: DailyPriceFetcher.fetch() 반환 DataFrame
                (index=date[tz-aware], columns=[ticker, open, high, low, close, ...])

        Returns:
            적재된 행 수
        """
        if df.empty:
            log.warning("upsert_daily_empty")
            return 0

        records = _prepare_daily_records(df)
        with self.engine.begin() as conn:
            stmt = _dialect_insert(self.engine, DailyPrice).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["date", "ticker"],
                set_={col: getattr(stmt.excluded, col) for col in _DAILY_UPSERT_COLS},
            )
            conn.execute(stmt)

        log.info("upsert_daily_done", rows=len(records))
        return len(records)

    def upsert_intraday_4h(self, df: pd.DataFrame) -> int:
        """4H봉 DataFrame을 intraday_price_4h 테이블에 Upsert.

        Args:
            df: Intraday4HFetcher.fetch() 반환 DataFrame
                (index=datetime[tz-aware], columns=[ticker, open, high, low, close, volume, fetched_at])

        Returns:
            적재된 행 수
        """
        if df.empty:
            log.warning("upsert_intraday_empty")
            return 0

        records = _prepare_intraday_records(df)
        with self.engine.begin() as conn:
            stmt = _dialect_insert(self.engine, IntradayPrice4H).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=["datetime", "ticker"],
                set_={col: getattr(stmt.excluded, col) for col in _INTRADAY_UPSERT_COLS},
            )
            conn.execute(stmt)

        log.info("upsert_intraday_done", rows=len(records))
        return len(records)


def _prepare_daily_records(df: pd.DataFrame) -> list[dict]:
    """DataFrame → daily_price INSERT 레코드 리스트 변환."""
    records = []
    for idx, row in df.iterrows():
        dt = idx if isinstance(idx, date) else idx.date()
        records.append({
            "date": dt,
            "ticker": str(row["ticker"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
            "trading_value": int(row["trading_value"]) if pd.notna(row.get("trading_value")) else None,
            "shares_outstanding": int(row["shares_outstanding"]) if pd.notna(row.get("shares_outstanding")) else None,
            "last_updated": row["last_updated"],
        })
    return records


def _prepare_intraday_records(df: pd.DataFrame) -> list[dict]:
    """DataFrame → intraday_price_4h INSERT 레코드 리스트 변환."""
    records = []
    for idx, row in df.iterrows():
        records.append({
            "datetime": idx,
            "ticker": str(row["ticker"]),
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
            "fetched_at": row["fetched_at"],
        })
    return records
