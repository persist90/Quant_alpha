"""PriceLoader Upsert 로직 테스트 (SQLite 인메모리 DB 사용)."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

KST = ZoneInfo("Asia/Seoul")


@pytest.fixture()
def sqlite_engine():
    """SQLite 인메모리 엔진 + ORM 테이블 생성."""
    from quant_alpha.common.models.market_data import Base

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


def _make_daily_df() -> pd.DataFrame:
    """테스트용 일봉 DataFrame."""
    index = pd.DatetimeIndex(
        [datetime(2024, 1, 2, tzinfo=KST), datetime(2024, 1, 3, tzinfo=KST)]
    )
    return pd.DataFrame(
        {"ticker": ["005930", "005930"],
         "open": [70000.0, 71000.0], "high": [72000.0, 73000.0],
         "low": [69000.0, 70000.0], "close": [71000.0, 72000.0],
         "volume": [10000, 11000], "trading_value": [710000000, 792000000],
         "shares_outstanding": [5000000, 5000000],
         "last_updated": [datetime.now(KST), datetime.now(KST)]},
        index=index,
    )


def _make_intraday_df() -> pd.DataFrame:
    """테스트용 4H봉 DataFrame."""
    index = pd.DatetimeIndex([
        datetime(2024, 1, 2, 9, 0, tzinfo=KST),
        datetime(2024, 1, 2, 13, 0, tzinfo=KST),
    ])
    return pd.DataFrame(
        {"ticker": ["005930", "005930"],
         "open": [70000.0, 71000.0], "high": [72000.0, 73000.0],
         "low": [69000.0, 70000.0], "close": [71000.0, 72000.0],
         "volume": [5000, 6000],
         "fetched_at": [datetime.now(KST), datetime.now(KST)]},
        index=index,
    )


class TestPriceLoaderDaily:
    def test_upsert_daily_inserts_rows(self, sqlite_engine):
        """정상 DataFrame Upsert 시 행이 삽입되어야 한다."""
        from quant_alpha.l1_ingestion.market_price.loader import PriceLoader

        loader = PriceLoader(engine=sqlite_engine)
        df = _make_daily_df()
        rows = loader.upsert_daily(df)

        assert rows == 2

    def test_upsert_daily_idempotent(self, sqlite_engine):
        """동일 데이터 2회 Upsert 시 중복 삽입 없음 (행 수 동일)."""
        from quant_alpha.l1_ingestion.market_price.loader import PriceLoader

        loader = PriceLoader(engine=sqlite_engine)
        df = _make_daily_df()

        loader.upsert_daily(df)
        loader.upsert_daily(df)

        with sqlite_engine.connect() as conn:
            result = conn.execute(
                text("SELECT COUNT(*) FROM daily_price WHERE ticker='005930'")
            )
            count = result.scalar()
        assert count == 2

    def test_upsert_daily_empty_df_returns_zero(self, sqlite_engine):
        """빈 DataFrame 입력 시 0 반환, 예외 없음."""
        from quant_alpha.l1_ingestion.market_price.loader import PriceLoader

        loader = PriceLoader(engine=sqlite_engine)
        rows = loader.upsert_daily(pd.DataFrame())
        assert rows == 0

    def test_upsert_daily_updates_on_conflict(self, sqlite_engine):
        """동일 (date, ticker)에 다른 값 재적재 시 close 값이 갱신되어야 한다."""
        from quant_alpha.l1_ingestion.market_price.loader import PriceLoader

        loader = PriceLoader(engine=sqlite_engine)
        df_original = _make_daily_df()
        loader.upsert_daily(df_original)

        df_updated = _make_daily_df()
        df_updated["close"] = [99999.0, 99999.0]
        loader.upsert_daily(df_updated)

        with sqlite_engine.connect() as conn:
            result = conn.execute(
                text("SELECT close FROM daily_price WHERE ticker='005930' LIMIT 1")
            )
            close_val = result.scalar()
        assert close_val == 99999.0


class TestPriceLoaderIntraday:
    def test_upsert_intraday_inserts_rows(self, sqlite_engine):
        """4H봉 정상 Upsert 시 행이 삽입되어야 한다."""
        from quant_alpha.l1_ingestion.market_price.loader import PriceLoader

        loader = PriceLoader(engine=sqlite_engine)
        df = _make_intraday_df()
        rows = loader.upsert_intraday_4h(df)

        assert rows == 2

    def test_upsert_intraday_empty_df_returns_zero(self, sqlite_engine):
        """빈 DataFrame 입력 시 0 반환, 예외 없음."""
        from quant_alpha.l1_ingestion.market_price.loader import PriceLoader

        loader = PriceLoader(engine=sqlite_engine)
        rows = loader.upsert_intraday_4h(pd.DataFrame())
        assert rows == 0
