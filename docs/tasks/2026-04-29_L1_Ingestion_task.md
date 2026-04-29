# [L1 Ingestion] KOSDAQ 150 데이터 파이프라인 태스크 (Claude Code 전용)

이 태스크 문서는 `implementation_plan.md` 설계에 기반하여 Claude Code(`builder` 및 `validator` 에이전트)가 실행할 작업 목록입니다.

## 1. 공통 기반 모듈 (Common) 구현
- `[ ]` `pyproject.toml`에 의존성 추가 (`pykrx`, `mojito2`, `structlog`, `pydantic-settings` 등) 및 `poetry update`
- `[ ]` `src/quant_alpha/common/config.py` 작성 (DB 연결 및 한투 API 키 설정: `APP_KEY`, `APP_SECRET`, `CANO`, `ACNT_PRDT_CD`)
- `[ ]` `src/quant_alpha/common/logger.py` 작성 (structlog 포맷팅 설정)
- `[ ]` `src/quant_alpha/common/database.py` 작성 (SQLAlchemy Engine, SessionMaker 및 벌크 인서트 유틸)
- `[ ]` `src/quant_alpha/common/models/market_data.py` 작성 (`daily_price`, `intraday_price_4h` SQLAlchemy 모델)
- `[ ]` 데이터베이스 마이그레이션 적용 (테이블 생성 및 TimescaleDB `create_hypertable` 쿼리 실행)

## 2. 데이터 수집 로직 (Fetcher) 구현
- `[ ]` `src/quant_alpha/l1_ingestion/market_price/fetcher.py` 생성
- `[ ]` `DailyPriceFetcher` 구현: `pykrx`로 코스닥 150 종목 추출 및 일봉 OHLCV 수집
- `[ ]` `Intraday4HFetcher` 구현: `mojito2` (한국투자증권 API)로 4시간 봉 수집 (데이터 빈도 변환 로직 포함 필요 시 구현)
- `[ ]` `tenacity` retry 로직 및 KST Timezone 준수 확인

## 3. 데이터 적재 로직 (Loader) 구현
- `[ ]` `src/quant_alpha/l1_ingestion/market_price/loader.py` 생성
- `[ ]` PostgreSQL의 `INSERT ON CONFLICT DO UPDATE` (Upsert) 로직을 활용한 데이터 벌크 인서트 구현

## 4. 파이프라인 오케스트레이션 (Prefect Flow)
- `[ ]` `src/quant_alpha/l1_ingestion/market_price/pipeline.py` 생성
- `[ ]` `@task` 데코레이터를 fetcher, loader 함수에 적용
- `[ ]` `@flow` 로 전체 실행 흐름 정의 (종목 조회 -> 일봉 수집 -> 4시간봉 수집 -> DB 저장)

## 5. 검증 (Validator 에이전트 인계)
- `[ ]` `tests/l1_ingestion/test_fetcher.py` 작성 (API Mocking 활용)
- `[ ]` `tests/l1_ingestion/test_loader.py` 작성 (임시 DB 활용 Upsert 검증)
- `[ ]` 전체 테스트 커버리지 80% 이상 확인 및 `pytest` 통과 확인
