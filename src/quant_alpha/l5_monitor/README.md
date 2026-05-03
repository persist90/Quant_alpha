# L5 Monitor Module

이 모듈은 트레이딩 시스템의 실시간 상태, 주문 체결 내역, 포트폴리오 성과를 모니터링합니다.

### 1. What does this module configure/own?
- 실시간 이벤트 스트리밍 구독 (Redis Streams).
- 성능 메트릭 계산 (Daily PnL, Drawdown 등).
- Grafana 대시보드와 연동할 메트릭 노출 포맷팅.

### 2. What are common modification patterns?
- 새로운 모니터링 지표(예: 전략별 노출도, 회전율) 추가.
- 경고(Alert) 임계치 조정.

### 3. What non-obvious patterns cause failures?
- Redis 메모리 누수 (스트림 데이터가 정리되지 않고 쌓임).
- PnL 계산 시 배당금이나 액면분할 처리를 누락하여 수익률 왜곡.

### 4. What are the cross-module dependencies?
- `l1_ingestion`, `l4_execution` 등에서 발생하는 상태 이벤트를 수신합니다.
- 외부 의존성: `Redis`, `Grafana`.

### 5. What tribal knowledge is hidden?
- 슬랙(Slack) 알림은 정보성 알림과 에러(Critical) 알림의 채널을 분리해야 하며, 알림 폭탄(Alert Fatigue)을 방지하기 위해 쓰로틀링(Throttling)을 적용해야 합니다.
