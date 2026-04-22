#!/bin/bash
# TimescaleDB 초기화 스크립트
set -e

echo "==> TimescaleDB 초기화 시작..."

PGPASSWORD=quant1234 psql -h localhost -p 5432 -U quant -d quant_db <<-EOSQL
    -- TimescaleDB 확장 활성화
    CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

    -- OHLCV 가격 데이터 테이블
    CREATE TABLE IF NOT EXISTS ohlcv (
        time        TIMESTAMPTZ NOT NULL,
        symbol      TEXT        NOT NULL,
        open        DOUBLE PRECISION,
        high        DOUBLE PRECISION,
        low         DOUBLE PRECISION,
        close       DOUBLE PRECISION,
        volume      DOUBLE PRECISION,
        PRIMARY KEY (time, symbol)
    );
    SELECT create_hypertable('ohlcv', 'time', if_not_exists => TRUE);

    -- 팩터/시그널 테이블
    CREATE TABLE IF NOT EXISTS signals (
        time        TIMESTAMPTZ NOT NULL,
        symbol      TEXT        NOT NULL,
        factor_name TEXT        NOT NULL,
        value       DOUBLE PRECISION,
        PRIMARY KEY (time, symbol, factor_name)
    );
    SELECT create_hypertable('signals', 'time', if_not_exists => TRUE);

    -- 포트폴리오 포지션 테이블
    CREATE TABLE IF NOT EXISTS positions (
        time        TIMESTAMPTZ NOT NULL,
        symbol      TEXT        NOT NULL,
        quantity    DOUBLE PRECISION,
        avg_price   DOUBLE PRECISION,
        pnl         DOUBLE PRECISION,
        PRIMARY KEY (time, symbol)
    );
    SELECT create_hypertable('positions', 'time', if_not_exists => TRUE);

    -- 압축 정책 (7일 이상 데이터 압축)
    SELECT add_compression_policy('ohlcv', INTERVAL '7 days', if_not_exists => TRUE);
    SELECT add_compression_policy('signals', INTERVAL '7 days', if_not_exists => TRUE);

    -- 보존 정책 (2년 보관)
    SELECT add_retention_policy('ohlcv', INTERVAL '2 years', if_not_exists => TRUE);

    \echo 'TimescaleDB 초기화 완료!'
EOSQL

echo "==> 완료! 생성된 테이블:"
PGPASSWORD=quant1234 psql -h localhost -p 5432 -U quant -d quant_db -c "\dt"
