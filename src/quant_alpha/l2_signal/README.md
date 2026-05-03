# L2 Signal Module

이 모듈은 적재된 원시 데이터를 바탕으로 투자 전략에 쓰일 피처(Factor)와 시그널을 연산합니다.

### 1. What does this module configure/own?
- 가격 기반 지표 (Moving Averages, RSI, MACD 등) 연산.
- 펀더멘털 기반 지표 (PER, PBR, 분기 실적 yoy 등) 연산.
- 크로스섹셔널 및 시계열 팩터 생성.

### 2. What are common modification patterns?
- 새로운 팩터 로직 추가.
- 이상치(Outlier) 제거 방법론 변경 (Winsorization 등).

### 3. What non-obvious patterns cause failures?
- 팩터 계산 시 `shift(1)`을 누락하여 **Look-Ahead Bias(미래 참조 오류)** 발생.
- `inf`나 `-inf` 값이 발생했는데 `NaN`으로 변환하지 않아 후속 최적화 모듈(cvxpy)에서 크래시 발생.

### 4. What are the cross-module dependencies?
- `l1_ingestion`에서 최신 데이터가 적재되어야만 연산이 가능.
- 생성된 시그널은 `l3_strategy` 모듈의 입력값으로 사용됨.

### 5. What tribal knowledge is hidden?
- 시가총액이나 거래대금 필터링은 팩터 계산 '이전'이 아니라 '이후'에 적용하여, 팩터 스코어 분포(z-score 등)가 유니버스 전체를 반영하도록 해야 합니다.
