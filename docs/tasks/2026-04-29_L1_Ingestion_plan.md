# [L1 Ingestion] KOSDAQ 150 시장 데이터(OHLCV) 수집 파이프라인 구축

본 설계서는 `quant-alpha` 프로젝트의 첫 번째 데이터 수집 파이프라인인 **코스닥 150(KOSDAQ 150) 종목의 일봉(Daily) 및 4시간 봉(4H) 데이터 수집기**를 구축하기 위한 기술 문서입니다. Claude Code (`builder` 에이전트)가 이 문서를 읽고 즉시 구현을 시작할 수 있도록 작성되었습니다.

> [!NOTE]
> 본 파이프라인은 현재 `docker-compose.yml`에 구성된 **TimescaleDB**를 주 저장소로 사용하며, **Prefect**를 통해 스케줄링 및 모니터링됩니다.

## Architecture Decisions (확정 사항)

> [!NOTE]
> 설계 검토 과정에서 확정된 핵심 의사결정 사항입니다.

1. **데이터 소스 분리 전략 (Hybrid)**
   - **일별(Daily) 종가 및 시총 데이터**: `pykrx` 사용 (KOSDAQ 150 구성 종목 추출 및 기본 일봉 데이터 수집)
   - **장중 4시간 봉(Intraday 4H)**: `한국투자증권 Open API` 사용
   
2. **한국투자증권 API 및 OS 호환성 (Mac/Windows)**
   - 과거 증권사 API(COM 객체 기반)와 달리, 현재 한국투자증권 Open API는 **RESTful JSON API** 형식을 제공합니다.
   - 따라서 운영체제(Mac, Linux, Windows)에 전혀 구애받지 않으며, Mac 환경에서 파이썬의 `requests` 라이브러리(혹은 `mojito2` 래퍼)를 사용해 완벽하게 개발 및 실행이 가능합니다.

## Proposed Changes

### 1. Common Layer (공통 기반 모듈)
데이터베이스 연결과 환경 설정, 로깅을 담당하는 기반 모듈을 구축합니다.

#### [NEW] [src/quant_alpha/common/config.py](file:///Users/keonyoungsong/projects/quant-alpha/src/quant_alpha/common/config.py)
- `pydantic-settings`를 활용하여 `.env` 파일의 환경변수를 로드하는 `Settings` 클래스 구현.
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST` 등 TimescaleDB 연결 정보 관리.

#### [NEW] [src/quant_alpha/common/logger.py](file:///Users/keonyoungsong/projects/quant-alpha/src/quant_alpha/common/logger.py)
- `structlog`를 활용한 JSON 포맷 로거 설정 모듈.

#### [NEW] [src/quant_alpha/common/database.py](file:///Users/keonyoungsong/projects/quant-alpha/src/quant_alpha/common/database.py)
- SQLAlchemy `create_engine` 및 session maker 설정.
- 데이터 대량 삽입(Bulk Insert)에 최적화된 유틸리티 함수 포함.

### 2. Database Schema (테이블 정의)

#### [NEW] [src/quant_alpha/common/models/market_data.py](file:///Users/keonyoungsong/projects/quant-alpha/src/quant_alpha/common/models/market_data.py)
- SQLAlchemy ORM을 사용하여 일봉(`daily_price`) 및 4시간봉(`intraday_price_4h`) 테이블 정의.
  ```python
  # daily_price 스키마 예시
  # date (Date, PK)
  # ticker (String, PK)
  # open, high, low, close (Float)
  # volume, trading_value, shares_outstanding (BigInteger)
  
  # intraday_price_4h 스키마 예시
  # datetime (DateTime(timezone=True), PK)
  # ticker (String, PK)
  # open, high, low, close (Float)
  # volume (BigInteger)
  ```
- **TimescaleDB Hypertable 변환**: 테이블 생성 직후 두 테이블에 대해 각각 `create_hypertable`을 실행하는 마이그레이션 로직 추가. (`daily_price`는 `date`, `intraday_price_4h`는 `datetime` 기준)

### 3. L1 Ingestion Layer (수집 파이프라인)

#### [NEW] [src/quant_alpha/l1_ingestion/market_price/fetcher.py](file:///Users/keonyoungsong/projects/quant-alpha/src/quant_alpha/l1_ingestion/market_price/fetcher.py)
- `pykrx`를 활용하여 KOSDAQ 150 구성 종목을 추출하고 일봉(Daily) 데이터를 수집하는 `DailyPriceFetcher` 클래스 구현.
- 한국투자증권 Open API를 호출하여 4시간 봉 데이터를 수집하는 `Intraday4HFetcher` 클래스 구현 (mojito2 라이브러리 활용 권장).
- 외부 API Rate Limit을 고려하여 `tenacity`의 `@retry` 데코레이터를 적용 (재시도 3회, 백오프 적용).
- DataFrame 반환 시 스키마 표준화 (컬럼명 snake_case 통일, DatetimeIndex, 시간대는 Asia/Seoul).

#### [NEW] [src/quant_alpha/l1_ingestion/market_price/loader.py](file:///Users/keonyoungsong/projects/quant-alpha/src/quant_alpha/l1_ingestion/market_price/loader.py)
- 수집된 DataFrame을 TimescaleDB `daily_price` 테이블에 Upsert (ON CONFLICT DO UPDATE) 하는 로직 구현.
- PostgreSQL의 `INSERT ... ON CONFLICT` 문법 활용.

#### [NEW] [src/quant_alpha/l1_ingestion/market_price/pipeline.py](file:///Users/keonyoungsong/projects/quant-alpha/src/quant_alpha/l1_ingestion/market_price/pipeline.py)
- Prefect `@flow`와 `@task` 데코레이터를 사용하여 수집 → 저장의 전체 오케스트레이션 구성.
- 매일 장 마감 후 (오후 15:40 이후) 실행될 수 있는 구조로 작성.

### 4. Dependencies 수정

#### [MODIFY] [pyproject.toml](file:///Users/keonyoungsong/projects/quant-alpha/pyproject.toml)
- `pykrx` 패키지 추가 (일봉/KOSDAQ 종목 추출용).
- `mojito2` 패키지 추가 (한국투자증권 Open API 래퍼, 4시간봉 수집용).
- `psycopg2-binary` (기존 존재 확인)
- `SQLAlchemy` (기존 존재 확인)

## Verification Plan

### Automated Tests (validator 에이전트 용)
1. **Mocking Test**: 외부 API 호출(`fetcher.py`)을 Mocking하여 데이터 표준화(snake_case 변환 등)가 정상 작동하는지 확인.
2. **DB Insert Test**: 임시 SQLite 또는 Local DB에 ORM을 통한 Upsert 로직이 정상 작동하는지 확인.
3. **Data Integrity Test**: 수집된 데이터에 NaN 값이 있는지 검증하는 로직 테스트.

### Manual Verification
1. 클로드 코드를 통해 코드가 작성된 후, 사용자가 직접 `python -m src.quant_alpha.l1_ingestion.market_price.pipeline` 등을 실행.
2. `docker exec -it quant_timescaledb psql -U quant -d quant_db`에 접속하여 데이터가 정상 적재되었는지 SELECT 쿼리로 확인.
3. Grafana (localhost:3000)를 연결하여 적재된 주가 데이터 시계열 차트 시각화 테스트.
