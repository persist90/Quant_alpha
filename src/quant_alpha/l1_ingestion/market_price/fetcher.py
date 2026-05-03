"""L1 시장 데이터 수집기: pykrx(일봉) + 한투 API mojito2(4시간봉)."""

import time
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
from tenacity import retry, stop_after_attempt, wait_exponential

from quant_alpha.common.config import settings
from quant_alpha.common.logger import get_logger

KST = ZoneInfo("Asia/Seoul")
KOSDAQ_150_INDEX_CODE = "2203"

log = get_logger(__name__)


def _now_kst() -> datetime:
    return datetime.now(tz=KST)


def _inject_krx_env() -> None:
    """pykrx는 os.environ에서 KRX_ID/KRX_PW를 직접 읽으므로 모듈 수준에서 주입."""
    import os
    if settings.krx_id:
        os.environ.setdefault("KRX_ID", settings.krx_id)
    if settings.krx_pw:
        os.environ.setdefault("KRX_PW", settings.krx_pw)


class DailyPriceFetcher:
    """pykrx를 활용한 KOSDAQ 150 일봉 OHLCV 수집기.

    날짜별로 코스닥 전종목을 1회 API 호출(get_market_ohlcv)로 가져온 뒤
    KOSDAQ 150 티커로 필터링. 종목별 개별 호출(150회) 대비 속도 150배 향상.
    """

    def __init__(self, start_date: str, end_date: str) -> None:
        self.start_date = start_date
        self.end_date = end_date

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _get_kosdaq150_tickers(self) -> list[str]:
        """코스닥 150 구성 종목 티커 리스트 반환 (1 API Call)."""
        from pykrx import stock

        tickers = stock.get_index_portfolio_deposit_file(KOSDAQ_150_INDEX_CODE, self.end_date)
        log.info("kosdaq150_tickers_fetched", count=len(tickers))
        return list(tickers)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _fetch_all_on_date(self, date_str: str, kosdaq150_tickers: list[str]) -> pd.DataFrame:
        """특정 일자 코스닥 전종목 일봉을 1 API Call로 수집 후 코스닥 150 필터링.

        get_market_ohlcv 반환 컬럼: 시가, 고가, 저가, 종가, 거래량, 거래대금, 등락률, 시가총액
        상장주식수는 해당 API에 없어 None으로 저장 (시가총액/종가로 근사 가능하나 부정확).
        """
        from pykrx import stock

        df = stock.get_market_ohlcv(date_str, market="KOSDAQ")
        if df.empty:
            return pd.DataFrame()

        df = df[df.index.isin(kosdaq150_tickers)].copy()
        if df.empty:
            return pd.DataFrame()

        df = df.rename(columns={
            "시가": "open", "고가": "high", "저가": "low",
            "종가": "close", "거래량": "volume", "거래대금": "trading_value",
        })
        df["shares_outstanding"] = None  # get_market_ohlcv에는 상장주식수 없음
        df["ticker"] = df.index.astype(str)
        ts = pd.Timestamp(date_str, tz=KST)
        df.index = pd.DatetimeIndex([ts] * len(df))
        df["last_updated"] = _now_kst()

        return df[["ticker", "open", "high", "low", "close",
                   "volume", "trading_value", "shares_outstanding", "last_updated"]]

    def fetch(self) -> pd.DataFrame:
        """KOSDAQ 150 일봉 수집 — 날짜별 1 API Call 후 코스닥 150 필터링."""
        _inject_krx_env()  # 모든 pykrx 호출 이전에 KRX 인증 환경변수 주입

        tickers = self._get_kosdaq150_tickers()
        if not tickers:
            log.warning("kosdaq150_tickers_empty")
            return pd.DataFrame()

        # bdate_range: 월~금 기준. 한국 공휴일은 pykrx가 빈 df 반환 → skip 처리됨
        dates = pd.bdate_range(self.start_date, self.end_date)
        frames: list[pd.DataFrame] = []

        for date in dates:
            date_str = date.strftime("%Y%m%d")
            try:
                df = self._fetch_all_on_date(date_str, tickers)
                if not df.empty:
                    frames.append(df)
            except Exception as e:
                log.error("daily_fetch_failed", date=date_str, error=str(e))
            time.sleep(0.2)  # pykrx KRX 세션 보호 — 연속 호출 시 세션 만료 방지

        if not frames:
            return pd.DataFrame()

        result = pd.concat(frames)
        result.index.name = "date"
        log.info("daily_price_fetched", dates=len(dates), rows=len(result),
                 start=self.start_date, end=self.end_date)
        return result


