# DART 재무제표 파싱 가이드

## 개요
DART(전자공시시스템) API에서 제공하는 XBRL/XML 재무제표는 회사별로 계정과목 명칭과 구조가 상이함. 표준 스키마로 정규화 필수.

## 파싱 전략
1. 샘플 5~10건 구조 분석 (회사 규모/업종별 1건씩)
2. 공통 스키마 정의 (BS, IS, CF 핵심 항목)
3. 회사별 예외 처리 로직 작성
4. 무작위 20건으로 정규화 결과 수동 검증

## 표준 계정과목 매핑

```yaml
# config/account_mapping.yaml 구조
balance_sheet:
  assets:
    - ["자산총계", "자산 합계", "총자산"]
  current_assets:
    - ["유동자산", "유동 자산"]
  cash:
    - ["현금및현금성자산", "현금 및 현금성 자산"]
income_statement:
  revenue:
    - ["매출액", "영업수익", "수익(매출액)"]
  operating_income:
    - ["영업이익", "영업이익(손실)"]
```

## API 엔드포인트

| 데이터 | API | 비고 |
|--------|-----|------|
| 재무제표 | `/fnlttSinglAcnt` | 단일회사 |
| 재무제표(다중) | `/fnlttMultiAcnt` | 복수회사 |
| 주요사항보고 | `/list` + `/document` | 공시 원문 |

## 파일 위치
- 파서: `src/ingestion/parsers/parse_{source}_{type}.py`
- 매핑 사전: `config/account_mapping.yaml`
- 실패 로그: `logs/parsing_failures/`

## 파싱 품질 기준
- 파싱 성공률: 95% 이상
- 계정과목 매핑률: 99% 이상
- 미매핑 계정: 자동 추론 금지 → 로그 + 수동 처리 큐

## 주의사항
- 연결재무제표 vs 별도재무제표 구분 필수
- 사업연도 종료일과 실제 공시일 분리 관리
- 수정공시 존재 시 최신 공시 우선 적용
