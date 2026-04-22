# Quant-Alpha Project Convention

## Architecture
- 5-Layer: L1(Ingestion) > L2(Signal) > L3(Strategy) > L4(Execution) > L5(Monitor)
- 각 레이어는 독립 배포/테스트 가능
- 레이어 간 통신: Redis Streams (비동기), 직접 함수 호출 (동기)
- 오케스트레이션: Prefect (@flow, @task)

## Coding Standards & Quant Rules
- Python 3.11+, Type hints 필수 (mypy strict)
- DataFrame: 항상 DatetimeIndex, column은 snake_case
- **[CRITICAL] Timezone:** 모든 시간 데이터는 'Asia/Seoul' (KST) 기준.
- **[CRITICAL] Look-Ahead Bias:** 시그널 연산 시 미래 정보 유입을 막기 위해 철저한 Lagging 및 `.shift()` 적용.
- 최대 함수 길이: 50줄, 초과 시 분리.

## Safety Rules (CRITICAL)
- 실제 자금 관련 함수: @requires_confirmation 데코레이터
- L4 모든 주문 함수: `dry_run=True` 기본값
- TRADING_MODE=live 아니면 실주문 절대 불가
- 모든 주문 전 `harness.pre_order_check()` 통과 필수

## Testing & Backtest
- 최소 80% coverage, 팩터는 IC validation 테스트 포함
- **[CRITICAL] Friction:** 백테스트 로직에 수수료(15bp)와 슬리피지 기본값 필수 포함.

## Dependencies
- pandas, numpy, scipy, scikit-learn, cvxpy, anthropic, structlog, redis, psycopg2-binary, sqlalchemy, prefect, tenacity, pydantic-settings, duckdb
