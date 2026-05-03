# L3 Strategy Module

이 모듈은 L2에서 생성된 시그널을 바탕으로 최적의 포트폴리오 비중(Weights)을 산출합니다.

### 1. What does this module configure/own?
- 포트폴리오 최적화 목적 함수 (Mean-Variance, Risk Parity 등).
- 제약 조건 (섹터 중립, 최대 비중 제한, 턴오버 제한).
- 최종 Target Weights 산출.

### 2. What are common modification patterns?
- 새로운 최적화 제약 조건(예: 특정 종목 편입 금지) 추가.
- 시장 상황에 따른 목표 변동성(Target Volatility) 조정.

### 3. What non-obvious patterns cause failures?
- 제약 조건이 너무 빡빡하여 최적해를 찾지 못하는(Infeasible) 경우 발생.
- 입력된 covariance matrix가 positive semi-definite 상태가 아니어서 솔버가 실패.

### 4. What are the cross-module dependencies?
- `l2_signal`로부터 팩터 스코어와 리스크 모델 입력을 받습니다.
- 산출된 비중은 `l4_execution`에서 실제 주문 수량으로 변환됩니다.

### 5. What tribal knowledge is hidden?
- 최적화기(Optimizer)는 기본적으로 `cvxpy`를 사용하며, 솔버는 `ECOS` 또는 `SCS`를 우선적으로 사용합니다. 솔버 실패 시 fallback 로직을 반드시 포함해야 합니다.
