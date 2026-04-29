"""TimescaleDB 시장 데이터 ORM 모델 (daily_price, intraday_price_4h)."""

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Float, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DailyPrice(Base):
    """일봉 OHLCV 테이블 (TimescaleDB Hypertable, partition key: date)."""

    __tablename__ = "daily_price"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    trading_value: Mapped[int] = mapped_column(BigInteger, nullable=True)
    shares_outstanding: Mapped[int] = mapped_column(BigInteger, nullable=True)
    last_updated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


class IntradayPrice4H(Base):
    """4시간봉 OHLCV 테이블 (TimescaleDB Hypertable, partition key: datetime)."""

    __tablename__ = "intraday_price_4h"

    datetime: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), primary_key=True
    )
    ticker: Mapped[str] = mapped_column(String(10), primary_key=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
