# kyobo-workspace 설계 계획서 v2

> **생성**: 2026-05-01 | **상태**: User Review 대기 중 (v2 - 문서 분석 반영)
> **상세**: Gemini 아티팩트 `implementation_plan.md` 참조

## 문서 분석 결과
- 5개 교보 실제 문서 분석 완료
- 공통 패턴: A4, 나눔명조/나눔고딕, 문서당 평균 테이블 20개 + 이미지 11개
- 시각화 비중이 압도적 → 시각화 자동화가 핵심 가치

## 도출된 3가지 템플릿
1. **투심위 보고서** (IQUW, Clearwater 참조)
2. **사업기획서** (손해보험진출, 시니어비즈니스 참조)
3. **전략제안서** (웹3 패러다임 참조)

## 시각화 시스템 (핵심)
- Mermaid: 투자구조도, 로드맵, 프로세스, 마인드맵
- matplotlib: 시장규모, 경쟁사비교, 재무차트
- python-docx: Word 네이티브 표 자동 생성
- 교보 전용 테마/색상 적용

## 구현 Phase
- Phase 1: Repo 초기화 + 템플릿 (Day 1)
- Phase 2: 시각화 파이프라인 — 핵심 (Day 1~2)
- Phase 3: Word 변환 (Day 2~3)
- Phase 4: 리서치 관리 (Day 3)
- Phase 5: Google Drive (Day 4)
