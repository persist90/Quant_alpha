"""SQLAlchemy 엔진 및 세션 팩토리, 벌크 Upsert 유틸."""

from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from quant_alpha.common.config import settings
from quant_alpha.common.logger import get_logger

log = get_logger(__name__)

_engine: Engine | None = None


def get_engine() -> Engine:
    """싱글턴 SQLAlchemy 엔진 반환."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.db_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            echo=False,
        )
        log.info("db_engine_created", url=settings.db_url.split("@")[-1])
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """세션 팩토리 반환."""
    return sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """컨텍스트 매니저 기반 DB 세션."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def create_tables() -> None:
    """ORM 모델 기반 테이블 생성 및 TimescaleDB Hypertable 전환."""
    from quant_alpha.common.models.market_data import Base

    engine = get_engine()
    Base.metadata.create_all(engine)
    log.info("tables_created")
    _create_hypertables(engine)


def _create_hypertables(engine: Engine) -> None:
    """TimescaleDB Hypertable 생성 (이미 존재하면 무시)."""
    statements: list[dict[str, Any]] = [
        {
            "table": "daily_price",
            "sql": "SELECT create_hypertable('daily_price', 'date', if_not_exists => TRUE);",
        },
        {
            "table": "intraday_price_4h",
            "sql": "SELECT create_hypertable('intraday_price_4h', 'datetime', if_not_exists => TRUE);",
        },
    ]
    with engine.connect() as conn:
        for item in statements:
            try:
                conn.execute(text(item["sql"]))
                conn.commit()
                log.info("hypertable_created", table=item["table"])
            except Exception as e:
                log.warning("hypertable_skip", table=item["table"], reason=str(e))
