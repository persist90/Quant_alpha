"""DailyPriceFetcher / Intraday4HFetcher 단위 테스트 (API Mocking)."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

KST = ZoneInfo("Asia/Seoul")
START = "20240101"
END = "20240131"


def _make_daily_df(tickers: list[str]) -> pd.DataFrame:
    """테스트용 pykrx 반환 형식 DataFrame 생성."""
    index = pd.to_datetime(["2024-01-02", "2024-01-03"]).tz_localize(KST)
    frames = []
    for ticker in tickers:
        df = pd.DataFrame(
            {"시가": [100.0, 101.0], "고가": [105.0, 106.0],
             "저가": [99.0, 100.0], "종가": [103.0, 104.0],
             "거래량": [10000, 11000], "거래대금": [1030000, 1144000],
             "상장주식수": [500000, 500000]},
            index=index,
        )
        frames.append((ticker, df))
    return frames


def _make_1h_df() -> pd.DataFrame:
    """테스트용 1H 봉 DataFrame (09:00 ~ 15:00)."""
    index = pd.date_range("2024-01-02 09:00", periods=7, freq="1h", tz=KST)
    return pd.DataFrame(
        {"open": [100.0] * 7, "high": [105.0] * 7, "low": [99.0] * 7,
         "close": [103.0] * 7, "volume": [1000] * 7},
        index=index,
    )


# ── DailyPriceFetcher ──────────────────────────────────────────────────────

class TestDailyPriceFetcher:
    def test_fetch_returns_dataframe(self, mocker):
        """정상 수집 시 DatetimeIndex DataFrame 반환."""
        from quant_alpha.l1_ingestion.market_price.fetcher import DailyPriceFetcher

        mocker.patch(
            "quant_alpha.l1_ingestion.market_price.fetcher.DailyPriceFetcher"
            "._get_kosdaq150_tickers",
            return_value=["005930", "000660"],
        )
        ticker_dfs = dict(_make_daily_df(["005930", "000660"]))
        mocker.patch(
            "quant_alpha.l1_ingestion.market_price.fetcher.DailyPriceFetcher"
            "._fetch_single",
            side_effect=lambda t: ticker_dfs.get(t, pd.DataFrame()),
        )

        fetcher = DailyPriceFetcher(start_date=START, end_date=END)
        df = fetcher.fetch()

        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert isinstance(df.index, pd.DatetimeIndex)
        assert df.index.tz is not None

    def test_fetch_columns_snake_case(self, mocker):
        """컬럼명이 snake_case 표준 형식으로 반환되어야 한다."""
        from quant_alpha.l1_ingestion.market_price.fetcher import DailyPriceFetcher

        mocker.patch(
            "quant_alpha.l1_ingestion.market_price.fetcher.DailyPriceFetcher"
            "._get_kosdaq150_tickers",
            return_value=["005930"],
        )
        _, sample_df = _make_daily_df(["005930"])[0]
        mocker.patch(
            "quant_alpha.l1_ingestion.market_price.fetcher.DailyPriceFetcher"
            "._fetch_single",
            return_value=sample_df.rename(columns={
                "시가": "open", "고가": "high", "저가": "low",
                "종가": "close", "거래량": "volume", "거래대금": "trading_value",
                "상장주식수": "shares_outstanding",
            }).assign(ticker="005930", last_updated=datetime.now(KST)),
        )

        fetcher = DailyPriceFetcher(start_date=START, end_date=END)
        df = fetcher.fetch()

        for col in ["open", "high", "low", "close", "volume", "ticker"]:
            assert col in df.columns, f"컬럼 누락: {col}"

    def test_fetch_empty_on_all_failures(self, mocker):
        """모든 종목 수집 실패 시 빈 DataFrame 반환 (예외 전파 없음)."""
        from quant_alpha.l1_ingestion.market_price.fetcher import DailyPriceFetcher

        mocker.patch(
            "quant_alpha.l1_ingestion.market_price.fetcher.DailyPriceFetcher"
            "._get_kosdaq150_tickers",
            return_value=["999999"],
        )
        mocker.patch(
            "quant_alpha.l1_ingestion.market_price.fetcher.DailyPriceFetcher"
            "._fetch_single",
            side_effect=RuntimeError("API 오류"),
        )

        fetcher = DailyPriceFetcher(start_date=START, end_date=END)
        df = fetcher.fetch()
        assert df.empty


# ── Intraday4HFetcher ──────────────────────────────────────────────────────

class TestIntraday4HFetcher:
    def test_resample_produces_4h_bars(self, mocker):
        """1H 봉 → 4H 리샘플 후 바 수가 줄어들어야 한다."""
        mocker.patch(
            "quant_alpha.l1_ingestion.market_price.fetcher.Intraday4HFetcher"
            "._init_broker",
            return_value=None,
        )
        from quant_alpha.l1_ingestion.market_price.fetcher import Intraday4HFetcher

        fetcher = Intraday4HFetcher.__new__(Intraday4HFetcher)
        fetcher.start_date = START
        fetcher.end_date = END
        fetcher._broker = None

        df_1h = _make_1h_df()
        df_4h = fetcher._resample_to_4h(df_1h)

        assert len(df_4h) < len(df_1h)
        assert "open" in df_4h.columns
        assert "close" in df_4h.columns
        assert df_4h["high"].max() >= df_4h["open"].max()

    def test_resample_ohlc_correctness(self, mocker):
        """4H 리샘플 후 high는 구간 내 최대, low는 최소여야 한다."""
        mocker.patch(
            "quant_alpha.l1_ingestion.market_price.fetcher.Intraday4HFetcher"
            "._init_broker",
            return_value=None,
        )
        from quant_alpha.l1_ingestion.market_price.fetcher import Intraday4HFetcher

        fetcher = Intraday4HFetcher.__new__(Intraday4HFetcher)
        fetcher.start_date = START
        fetcher.end_date = END

        index = pd.date_range("2024-01-02 09:00", periods=4, freq="1h", tz=KST)
        df_1h = pd.DataFrame(
            {"open": [100, 101, 102, 103], "high": [110, 105, 108, 107],
             "low": [98, 99, 100, 101], "close": [101, 102, 103, 104],
             "volume": [1000, 1100, 1200, 1300]},
            index=index,
        )
        df_4h = fetcher._resample_to_4h(df_1h)

        assert df_4h.iloc[0]["high"] == 110.0
        assert df_4h.iloc[0]["low"] == 98.0
        assert df_4h.iloc[0]["open"] == 100.0
        assert df_4h.iloc[0]["close"] == 104.0

    def test_fetch_returns_empty_on_failure(self, mocker):
        """API 실패 시 빈 DataFrame 반환 (예외 전파 없음)."""
        mock_broker = mocker.MagicMock()
        mock_broker.fetch_ohlcv.side_effect = RuntimeError("KIS API 오류")

        mocker.patch(
            "quant_alpha.l1_ingestion.market_price.fetcher.Intraday4HFetcher"
            "._init_broker",
            return_value=mock_broker,
        )
        from quant_alpha.l1_ingestion.market_price.fetcher import Intraday4HFetcher

        fetcher = Intraday4HFetcher(start_date=START, end_date=END)
        df = fetcher.fetch(["005930"])
        assert df.empty
