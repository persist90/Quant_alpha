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

## Subagent Governance (CRITICAL)

### 병렬 실행 제한
- 동시 실행 가능한 서브에이전트 최대: **4개**
- 이유: 5개 이상 동시 실행 시 토큰 소모가 급증하고 Claude Pro 사용량 한도를 20분 내 소진할 수 있음

### 자동 실행 금지
- 서브에이전트를 무인(headless)으로 연속 실행 절대 금지
- CI/CD나 수동 호출만 허용
- /add-factor 등 커스텀 명령어도 사용자 확인 후 실행

### 레이어 분리 원칙
- 운영 레이어(Prefect Flow, Python 실행 코드)는 서브에이전트 사용 금지
- 서브에이전트는 개발 레이어(코드 생성/리뷰/테스트)에서만 사용

### 토큰 예산 모니터링
- Claude Pro 사용량 대시보드를 주기적으로 확인
- 일일 사용량이 80%를 넘으면 당일 서브에이전트 사용 중단
- 주간 사용량 제한에 도달 시 다음 주까지 개발 중단

### 에이전트별 도구 권한 준수
- data-connector: Bash/WebFetch 허용 (실제 API 호출 검증)
- factor-calculator: Bash 금지 (실행은 test-writer)
- test-writer: Bash 허용 (pytest 실행)
- ic-validator: Bash 허용 (백테스트 실행)
- code-reviewer: Read/Grep/Glob만 (읽기 전용)
- prefect-worker: Bash 허용 (prefect 명령어)

> ⚠ 실제 비용 사고 사례: 49개 서브에이전트 2.5시간 병렬 실행 → $8,000~15,000 청구.
> 23개 서브에이전트 3일 무인 실행 → $47,000 청구. 상한 4개 규칙은 타협 불가.
