# L4 Execution Module

이 모듈은 L3에서 산출된 Target Weights를 실제 브로커 API 주문으로 변환하고 실행합니다.

### 1. What does this module configure/own?
- 현재 포트폴리오 잔고 확인.
- Target Weights와 현재 잔고를 비교하여 매수/매도 수량(Shares) 계산.
- 증권사(Broker) API 통신 및 실제 주문 전송.

### 2. What are common modification patterns?
- 거래 수수료 및 슬리피지 모델 업데이트.
- 체결 알고리즘(예: TWAP, VWAP) 수정.

### 3. What non-obvious patterns cause failures?
- 잔고 조회 시 체결 대기 중인 미체결 잔량을 고려하지 않으면 중복 주문이 발생할 수 있음.
- 시장가 주문 시 호가창 호가 공백으로 인한 극심한 슬리피지 발생.

### 4. What are the cross-module dependencies?
- `l3_strategy`의 Target Weights 입력을 받음.
- 주문 체결 내역은 `l5_monitor`의 Redis Streams로 발행됨.

### 5. What tribal knowledge is hidden?
- **CRITICAL: 모든 L4 주문 함수는 `dry_run=True`가 기본값이어야 합니다.**
- 환경 변수 `TRADING_MODE=live`가 명시되지 않은 이상 실제 주문은 절대 나가지 않도록 2중 안전 장치를 구현해야 합니다.