class HistoricalIntraday4HFetcher:
    """yfinance 기반 KOSDAQ 150 역사적 4H봉 수집기.

    Yahoo Finance 제약: 1H 데이터 최대 730일 지원.
    KOSDAQ 티커 형식: {6자리 코드}.KQ (예: 035720.KQ)
    1H 데이터 수신 후 4H로 리샘플. trading_value는 yfinance 미지원으로 미포함.
    """

    MAX_DAYS = 728  # yfinance 730일 한도에서 오늘 기준 경계 충돌 방지 (2일 여유)
    BATCH_SIZE = 20

    def __init__(self, start_date: str, end_date: str) -> None:
        self.start_date = start_date
        self.end_date = end_date

    def fetch(self, tickers: list[str]) -> pd.DataFrame:
        """KOSDAQ 150 역사적 4H봉 수집 (yfinance 730일 한도 내)."""
        try:
            import yfinance as yf
        except ImportError:
            log.error("yfinance_not_installed", hint="pip install yfinance")
            return pd.DataFrame()

        start_dt = pd.Timestamp(self.start_date, tz=KST)
        end_dt = pd.Timestamp(self.end_date, tz=KST)
        max_start = end_dt - pd.Timedelta(days=self.MAX_DAYS)

        if start_dt < max_start:
            log.warning(
                "yfinance_4h_limit",
                requested_start=self.start_date,
                actual_start=max_start.strftime("%Y%m%d"),
                reason="yfinance 1H 데이터 최대 730일 제한",
            )
            start_dt = max_start

        yf_start = start_dt.strftime("%Y-%m-%d")
        yf_end = (end_dt + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        yf_tickers = [f"{t}.KQ" for t in tickers]
        fetched_at = _now_kst()
        frames: list[pd.DataFrame] = []

        for i in range(0, len(yf_tickers), self.BATCH_SIZE):
            batch = yf_tickers[i : i + self.BATCH_SIZE]
            try:
                raw = yf.download(
                    batch,
                    start=yf_start,
                    end=yf_end,
                    interval="1h",
                    group_by="ticker",
                    auto_adjust=True,
                    progress=False,
                )
                if raw.empty:
                    continue

                for yf_ticker in batch:
                    ticker_code = yf_ticker.replace(".KQ", "")
                    try:
                        df_t = raw[yf_ticker].copy() if len(batch) > 1 else raw.copy()
                        df_t = df_t.dropna(subset=["Open"])
                        if df_t.empty:
                            continue

                        df_t = df_t.rename(columns={
                            "Open": "open", "High": "high", "Low": "low",
                            "Close": "close", "Volume": "volume",
                        })[["open", "high", "low", "close", "volume"]]

                        if df_t.index.tz is None:
                            df_t.index = df_t.index.tz_localize(KST)
                        else:
                            df_t.index = df_t.index.tz_convert(KST)

                        df_4h = (
                            df_t.resample("4h", offset="9h", closed="left", label="left")
                            .agg({"open": "first", "high": "max", "low": "min",
                                  "close": "last", "volume": "sum"})
                            .dropna(subset=["open"])
                        )
                        df_4h["ticker"] = ticker_code
                        df_4h["fetched_at"] = fetched_at
                        frames.append(df_4h)
                    except Exception as e:
                        log.error("hist_4h_ticker_failed", ticker=yf_ticker, error=str(e))
            except Exception as e:
                log.error("hist_4h_batch_failed", batch_size=len(batch), error=str(e))
            time.sleep(1.0)  # yfinance rate limit 보호

        if not frames:
            return pd.DataFrame()

        result = pd.concat(frames)
        result.index.name = "datetime"
        log.info("historical_4h_fetched", tickers=len(frames), rows=len(result))
        return result


class Intraday4HFetcher:
    """KIS API 분봉조회(당일)를 활용한 4시간봉 수집기.

    KIS 분봉조회 API 제약: 당일 데이터만 지원, 1회 30봉 반환 → 페이지네이션 필요.
    fetch_ohlcv(timeframe='60')는 mojito에 존재하지 않으므로 _fetch_today_1m_ohlcv 직접 호출.
    """

    def __init__(self, start_date: str, end_date: str) -> None:
        self.start_date = start_date
        self.end_date = end_date
        self._broker: object | None = None  # lazy init — fetch() 호출 시 초기화

    def _init_broker(self) -> object | None:
        """mojito KoreaInvestment 브로커 초기화. KIS 키 미설정 시 None 반환."""
        if not settings.kis_app_key or not settings.kis_app_secret:
            log.warning("kis_credentials_missing", reason="KIS API 키 미설정 — 4H봉 건너뜀")
            return None

        import mojito

        acc_no = f"{settings.kis_account_no}-{settings.kis_acnt_prdt_cd}"
        is_mock = settings.trading_mode == "paper"
        return mojito.KoreaInvestment(
            api_key=settings.kis_app_key,
            api_secret=settings.kis_app_secret,
            acc_no=acc_no,
            mock=is_mock,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=3, max=15))
    def _fetch_1m_today(self, ticker: str) -> pd.DataFrame:
        """KIS 분봉조회 API 페이지네이션으로 당일 1분봉 전체 수집.

        _fetch_today_1m_ohlcv의 to 파라미터는 'HH:MM:SS' 형식 필수 (공개 메서드 버그 우회).
        """
        from datetime import datetime as dt_cls, timedelta

        raw_bars: list[dict] = []
        to = "15:30:00"

        while True:
            resp = self._broker._fetch_today_1m_ohlcv(symbol=ticker, to=to)  # type: ignore[union-attr]
            bars = resp.get("output2") or []
            if not bars:
                break
            raw_bars.extend(bars)
            last_hour = bars[-1]["stck_cntg_hour"]
            if last_hour <= "090100":
                break
            prev = dt_cls.strptime(last_hour, "%H%M%S") - timedelta(minutes=1)
            to = prev.strftime("%H:%M:%S")

        if not raw_bars:
            return pd.DataFrame()

        df = pd.DataFrame(raw_bars)
        df.index = (
            pd.to_datetime(
                df["stck_bsop_date"] + df["stck_cntg_hour"], format="%Y%m%d%H%M%S"
            )
            .dt.tz_localize(KST)
        )
        df.index.name = "datetime"
        df = df.sort_index()
        df = df.rename(columns={
            "stck_oprc": "open", "stck_hgpr": "high",
            "stck_lwpr": "low", "stck_prpr": "close", "cntg_vol": "volume",
        })
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = pd.to_numeric(df[col])
        return df[["open", "high", "low", "close", "volume"]]

    def _resample_to_4h(self, df_1m: pd.DataFrame) -> pd.DataFrame:
        """1분봉 → 4H봉 리샘플 (한국 장 09:00 기준 오프셋 적용)."""
        return (
            df_1m.resample("4h", offset="9h", closed="left", label="left")
            .agg({"open": "first", "high": "max", "low": "min",
                  "close": "last", "volume": "sum"})
            .dropna(subset=["open"])
        )

    def fetch(self, tickers: list[str]) -> pd.DataFrame:
        """지정 종목 리스트에 대해 4H봉 수집 후 통합 DataFrame 반환."""
        if not tickers:
            log.warning("intraday_skipped_no_tickers")
            return pd.DataFrame()

        if self._broker is None:
            self._broker = self._init_broker()
        if self._broker is None:
            return pd.DataFrame()

        fetched_at = _now_kst()
        frames: list[pd.DataFrame] = []

        for ticker in tickers:
            try:
                df_1m = self._fetch_1m_today(ticker)
                if df_1m.empty:
                    continue
                df_4h = self._resample_to_4h(df_1m)
                df_4h["ticker"] = ticker
                df_4h["fetched_at"] = fetched_at
                frames.append(df_4h)
            except Exception as e:
                log.error("intraday_fetch_failed", ticker=ticker, error=str(e))
            finally:
                time.sleep(0.1)  # KIS API rate limit: 초당 10~20건 제한 준수

        if not frames:
            return pd.DataFrame()

        result = pd.concat(frames)
        result.index.name = "datetime"
        log.info("intraday_4h_fetched", tickers=len(frames),
                 rows=len(result), start=self.start_date, end=self.end_date)
        return result
