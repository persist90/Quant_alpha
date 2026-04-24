# 팩터 분류 체계 (Factor Taxonomy)

## 카테고리별 팩터 목록

### Value
| 팩터 | 계산식 | 파일 |
|------|--------|------|
| PER | 시가총액 / 순이익 | value.py |
| PBR | 시가총액 / 자본총계 | value.py |
| PSR | 시가총액 / 매출액 | value.py |
| EV_EBITDA | 기업가치 / EBITDA | value.py |
| FCF_Yield | FCF / 시가총액 | value.py |
| Earnings_Yield | 순이익 / 시가총액 | value.py |

### Momentum
| 팩터 | 계산식 | 파일 |
|------|--------|------|
| Mom_12_1 | 12개월 수익률 - 1개월 수익률 | momentum.py |
| High52W | 현재가 / 52주 최고가 | momentum.py |
| SUE | (실제EPS - 예상EPS) / std | momentum.py |

### Quality
| 팩터 | 계산식 | 파일 |
|------|--------|------|
| ROE | 순이익 / 자본총계 | quality.py |
| ROIC | NOPAT / 투하자본 | quality.py |
| GrossMarginStability | 매출총이익률 변동성 역수 | quality.py |
| Accruals | (순이익 - 영업현금흐름) / 총자산 | quality.py |

### Volatility
| 팩터 | 계산식 | 파일 |
|------|--------|------|
| RealizedVol60D | 60일 일간수익률 표준편차 | volatility.py |
| DownsideBeta | 하방 베타 | volatility.py |
| IdiosyncraticVol | 잔차 변동성 (CAPM 기준) | volatility.py |

### Growth
| 팩터 | 계산식 | 파일 |
|------|--------|------|
| SalesGrowthYoY | 매출액 YoY 성장률 | growth.py |
| SalesGrowthQoQ | 매출액 QoQ 성장률 | growth.py |
| EPSGrowth | EPS YoY 성장률 | growth.py |

### Flow
| 팩터 | 계산식 | 파일 |
|------|--------|------|
| ForeignNetBuy | 외국인 순매수 / 시가총액 | flow.py |
| InstNetBuy | 기관 순매수 / 시가총액 | flow.py |
| ShortSellChange | 대차잔고 변화율 | flow.py |

## 함수 표준 시그니처
```python
def calc_[factor_name](
    df_price: pd.DataFrame,
    df_fundamental: pd.DataFrame,
    date: pd.Timestamp,
) -> pd.Series:
    """[팩터명] 계산.

    Args:
        df_price: DatetimeIndex, 종목별 가격 데이터
        df_fundamental: DatetimeIndex, 종목별 재무 데이터
        date: 팩터 계산 기준일 (이 날짜 이전 데이터만 사용)

    Returns:
        cross-sectional z-score (index=ticker)
    """
```

## 전처리 규칙
1. Winsorization: 2.5 / 97.5 percentile
2. NaN 대체: cross-sectional 중앙값
3. 극단값 제거: MAD 3 이상
4. 상/하한가 종목 필터링
5. 최종 z-score 표준화

## @factor_registry 사용
```python
from src.signals.registry import factor_registry

@factor_registry(category="value", include=True)
def calc_per(df_price, df_fundamental, date):
    ...
```
