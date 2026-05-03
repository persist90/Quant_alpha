# Biz-Workspace Repo 설계 계획서

> 이 문서는 Gemini가 2026-05-01에 생성한 설계 계획서입니다.
> 상세 내용은 Gemini 아티팩트 `implementation_plan.md`를 참조하세요.
> 상태: **User Review 대기 중**

## 요약
- 회사 업무용 별도 repo (`biz-workspace`) 신규 생성
- 보고서 작성·관리 (Markdown + YAML frontmatter, 템플릿 기반)
- 시각화 시스템 (Mermaid → SVG/PNG 변환)
- 시장 리서치 카테고리별 관리 (industry/company/technology/macro)
- 자동화 스크립트 (보고서 생성, 색인 빌드, 다이어그램 렌더링)

## 확인 필요 사항
1. Repo 이름: `biz-workspace` OK?
2. 보고서 포맷: Markdown → PDF 방식 OK? Word 호환 필요?
3. 웹 뷰어(MkDocs Material) 포함 여부
4. 보고서 종류 / 리서치 카테고리 상세
5. 시각화 결과물 용도 (발표용/개인용)
