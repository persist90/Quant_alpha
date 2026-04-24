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

## Subagent Governance (v3)

### 4-Agent Architecture
- **builder**: 신규 코드 작성 (데이터/팩터/최적화 모두)
- **validator**: 테스트, IC 검증, 백테스트
- **reviewer**: 읽기 전용 코드 리뷰
- **orchestrator**: Prefect 워크플로우 구성

### 병렬 실행 제한
- 동시 실행 최대: **3개**
- 일반 패턴: builder + validator + reviewer 병렬
- orchestrator: 단독 실행
- 실제 사고 사례: 49개 병렬 $8,000~15,000 청구, 23개 무인 3일 $47,000 청구

### 자동 실행 금지
- 무인(headless) 연속 실행 절대 금지
- 커스텀 명령어(/add-factor 등)도 사용자 확인 후 실행

### 권한 매트릭스

| 에이전트 | Read | Write | Edit | Bash | 특이사항 |
|---------|------|-------|------|------|---------|
| builder | ✓ | ✓ | ✓ | ✗ | 실행 불가 |
| validator | ✓ | ✓* | ✓* | ✓ | tests/, backtests/만 쓰기 |
| reviewer | ✓ | ✗ | ✗ | ✗ | 완전 읽기 전용 |
| orchestrator | ✓ | ✓ | ✓ | ✓ | deploy/, src/monitoring/ |

### 레이어 분리 원칙
- 운영 레이어(Prefect Flow 실행)는 서브에이전트 개입 금지
- 서브에이전트는 개발 레이어(코드 생성/리뷰/테스트)에서만 활성화
- L4 주문 실행은 사용자 직접 작성 (reviewer가 최종 검증, 2회 이상)

### 도메인 지식 참조 규칙
- 모든 에이전트는 작업 전 docs/domain/ 관련 문서 참조 필수
- 도메인 지식을 에이전트 description에 담지 않음
- 문서 변경 시 모든 에이전트가 즉시 영향 받음

### 토큰 예산 모니터링
- Claude Pro 사용량 대시보드 주기적 확인
- 일일 사용량이 80% 넘으면 당일 서브에이전트 사용 중단
