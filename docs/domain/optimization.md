# 포트폴리오 최적화 가이드

## 기본 프레임워크: Black-Litterman + NLP Overlay

### 목적함수
```
Maximize: μ_BL·w - (λ/2)·w·Σ·w + α·(NLP_Signal)·w

Subject to:
  Σw_i = 1
  0 ≤ w_i ≤ 0.05          (단일 종목 5% 상한)
  turnover ≤ 0.20          (월간 회전율)
  |sector_weight - bm| ≤ 0.10  (섹터 편향 ±10%)
```

### 파라미터
| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| λ (리스크 회피) | 2.5 | 수익-리스크 트레이드오프 |
| α (NLP 오버레이) | ±0.15 | NLP 시그널 반영 강도 |
| τ (BL prior 신뢰도) | 0.05 | 균형 포트폴리오 대비 신뢰 |

### 공분산 추정
- Ledoit-Wolf Shrinkage 적용 (scikit-learn `LedoitWolf`)
- 과거 250 거래일 수익률 데이터 사용
- 극단값 제거 후 추정

## 지원 방식

| 방식 | 사용 시점 | 특이사항 |
|------|----------|---------|
| black-litterman | 기본값 | NLP 시그널 통합 가능 |
| mean-variance | 벤치마크 비교용 | 단순하지만 불안정 |
| risk-parity | 리스크 균등 배분 | 분산 시장에서 유리 |
| equal-weight | 순수 벤치마크 | 성과 하한선 확인 |

## 리스크 관리 임계값

| 지표 | 경고 | 중단 |
|------|------|------|
| VaR 95% 1-day | 1.5% | 2.0% |
| HHI | 0.04 | 0.05 |
| Rolling MDD (60일) | 10% | 15% |
| 유동성 비율 | 8% | 10% |

## 리밸런싱 규칙
- **정기**: 매 거래일 08:30 목표 포트폴리오 산출
- **최소 임계치**: 왕복 거래비용 (30bp) 초과 시만 주문 생성
- **이벤트 드리븐**: NLP 고영향도 이벤트 감지 후 15분 쿨다운

## cvxpy 구현 패턴
```python
import cvxpy as cp

w = cp.Variable(n)
ret = mu_bl @ w
risk = cp.quad_form(w, sigma)
nlp_overlay = alpha * (nlp_signal @ w)

objective = cp.Maximize(ret - (lam / 2) * risk + nlp_overlay)
constraints = [
    cp.sum(w) == 1,
    w >= 0,
    w <= 0.05,
    cp.sum(cp.abs(w - w_prev)) <= 0.20,  # turnover
]
prob = cp.Problem(objective, constraints)
prob.solve(solver=cp.OSQP)

if prob.status not in ["optimal", "optimal_inaccurate"]:
    # fallback: 이전 포트폴리오 유지
    return w_prev
```

## 출력 형식
```python
def rebalance(
    current_portfolio: dict[str, float],
    signals: pd.DataFrame,
    date: pd.Timestamp,
) -> tuple[dict[str, float], list[Order]]:
    """목표 포트폴리오와 주문 리스트 반환."""
```
