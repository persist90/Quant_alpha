# kyobo-workspace 구현 태스크 리스트

> **프로젝트**: kyobo-workspace (교보생명 신사업기획팀 업무 Repo)
> **설계서**: `docs/tasks/2026-05-01_kyobo-workspace_plan.md`
> **생성일**: 2026-05-01
> **실행**: Claude Code

---

## Phase 1: Repo 초기화 + 템플릿

- [ ] **1.1** `c:\Users\aiueo\projects\kyobo-workspace\` 생성 + `git init`
- [ ] **1.2** 전체 폴더 구조 생성
- [ ] **1.3** `.gitignore` 작성
- [ ] **1.4** `CLAUDE.md` 작성 (교보 보고서 에이전트 규칙)
- [ ] **1.5** `GEMINI.md` 작성
- [ ] **1.6** 보고서 템플릿 3종 (투심위, 사업기획서, 전략제안서)
- [ ] **1.7** 교보 원본 문서 → `templates/kyobo_originals/` 이동

## Phase 2: 시각화 파이프라인 — 핵심

- [ ] **2.1** `requirements.txt` 작성
- [ ] **2.2** `package.json` (Mermaid CLI)
- [ ] **2.3** `config/mermaid_kyobo.json` (Mermaid 교보 테마)
- [ ] **2.4** `config/chart_style.yaml` (matplotlib 교보 스타일)
- [ ] **2.5** `scripts/render_diagram.py` (Mermaid → 이미지)
- [ ] **2.6** `scripts/render_chart.py` (6종 차트: market_size, quadrant, pie, growth_projection, roadmap, stacked_bar)
- [ ] **2.7** `visuals/templates/` 재사용 데이터 템플릿
- [ ] **2.8** 샘플 시각화 5종 테스트 (투자구조도, 밸류체인시너지, 로드맵, 사분면, 시장규모)
- [ ] **2.9** `templates/리서치_노트.md`
- [ ] **2.10** `README.md`

## Phase 3: Word 변환 파이프라인

- [ ] **3.1** Pandoc 설치 확인
- [ ] **3.2** `templates/reference.docx` 생성 (나눔명조, 교보 스타일)
- [ ] **3.3** `scripts/export_docx.py` (MD → Word, 시각화 임베드, 네이티브 표)
- [ ] **3.4** `scripts/new_report.py` (새 보고서 폴더 생성)
- [ ] **3.5** 아카이브 이동 기능
- [ ] **3.6** 통합 테스트

## Phase 4: 리서치 관리

- [ ] **4.1** `research/_categories.yaml` 초기 정의
- [ ] **4.2** `scripts/new_category.py`
- [ ] **4.3** `scripts/index_builder.py`
- [ ] **4.4** 초기 카테고리 폴더 생성

## Phase 5: Google Drive 연동

- [ ] **5.1** Google Drive 설정 가이드 문서
- [ ] **5.2** `scripts/upload_drive.py`
- [ ] **5.3** `config/drive_config.yaml` 초기 설정

---

**상세 명세**: Gemini 아티팩트 `task.md` 참조 (각 태스크별 입출력, 파일 경로, 참조 문서 포함)

**Python 경로**: `C:\Users\aiueo\anaconda3\python.exe`
