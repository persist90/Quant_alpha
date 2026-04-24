---
description: 새 팩터를 시스템에 추가하고 IC 검증까지 수행
argument-hint: <팩터명> <카테고리>
---

# 새 팩터 추가 워크플로우 (v3)

사용자가 /add-factor $ARGUMENTS로 호출.
예: /add-factor short_interest_ratio flow

## 실행 단계

### Step 1: 데이터 확인 (직접)
필요 원시 데이터가 DB에 있는지 확인. 없으면 Step 2로, 있으면 Step 3으로.

### Step 2: 데이터 수집 구현 (builder)
"builder에게: docs/domain/dart-parsing.md 참조하여
[필요한 데이터]를 수집하는 커넥터/파서를 src/ingestion/에 추가."

### Step 3: 팩터 계산 구현 (builder)
"builder에게: docs/domain/point-in-time.md와
docs/domain/factor-taxonomy.md 참조하여 src/signals/factors/{카테고리}.py에
calc_{팩터명} 함수 추가. @factor_registry 데코레이터 적용."

### Step 4: 검증 + 리뷰 (validator + reviewer 병렬)
- validator: pytest 작성 및 실행, IC 검증 (Walk-Forward 포함)
- reviewer: Step 2, 3 코드 리뷰

두 가지 모두 완료 후 결과 종합.

### Step 5: 편입 판단 (직접)
validator의 IC 결과 기준:
- IC > 0.03 AND t-stat > 2.0: factor_registry 추가 (include=True), Git 커밋
- IC < 0.01: 코드 유지하되 비활성화
- 중간: 사용자 판단 요청

### Step 6: 요약 보고
- 생성 파일 목록
- IC 주요 지표
- reviewer 지적 사항
- 채택/기각 최종 판단
- 백테스트 리포트 링크

## 지침
- Step 4만 병렬, 나머지 순차
- 각 Step 완료 후 진행 상황 보고
- 실패 시 해당 Step 중단 및 사용자 판단 요청
