---
description: 새로운 팩터를 시스템에 추가하고 IC 검증까지 자동 수행
argument-hint: <팩터명> <카테고리>
---

# 새 팩터 추가 워크플로우

사용자가 /add-factor $ARGUMENTS로 호출. 인자: <팩터명> <카테고리>.
예: /add-factor short_interest_ratio flow

## 실행 단계

### Step 1: 필요 데이터 확인 (직접 수행)
- 필요한 원시 데이터가 이미 DB에 있는지 확인
- 없으면 Step 2로, 있으면 Step 3으로 진행

### Step 2: 데이터 커넥터 추가 (data-connector 서브에이전트)
"data-connector 에이전트를 사용하여 [필요한 데이터]를 수집하는 커넥터를 src/ingestion/에 신규 생성. DB에 적재 데이터 저장."

### Step 3: 팩터 계산 구현 (factor-calculator 서브에이전트)
"factor-calculator 에이전트를 사용하여 src/signals/factors/{카테고리}.py에 calc_{팩터명} 함수 추가. @factor_registry 데코레이터 적용."

### Step 4: 테스트 작성 + 코드 리뷰 (병렬 실행)
다음 두 에이전트를 병렬로 호출:
- test-writer: tests/signals/factors/test_{카테고리}.py에 테스트 추가
- code-reviewer: Step 2, 3에서 생성된 코드 리뷰

두 가지 모두 완료 후 결과 종합

### Step 5: IC 검증 (ic-validator 서브에이전트)
"ic-validator 에이전트를 사용하여 {팩터명}에 대해 5년 백테스트, Walk-Forward Validation 실행. backtests/results/에 HTML 리포트 생성."

### Step 6: 편입 판단 (직접 수행)
ic-validator 결과를 기준으로:
- IC > 0.03 AND t-stat > 2.0: factor_registry에 추가, Git 커밋 중 "include=True"
- IC < 0.01: 코드는 유지하되 factor_registry에서 비활성화
- 그 외: 사용자에게 판단 요청

### Step 7: 요약 보고
사용자에게 결과 요약 제시:
- 추가된 파일 목록
- IC 주요 지표
- code-reviewer 지적 사항
- 채택/기각/보류 최종 판단
- 백테스트 리포트 링크

## 지침
- Step 4는 반드시 병렬, 다른 Step은 순차 (의존성 존재)
- 각 Step 완료 후 진행 상황 사용자에게 보고
- Step 5의 IC 검증은 5~10분 소요 가능, 대기 필요
- 실패 시 해당 Step에서 중단하고 사용자 판단 요청

## 병렬/순차 라우팅 논리

| Step | 에이전트 | 실행 방식 | 이유 |
|------|---------|----------|------|
| Step 2 | data-connector | 순차 | 데이터 수집이 모든 후속 단계의 전제 |
| Step 3 | factor-calculator | 순차 | 커넥터 완료 후에만 계산 가능 |
| Step 4 | test-writer + code-reviewer | 병렬 | 두 작업이 서로 독립적 (다른 파일에 작업) |
| Step 5 | ic-validator | 순차 | 테스트 통과 후 검증 |
