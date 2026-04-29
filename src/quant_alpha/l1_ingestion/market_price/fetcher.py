"""L1 시장 데이터 수집기: pykrx(일봉) + 한투 API mojito2(4시간봉)."""

from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from quant_alpha.common.config import settings
from quant_alpha.common.logger import get_logger

KST = ZoneInfo("Asia/Seoul")
KOSDAQ_150_INDEX_CODE = "2150"

log = get_logger(__name__)


def _now_kst() -> datetime:
    return datetime.now(tz=KST)


class DailyPriceFetcher:
    """pykrx를 활용한 KOSDAQ 150 일봉 OHLCV 수집기."""

    def __init__(self, start_date: str, end_date: str) -> None:
        """
        Args:
            start_date: 수집 시작일 (YYYYMMDD)
            end_date: 수집 종료일 (YYYYMMDD)
        """
        self.start_date = start_date
        self.end_date = end_date

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _get_kosdaq150_tickers(self) -> list[str]:
        """코스닥 150 구성 종목 티커 리스트 반환."""
        from pykrx import stock

        # end_date를 명시하여 pykrx 내부 get_nearest_business_day_in_a_week() 호출 방지
        tickers = stock.get_index_portfolio_deposit_file(KOSDAQ_150_INDEX_CODE, self.end_date)
        log.info("kosdaq150_tickers_fetched", count=len(tickers))
        return list(tickers)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_single(self, ticker: str) -> pd.DataFrame:
        """단일 종목 일봉 데이터 수집 후 표준화된 DataFrame 반환."""
        from pykrx import stock

        df = stock.get_market_ohlcv_by_date(self.start_date, self.end_date, ticker)
        if df.empty:
            return pd.DataFrame()

        df = df.rename(columns={
            "시가": "open", "고가": "high", "저가": "low",
            "종가": "close", "거래량": "volume", "거래대금": "trading_value",
            "상장주식수": "shares_outstanding",
        })
        df.index = pd.to_datetime(df.index).tz_localize(KST)
        df["ticker"] = ticker
        df["last_updated"] = _now_kst()
        return df[["ticker", "open", "high", "low", "close",
                   "volume", "trading_value", "shares_outstanding", "last_updated"]]

    def fetch(self) -> pd.DataFrame:
        """KOSDAQ 150 전 종목 일봉 수집 후 통합 DataFrame 반환."""
        tickers = self._get_kosdaq150_tickers()
        frames: list[pd.DataFrame] = []
        for ticker in tickers:
            try:
                df = self._fetch_single(ticker)
                if not df.empty:
                    frames.append(df)
            except Exception as e:
                log.error("daily_fetch_failed", ticker=ticker, error=str(e))

        if not frames:
            return pd.DataFrame()

        result = pd.concat(frames)
        result.index.name = "date"
        log.info("daily_price_fetched", tickers=len(frames),
                 rows=len(result), start=self.start_date, end=self.end_date)
        return result


class Intraday4HFetcher:
    """한투 API(mojito2)를 활용한 4시간봉 수집기. 1H 봉 수집 후 4H로 리샘플."""

    def __init__(self, start_date: str, end_date: str) -> None:
        """
        Args:
            start_date: 수집 시작일 (YYYYMMDD)
            end_date: 수집 종료일 (YYYYMMDD)
        """
        self.start_date = start_date
        self.end_date = end_date
        self._broker = self._init_broker()

    def _init_broker(self) -> object | None:
        """mojito2 KoreaInvestment 브로커 초기화. KIS 키 미설정 시 None 반환."""
        if not settings.kis_app_key or not settings.kis_app_secret:
            log.warning("kis_credentials_missing", reason="KIS API 키가 설정되지 않아 4H봉 수집을 건너뜁니다.")
            return None

        import mojito

        acc_no = f"{settings.kis_account_no}-{settings.kis_acnt_prdt_cd}"
        return mojito.KoreaInvestment(
            api_key=settings.kis_app_key,
            api_secret=settings.kis_app_secret,
            acc_no=acc_no,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=3, max=15))
    def _fetch_1h(self, ticker: str) -> pd.DataFrame:
        """단일 종목 1시간봉 수집."""
        df = self._broker.fetch_ohlcv(  # type: ignore[union-attr]
            symbol=ticker,
            timeframe="60",
            start_date=self.start_date,
            end_date=self.end_date,
        )
        if df is None or (isinstance(df, pd.DataFrame) and df.empty):
            return pd.DataFrame()

        df = df.rename(columns={
            "open": "open", "high": "high", "low": "low",
            "close": "close", "volume": "volume",
        })
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        if df.index.tz is None:
            df.index = df.index.tz_localize(KST)
        return df[["open", "high", "low", "close", "volume"]]

    def _resample_to_4h(self, df_1h: pd.DataFrame) -> pd.DataFrame:
        """1H 봉 → 4H 봉 리샘플 (한국 장 09:00 기준 오프셋 적용)."""
        df_4h = (
            df_1h.resample("4h", offset="9h", closed="left", label="left")
            .agg({"open": "first", "high": "max", "low": "min",
                  "close": "last", "volume": "sum"})
            .dropna(subset=["open"])
        )
        return df_4h

    def fetch(self, tickers: list[str]) -> pd.DataFrame:
        """지정 종목 리스트에 대해 4H봉 수집 후 통합 DataFrame 반환."""
        if not tickers or self._broker is None:
            log.warning("intraday_skipped", tickers=len(tickers), broker_ready=self._broker is not None)
            return pd.DataFrame()

        fetched_at = datetime.now(tz=KST)
        frames: list[pd.DataFrame] = []

        for ticker in tickers:
            try:
                df_1h = self._fetch_1h(ticker)
                if df_1h.empty:
                    continue
                df_4h = self._resample_to_4h(df_1h)
                df_4h["ticker"] = ticker
                df_4h["fetched_at"] = fetched_at
                frames.append(df_4h)
            except Exception as e:
                log.error("intraday_fetch_failed", ticker=ticker, error=str(e))

        if not frames:
            return pd.DataFrame()

        result = pd.concat(frames)
        result.index.name = "datetime"
        log.info("intraday_4h_fetched", tickers=len(frames),
                 rows=len(result), start=self.start_date, end=self.end_date)
        return result
