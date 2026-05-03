# Repo 전략 검증 분석서

> **생성**: 2026-05-01 | **근거**: PDF 하네스 가이드 + 웹 리서치 (3건)
> **상세**: Gemini 아티팩트 `repo_strategy_analysis.md` 참조

## 핵심 결론
1. **Repo 분리 유지** — 도메인/보안/의존성이 완전히 다름
2. **Global CLAUDE.md** — `~/.claude/CLAUDE.md`에 Python 경로 등 공통 규칙 배치
3. **kyobo-workspace에 HARNESS/ 추가** — PDF 가이드의 실행 제어 패턴 적용
4. **루트 TODO.md + LOG.md** — Claude가 즉시 참조 가능
5. **quant-alpha 구조는 현재 그대로 유지**

## 환경변수 공유 방법
- Claude Code 설정 계층: Global → Project → Local
- `~/.claude/settings.json`에 공통 환경변수 정의
- 각 repo의 `.claude/settings.json`에 프로젝트별 설정

## 구조 개선
- kyobo-workspace에 `HARNESS/` 디렉토리 추가 (router, context, loop, roles)
- `docs/guides/` 디렉토리 추가 (보고서/시각화/변환 가이드)
