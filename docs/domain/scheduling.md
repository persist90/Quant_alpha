# 워크플로우 스케줄링 가이드

## 표준 Flow 스케줄 (KST 기준)

| Flow | 스케줄 | 의존성 | 예상 소요 |
|------|--------|--------|---------|
| morning_pipeline | 평일 08:00 | — | ~20분 |
| pre_market_orders | 평일 09:00 | morning_pipeline | ~5분 |
| intraday_monitor | 평일 09:00~15:30, 15분 간격 | — | ~1분 |
| post_market | 평일 15:40 | — | ~10분 |
| nightly_maintenance | 매일 23:00 | — | ~30분 |
| weekly_review | 금요일 18:00 | — | ~1시간 |

## Flow 의존성 그래프
```
morning_pipeline (08:00)
    └─► pre_market_orders (09:00)
            └─► [주문 실행 - L4 사용자 코드]

intraday_monitor (09:00~15:30, 15분)  ← 독립 실행

post_market (15:40)  ← 독립 실행
nightly_maintenance (23:00)  ← 독립 실행
weekly_review (금 18:00)  ← 독립 실행
```

## @task 설계 표준
```python
from prefect import task, flow

@task(
    retries=3,
    retry_delay_seconds=60,
    timeout_seconds=300,
    tags=["layer:L1"],
)
def fetch_krx_daily(date: str) -> pd.DataFrame:
    ...

@flow(name="morning_pipeline")
def morning_pipeline_flow(date: str | None = None) -> None:
    ...
```

## 알림 라우팅 규칙

| 레벨 | 조건 | 채널 |
|------|------|------|
| Info | 정상 완료 | Slack #quant-daily |
| Warning | 재시도 1~2회 | Slack #quant-daily |
| Error | 재시도 소진, Task 실패 | Slack #quant-alert |
| Critical | Level 3 리스크, Flow 전체 실패 | Slack #quant-alert + Telegram |

## 실패 처리 패턴
```python
from prefect.states import Failed

@flow
def morning_pipeline_flow():
    try:
        result = fetch_data.submit()
        signals = calc_signals.submit(wait_for=[result])
    except Exception as e:
        notify_slack.submit(level="error", message=str(e))
        return Failed(message=str(e))
```

## 배포
```bash
# Prefect Cloud 배포
prefect deploy --all

# 로컬 워커 실행
prefect worker start --pool quant-alpha-pool --type process
```

## prefect.yaml 위치
```
deploy/prefect/prefect.yaml
```

## 타임존 주의사항
- 모든 스케줄: Asia/Seoul (KST) 기준
- Prefect Cloud 대시보드: UTC 표시 → +9시간 차이 확인 필요
- cron 표현식 예: `"0 8 * * 1-5"` = 평일 08:00 KST
