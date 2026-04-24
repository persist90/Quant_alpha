# Point-in-Time 규칙 (퀀트 핵심)

## 원칙
t일에는 t-1일까지 실제로 접근 가능했던 데이터만 사용.

## 데이터별 적용 시점

| 데이터 유형 | 사용 가능 시점 |
|------------|-------------|
| 일봉 OHLCV | 당일 장 마감 후 (15:40) |
| 재무제표 | 실제 공시일 +1일부터 |
| 공시 | 공시 시간 +15분 후 |
| 뉴스 | 발행 시간 +5분 후 |

## 코드 레벨 방어

```python
def _assert_point_in_time(df: pd.DataFrame, target_date: pd.Timestamp) -> None:
    max_date = df.index.max()
    if max_date >= target_date:
        raise ValueError(
            f"Point-in-Time 위반: {max_date} >= {target_date}"
        )
```

## 테스트 필수 패턴
모든 팩터 함수 테스트에 미래 데이터 유입 시 ValueError 발생 검증 포함.

```python
def test_no_lookahead_bias():
    future_data = make_df_with_future_date(target_date)
    with pytest.raises(ValueError, match="Point-in-Time 위반"):
        calc_factor(future_data, target_date)
```

## 자주 발생하는 실수

- `.shift(0)` 누락: 당일 가격으로 당일 시그널 계산 → `.shift(1)` 적용
- 재무제표 공시일 무시: 분기 종료일 기준 적용 → 실제 공시일 +1 기준 적용
- 미래 수익률 사용: 팩터 정규화에 전체 기간 통계 사용 → 누적 통계만 사용
