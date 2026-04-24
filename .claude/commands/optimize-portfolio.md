---
description: 포트폴리오 최적화 로직을 구축하고 백테스트 검증
argument-hint: <최적화방식>
---

# 포트폴리오 최적화 구축 워크플로우

사용자가 /optimize-portfolio $ARGUMENTS로 호출.
예: /optimize-portfolio black-litterman

## 실행 단계

### Step 1: 최적화 방식 확인 (직접 수행)
지원되는 방식:
- black-litterman: Black-Litterman + NLP Overlay (기본)
- mean-variance: 고전적 Mean-Variance
- risk-parity: Risk Parity
- equal-weight: 동일 가중 (벤치마크용)

### Step 2: 최적화 엔진 구현 (strategy-optimizer)
"strategy-optimizer 에이전트를 사용해서 src/strategy/optimizer.py에
{최적화방식} 로직 구현. cvxpy 기반, 제약조건 5대(비중 상한 5%,
turnover 20%, 섹터 편향 10%, 단일 종목 상한, 현금 비중) 반영."

### Step 3: 리스크 관리 모듈 확인/구현 (strategy-optimizer)
"strategy-optimizer로 src/strategy/risk.py 확인. 없으면 VaR, HHI,
유동성 리스크, MDD 모니터링 구현."

### Step 4: 테스트 + 리뷰 (병렬 실행)
다음 두 에이전트를 병렬로 호출:
- test-writer: 제약조건 위반 케이스, 수렴 실패 케이스, 경계값 테스트
- code-reviewer: 수치 안정성, fallback 로직, NaN 처리 검증

### Step 5: 백테스트 (ic-validator)
"ic-validator 에이전트를 사용해서 {최적화방식}으로 5년 백테스트.
Sharpe, MDD, Calmar, Turnover 측정. HTML 리포트 생성."

### Step 6: 결과 보고
사용자에게 결과 요약 제시:
- Sharpe Ratio
- Maximum Drawdown
- Turnover (월간)
- 제약조건 준수율
- 벤치마크(KOSPI200) 대비 초과 수익
- 사용자에게 실전 적용 여부 판단 요청

## 지침
- Step 4는 병렬, 나머지는 순차
- Step 5는 10~15분 소요 가능
- L4 주문 실행 코드는 이 명령어에서 다루지 않음
