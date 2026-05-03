# WHITEPAPER.md — 하네스 엔지니어링 설계 헌법

**범용 표준 v2.0** · 2026년 5월

---

## 이 문서의 사용 방법

**AI (Claude Code)에게**: 이 문서를 읽고 프로젝트 구조를 생성하거나 기존 프로젝트에 하네스를 씌운다. 모든 규칙에는 이유가 함께 있다. 이유를 이해하면 명시되지 않은 상황에서도 올바른 판단을 내릴 수 있다.

**사람에게**: 환경 최초 구성 시, 구조 변경 결정 시에만 읽는다. 일상 작업에서는 읽지 않는다. 일상 작업의 기준은 이 문서에서 도출된 AGENTS.md다.

**실행 명령 (새 프로젝트)**:

@WHITEPAPER.md 와 @\<설계서\>.md 를 읽고,

도메인: \<DOMAIN\>, 프로젝트명: \<NAME\> 으로 전체 구조를 생성해주세요.

**실행 명령 (기존 프로젝트에 하네스 씌우기)**:

@WHITEPAPER.md 와 @\<설계서\>.md 를 읽고,

이 프로젝트에 하네스 구조를 씌워주세요.

src/ 등 기존 코드는 수정하지 말고, 하네스 파일만 추가하세요.

---

# 1부. 왜 이 구조인가 — AI가 반드시 이해해야 하는 이유

## 1.1 에이전트 \= 모델 \+ 하네스

같은 Claude 모델이라도 하네스 설계에 따라 성공률이 78% vs 42%로 갈린다 (Anthropic 내부 측정). 모델 성능이 아니라 **하네스가 결과를 만든다**.

하네스가 제어하는 것:

- 무엇을 컨텍스트에 올릴지 (어떤 파일을 읽을지)  
- 어떤 도구를 허용·금지할지 (권한)  
- 작업 전후에 무엇을 자동 실행할지 (훅)  
- 실수를 어떻게 잡을지 (검증 게이트)  
- 세션 간 무엇을 기억할지 (메모리)

## 1.2 컨텍스트는 유한 자원이다

모델의 컨텍스트 윈도우가 커져도 **품질은 보장되지 않는다**. 연구 결과: 정확도는 컨텍스트 길이에 따라 U자 형태로 저하된다. 시작과 끝은 잘 보지만 중간은 놓친다. 더 중요한 것: **무관한 토큰이 관련 토큰보다 더 큰 피해를 준다.**

→ 결론: 필요한 파일만, 필요한 때에만 컨텍스트에 올린다. 이것이 모든 문서 설계의 기준이다.

## 1.3 컨텍스트 붕괴와 컨텍스트 불안

긴 작업에서 발생하는 두 가지 실패 모드:

- **컨텍스트 붕괴**: 오류 로그와 수정이 누적되면서 초기 제약을 잊고 아키텍처 규칙을 위반한 코드를 생성한다.  
- **컨텍스트 불안**: 컨텍스트 한계에 가까워지면 미완료 작업을 "완료"라 선언하고 종료한다.

→ 대응: 파일 시스템에 상태를 기록하고, 세션은 짧게 유지하고, 장기 작업은 Ralph Wiggum Loop를 사용한다.

## 1.4 훅은 조언이 아니라 강제다

AGENTS.md의 규칙은 모델이 "따르기로 노력"하는 조언이다. 훅(Hook)은 모델이 어떻게 생각하든 반드시 실행되는 강제다.

→ 매번 지켜져야 하는 규칙은 AGENTS.md가 아니라 훅으로 구현한다. 예: "작업 완료 전 verify.sh 실행" → Stop 훅으로 강제. 모델이 잊어도 시스템이 막는다.

## 1.5 듀얼 하네스에서 공유 파일이 진실의 소스다

Antigravity(Gemini)와 Claude Code는 강점이 다르다.

| 도구 | 강점 |
| :---- | :---- |
| Antigravity (Gemini) | 설계, 리서치, 아키텍처, 다이어그램, 스펙 작성 |
| Claude Code | 코드 구현, 디버깅, 테스트, 리팩토링 |

두 도구가 **같은 파일**을 공유하는 것이 핵심이다. .agents/handoff.md, .agents/progress.txt가 두 도구 간의 진실 소스다. 두 도구를 동시에 켜면 KV 캐시 미스로 토큰 비용이 3–5배 폭증하고 파일 충돌이 발생한다. → 한 번에 한 도구만 사용한다.

---

# 2부. 워크스테이션 구조 — 왜 이렇게 나누는가

## 2.1 3계층 분리

\~/projects/

├── \_meta/                    ← 공통 표준 (git repo, 모든 프로젝트 공유)

│

├── quant-trading/            ← 독립 repo

├── kyobo-work/               ← 독립 repo

└── playground/               ← 모노 repo

    └── packages/

**독립 repo로 분리하는 기준** (하나라도 해당하면 분리):

- 실거래 자금, 회사 자산 등 보안 민감  
- 5년 이상 장기 운영 예정  
- 독립적으로 배포 (Docker, 클라우드)  
- 외부 협업 가능성

그 외 실험적 도구, 단기 스크립트 → playground 안 패키지로.

이유: 독립 repo는 Claude Code가 `cd quant-trading && claude` 실행 시 퀀트 파일만 본다. kyobo-work 파일이 퀀트 컨텍스트에 섞이지 않는다. 격리가 자동이다.

## 2.2 \_meta의 역할

\_meta는 모든 프로젝트가 공유하는 표준이다. 한 번 수정하면 모든 프로젝트에 반영된다.

\_meta/

├── WHITEPAPER.md             ← 이 문서

├── templates/                ← 프로젝트 생성 시 복사할 파일 골격

├── skills/                   ← 도메인 무관 공유 스킬

└── domain-packs/             ← 도메인별 지식 팩

    ├── quant/

    │   └── DOMAIN.md         ← KIS API, KRX, TimescaleDB 규칙

    ├── content-ip/

    │   └── DOMAIN.md

    └── finance-research/

        └── DOMAIN.md

## 2.3 symlink로 \_meta 연결

각 프로젝트는 \_meta를 복사하지 않고 symlink로 참조한다. 이유: 복사하면 \_meta를 수정해도 각 프로젝트에 반영되지 않는다. symlink는 항상 최신을 가리킨다.

\# bootstrap.sh가 자동 생성하는 symlink

ln \-sfn \~/projects/\_meta/WHITEPAPER.md ./WHITEPAPER.md

ln \-sfn \~/projects/\_meta/skills ./skills-shared

ln \-sfn \~/projects/\_meta/domain-packs/quant ./.agents/domain-pack

새 컴퓨터에서는 bootstrap.sh 한 번 실행으로 symlink를 재생성한다.

---

# 3부. 프로젝트 내부 구조 — 각 파일이 왜 있는가

## 3.1 전체 디렉토리 구조

\<project-root\>/

│

│ ── 진입점 ─────────────────────────────────────

├── AGENTS.md                 ← 모든 AI 도구가 매 세션 자동 로드 (≤150줄)

├── CLAUDE.md                 ← Claude Code 전용 어댑터 (≤30줄)

├── GEMINI.md                 ← Antigravity 전용 어댑터 (≤30줄)

├── README.md                 ← 사람용

├── WHITEPAPER.md             ← symlink → \_meta/WHITEPAPER.md

│

│ ── 에이전트 운영 상태 ──────────────────────────

├── .agents/

│   ├── PLAYBOOK.md           ← 작업 유형별 절차 (≤200줄)

│   ├── ARCHITECTURE.md       ← 시스템 설계 나침반 (≤300줄)

│   ├── DOMAIN.md             ← symlink → \_meta/domain-packs/\<name\>/DOMAIN.md

│   ├── TODO.md               ← 작업 큐 (단일 진실 소스)

│   ├── LOG.md                ← append-only 세션 로그

│   ├── progress.txt          ← 교차 세션 위치 ("지금 어디까지")

│   ├── handoff.md            ← Antigravity ↔ Claude Code 인계 노트

│   ├── MEMORY/

│   │   ├── facts.md          ← 검증된 사실 (API 제약, 시스템 규칙)

│   │   ├── preferences.md    ← 사용자 선호

│   │   ├── entities.md       ← 외부 시스템·도구 정보

│   │   └── corrections.md    ← 과거 실수와 교정 (학습 기록)

│   ├── sessions/             ← 일별 작업 노트 (YYYY-MM-DD.md)

│   └── ambient/              ← 앰비언트 에이전트 산출물

│

│ ── 도구별 설정 ─────────────────────────────────

├── .claude/

│   ├── settings.json         ← 권한·훅·모델 (커밋)

│   ├── settings.local.json   ← 개인 오버라이드 (gitignored)

│   ├── skills/               ← 프로젝트 전용 스킬

│   └── agents/               ← 서브에이전트 정의

│

├── .mcp/

│   └── servers.json          ← MCP 서버 (Antigravity·Claude Code 공유)

│

│ ── 자동화 ──────────────────────────────────────

├── HARNESS/

│   ├── verify.sh             ← 원커맨드 품질 게이트

│   ├── prime-context.sh      ← 세션 시작 시 컨텍스트 준비

│   └── ambient.sh            ← 야간 메모리 통합 트리거

│

│ ── symlink (bootstrap.sh가 생성) ───────────────

├── skills-shared → \_meta/skills

│

│ ── 실제 코드 ───────────────────────────────────

├── src/

├── tests/

├── docs/

│   ├── adr/                  ← Architecture Decision Records

│   └── runbooks/

└── spec/                     ← Antigravity 산출물 (스펙 문서)

## 3.2 .agents/ vs .claude/ 분리 이유

**.agents/** \= 에이전트의 *상태와 메모리*. 도구 무관. Antigravity도 읽는다. **.claude/** \= Claude Code *전용* 설정. settings.json, 훅, 스킬.

이 분리가 없으면 Antigravity가 Claude Code 전용 설정을 읽거나, Claude Code 세션 로그가 Antigravity 컨텍스트를 오염시킨다.

---

# 4부. 핵심 파일 사양 — 무엇을 어떻게 작성하는가

## 4.1 AGENTS.md (≤150줄) — 매 세션 자동 로드

**왜 150줄 한도인가**: Anthropic 측정 결과 300줄 초과 시 모델의 지시 준수율이 붕괴된다. 모델은 200개 지시 한도를 AGENTS.md가 소진하면 작업별 지시를 놓친다. 150줄을 넘는 내용은 PLAYBOOK.md로 위임한다.

**왜 WHAT/WHY/HOW 순서인가**: 스택 → 목적 → 절차 순서일 때 모델 성능이 최적이다. 무엇인지 알아야 왜 필요한지 이해하고, 그래야 어떻게 할지를 올바르게 판단한다.

\# \<프로젝트명\> — AI 에이전트 운영 계약

\#\# WHAT (무엇인가)

\- \*\*목적\*\*: \<한 문단\>

\- \*\*기술 스택\*\*: \<언어/프레임워크/DB, 구체적 버전\>

\- \*\*디렉토리 맵\*\*:

  \- \`src/\` — \<역할\>

  \- \`.agents/\` — 에이전트 운영 상태

  \- \`HARNESS/\` — 검증·자동화

\#\# WHY (왜 존재하는가)

\- \*\*목표\*\*: \<한 문단\>

\- \*\*비목표\*\*: \<만들지 않는 것\>

\#\# HOW (어떻게 작업하는가)

\#\#\# 매 세션 시작 시

1\. Plan Mode로 시작 (편집 전 계획 먼저).

2\. .agents/progress.txt → .agents/TODO.md 순서로 읽는다.

3\. 한 번에 작업 하나. 완료 후 ./HARNESS/verify.sh 실행.

4\. 세션 종료 시 .agents/LOG.md와 .agents/progress.txt 갱신.

\#\#\# 명령어

\- \<build\>

\- \<test\>

\- \<lint\>

\#\#\# 규칙

\- \<코딩 컨벤션\>

\- Conventional commits

\- PR ≤400줄

\#\#\# 절대 금지

\- IMPORTANT: \<금지 1\> — 이유: \<왜 금지인가\>

\- IMPORTANT: \<금지 2\> — 이유: \<왜 금지인가\>

\- YOU MUST: 작업 완료 선언 전 verify.sh 통과 확인

\#\# 더 알아야 할 때

\- 작업 절차: @.agents/PLAYBOOK.md

\- 시스템 설계: @.agents/ARCHITECTURE.md

\- 도메인 규칙: @.agents/DOMAIN.md

\- 전체 기준: @WHITEPAPER.md

**넣지 말 것**: API 전체 문서, 범용 조언("깨끗한 코드"), 훅으로 강제할 수 있는 규칙. 규칙을 어길 때 자동으로 막혀야 하면 → AGENTS.md가 아니라 훅.

## 4.2 CLAUDE.md (≤30줄) — Claude Code 전용 어댑터

**왜 분리하는가**: AGENTS.md는 Antigravity도 읽는 공통 표준이다. Claude Code 전용 키바인딩, 모델 선택, 슬래시 커맨드는 AGENTS.md에 넣으면 Antigravity에서 의미 없는 노이즈가 된다.

\# \<프로젝트명\> — Claude Code 어댑터

@AGENTS.md 먼저 읽으세요. 여기는 Claude Code 전용 추가사항만.

\#\# Claude Code 운영

\- 항상 Plan Mode 시작 (Shift+Tab 두 번 또는 /plan)

\- 컨텍스트 80% 도달 시 /compact 실행

\- KV 캐시 주의: 세션 간격 5분 이상이면 캐시 미스. 짧고 자주.

\#\# 모델

\- 기본: claude-opus-4-7

\- 서브에이전트 (읽기 전용): claude-haiku-4-5

\#\# 커맨드

\- /verify — ./HARNESS/verify.sh

\- /handoff — Antigravity 인계 노트 작성

\- /garden — .agents/MEMORY/ 통합

\#\# 설정 위치

\- 권한·훅: .claude/settings.json

\- 스킬: .claude/skills/

\- 서브에이전트: .claude/agents/

## 4.3 GEMINI.md (≤30줄) — Antigravity 전용 어댑터

\# \<프로젝트명\> — Antigravity / Gemini 어댑터

@AGENTS.md 먼저 읽으세요. 여기는 Antigravity 전용 추가사항만.

\#\# Antigravity 역할

\- 설계·리서치·다이어그램·스펙 전담

\- 구현은 Claude Code로 인계

\#\# 작업 분담

| 작업 | 담당 |

|---|---|

| 시장 리서치, 도메인 학습 | Antigravity |

| 아키텍처 설계, ADR 초안 | Antigravity |

| 스펙 작성 (spec/\*.md) | Antigravity |

| 코드 구현·테스트·디버깅 | Claude Code |

| 리팩토링 | Claude Code |

\#\# 인계 프로토콜 (Antigravity → Claude Code)

1\. spec/SPEC-\<feature\>.md 작성

2\. .agents/handoff.md 갱신:

   \- 만들 것 / 제약 / 검증 기준 / 관련 파일 목록

3\. .agents/progress.txt 갱신: "Spec ready: \<feature\>"

4\. Antigravity 닫기 → Claude Code 새 세션 시작

   (동시에 켜지 않는다 — KV 캐시 폭증 방지)

## 4.4 .claude/settings.json — 권한과 훅

**왜 deny 목록이 필수인가**: allow만 설정하면 새 도구 추가 시 자동 허용된다. deny는 명시적 차단이다. 실수로 .env 파일을 읽거나 git 이력을 손상시키는 것을 시스템이 막는다.

**왜 Stop 훅에 verify.sh를 거는가**: 모델이 "완료"를 선언하기 전에 시스템이 강제로 검증을 돌린다. 검증 실패 시 exit 2로 Claude Code에 재시작 신호를 보낸다. 모델이 잊어도 막힌다.

{

  "permissions": {

    "allow": \[

      "Read",

      "Bash(git \*)",

      "Bash(poetry \*)",

      "Bash(pytest \*)",

      "Bash(./HARNESS/\*)"

    \],

    "deny": \[

      "Read(./.env\*)",

      "Write(./.git/\*\*)",

      "Write(./migrations/\*\*)",

      "Bash(curl \*)",

      "Bash(rm \-rf \*)"

    \]

  },

  "model": {

    "default": "claude-opus-4-7",

    "subagent": "claude-haiku-4-5"

  },

  "hooks": {

    "SessionStart": \[

      {

        "hooks": \[{"type": "command", "command": "./HARNESS/prime-context.sh"}\]

      }

    \],

    "Stop": \[

      {

        "hooks": \[{"type": "command", "command": "./HARNESS/verify.sh || exit 2"}\]

      }

    \],

    "PostToolUse": \[

      {

        "matcher": "Write(\*.py)",

        "hooks": \[{"type": "command", "command": "ruff format \\"$file\\" && ruff check \\"$file\\""}\]

      }

    \]

  },

  "attribution": {

    "commit": ""

  }

}

## 4.5 HARNESS/verify.sh — 원커맨드 품질 게이트

**왜 필요한가**: AI에게 "테스트 돌려봐"라고 할 때마다 명령어를 알려줄 필요가 없다. verify.sh 하나로 lint → typecheck → test → build 전체를 돈다. Stop 훅과 결합하면 모든 작업 완료 시 자동 실행된다.

\#\!/bin/bash

set \-e

echo "▶ Lint..."

ruff check . && ruff format \--check .

echo "▶ Type check..."

mypy src/

echo "▶ Tests..."

pytest tests/ \-x \-q

echo "▶ Build check..."

poetry check

echo "✓ All checks passed"

실제 명령어는 프로젝트 기술 스택에 맞게 채운다.

## 4.6 HARNESS/prime-context.sh — 세션 시작 컨텍스트

**왜 필요한가**: 모든 세션이 progress.txt와 TODO.md를 먼저 읽어야 하는데, AI가 매번 잊을 수 있다. SessionStart 훅으로 자동 실행하면 세션 시작 시 항상 현재 상태를 본다.

\#\!/bin/bash

echo "=== 현재 상태 \==="

echo "▶ Progress:"

cat .agents/progress.txt 2\>/dev/null || echo "(없음)"

echo ""

echo "▶ 다음 작업 (TODO 상위):"

head \-20 .agents/TODO.md 2\>/dev/null || echo "(없음)"

echo ""

echo "▶ 마지막 세션:"

ls \-t .agents/sessions/\*.md 2\>/dev/null | head \-1 | xargs head \-5 2\>/dev/null || echo "(없음)"

echo "================="

## 4.7 .agents/PLAYBOOK.md (≤200줄)

**왜 AGENTS.md와 분리하는가**: AGENTS.md는 매 세션 자동 로드되어 토큰을 소비한다. 작업 유형별 상세 절차는 작업 시작 시에만 필요하다. 조건부 로드가 더 효율적이다.

\# Playbook: \<프로젝트명\>

\#\# 작업 분류 (Router)

모든 요청을 시작 전 분류한다:

\- \*\*A. 답변만\*\*: 코드 수정 없음 → 바로 답변

\- \*\*B. 확인 필요\*\*: 요청이 불명확 → 질문 먼저

\- \*\*C. 실행\*\*: 파일 생성·수정 → 아래 Loop 적용

\#\# 컨텍스트 조립 규칙

\- 항상: AGENTS.md \+ CLAUDE.md \+ progress.txt \+ TODO.md

\- 구조 변경 시: \+ ARCHITECTURE.md

\- 도메인 작업 시: \+ DOMAIN.md (또는 domain-pack)

\- 디버깅 시: \+ MEMORY/corrections.md

\- 제외: 자동 생성 코드, deprecated/, MVP 범위 밖

\#\# 실행 Loop (5단계)

1\. \*\*Plan\*\*: 목표·수정할 파일·위험 요소 파악

2\. \*\*Draft\*\*: 초안 구현

3\. \*\*Review\*\*: 범위·규칙·단순성 검토

4\. \*\*Revise\*\*: 피드백 반영

5\. \*\*Report\*\*: 변경한 것·검증 결과·남은 문제

\#\# 작업 유형별 절차

\#\#\# 새 기능

1\. spec/ 또는 TODO에서 요구사항 확인

2\. ARCHITECTURE.md로 영향 모듈 파악

3\. Plan Mode로 단계별 계획 → 사람 승인

4\. 단계별 구현 → verify.sh

5\. PR 생성 → MEMORY/facts.md 갱신

\#\#\# 버그 수정

1\. 실패 재현 테스트 먼저 작성

2\. MEMORY/corrections.md에서 유사 사례 확인

3\. 최소 변경으로 패치

4\. 회귀 테스트 통과

5\. MEMORY/corrections.md에 기록

\#\#\# 리팩토링

1\. 현재 테스트 전부 통과 확인

2\. 작은 단위로 분할

3\. 단계마다 verify.sh

4\. 아키텍처 결정이면 docs/adr/ 추가

## 4.8 .agents/ARCHITECTURE.md (≤300줄)

**왜 코드 작성 시에만 로드하는가**: 시스템 설계는 새 기능 구현이나 구조 변경 시에만 필요하다. 단순 버그 수정이나 문서 작업에 로드하면 불필요한 토큰 소비다.

\# Architecture: \<프로젝트명\>

\#\# 시스템 개요

\<한 문단 \+ Mermaid 또는 ASCII 다이어그램\>

\#\# 기술 스택

\- Language: Python 3.11+

\- Orchestration: Prefect

\- DB: PostgreSQL 16 \+ TimescaleDB / DuckDB (백테스트)

\- Cache: Redis

\- Monitor: Grafana / Uptime Kuma

\- Broker: KIS REST API

\#\# 레이어 구조

\<src/ 하위 디렉토리와 각 역할\>

\#\# 데이터 흐름

\<핵심 흐름 1–3개\>

\#\# 모듈 의존성 규칙

\<순환 임포트 금지 등 규칙\>

\#\# "이 파일을 수정하면 어디에 영향가는가?" 인덱스

\<변경 위치 → 영향 모듈 → 필수 검증\>

\#\# Architecture Decision Records

\- ADR-001: \<결정과 이유\>

## 4.9 .agents/DOMAIN.md (≤200줄) — 4섹션 패턴

**왜 4섹션인가**: AI가 도메인 작업 시 즉시 필요한 것은 딱 네 가지다. 빠른 명령(Quick Commands), 중요 파일(Key Files), 알아야 할 숨은 규칙(Non-Obvious Patterns), 참조(See Also). 설명보다 빠른 조회가 목적이다.

\# Domain: \<프로젝트명\>

\#\# Quick Commands

\- \<자주 쓰는 명령 복붙용\>

\- \<예: poetry run pytest tests/unit/strategy/ \-x\>

\#\# Key Files

\- \<진짜 중요한 3–5개 경로와 한 줄 설명\>

\- \<예: src/data/kis\_adapter.py — KIS API 유일 진입점\>

\#\# Non-Obvious Patterns

(아래 형식: 규칙 — Why: 이유)

\- \<예: TimescaleDB chunk\_time\_interval은 1일로 고정 — Why: 1분봉 기준 1일 이하로 줄이면 chunk 폭증으로 쿼리 성능 저하\>

\- \<예: KIS WebSocket은 계정당 동시 1개만 허용 — Why: 초과 시 연결 거부, 조용히 실패함\>

\- \<예: 백테스트 결과는 KST 기준 저장 — Why: KRX는 UTC+9, UTC로 저장 시 날짜 경계 오류\>

\#\# See Also

\- \<관련 ADR\>

\- \<외부 문서 링크\>

## 4.10 .agents/MEMORY/ — 4파일 카테고리

**왜 단일 MEMORY.md가 아닌가**: 하나의 파일이 1000줄을 넘으면 모델이 중간 섹션을 놓친다. 카테고리별로 분리하면 필요한 카테고리만 선택적으로 로드할 수 있다.

| 파일 | 내용 | 로드 시점 |
| :---- | :---- | :---- |
| facts.md | 검증된 사실 (API 제약, 시스템 규칙) | 도메인 작업 시 |
| preferences.md | 사용자 선호 (코딩 스타일, 응답 방식) | 매 세션 |
| entities.md | 외부 시스템·도구 접속 정보 | 도메인 작업 시 |
| corrections.md | 과거 실수와 교정 | 디버깅 시 |

facts.md 예시:

\# Facts

\- KIS API 토큰 유효기간: 24시간 (검증: 2026-04-15)

\- KRX 정규장: 09:00–15:30 KST, 동시호가: 15:20–15:30

\- TimescaleDB hypertable chunk\_time\_interval: 1일 (1분봉 기준)

corrections.md 예시:

\#\#\# 2026-04-22: KIS WebSocket 동시 연결 초과

\- 실수: 5개 종목 동시 구독 시도

\- 결과: 연결 거부, 에러 메시지 없이 조용히 실패

\- 교정: 1개 연결 유지, 종목은 연결 안에서 추가/제거

\- 학습: KIS는 계정당 WebSocket 동시 1개 한도

## 4.11 .agents/handoff.md — 듀얼 하네스 인계

**왜 인계 노트가 필요한가**: Antigravity 세션과 Claude Code 세션은 컨텍스트를 공유하지 않는다. handoff.md가 없으면 Claude Code가 "Antigravity가 뭘 했는지"를 모르고 처음부터 다시 파악해야 한다.

\# Handoff

\#\# 방향

\- From: Antigravity

\- To: Claude Code

\- 시각: YYYY-MM-DD HH:MM KST

\#\# 만들어야 할 것

\<무엇을 구현해야 하는지 한 문단\>

\#\# 제약

\- \<지켜야 할 조건들\>

\#\# 검증 기준

\- \<완료 조건: 어떻게 확인하는가\>

\#\# 관련 파일

\- spec/\<SPEC-feature\>.md — 전체 스펙

\- \<기타 참고 파일\>

\#\# Antigravity 완료 산출물

\- \<만들어둔 파일 목록\>

\#\# Claude Code 시작 순서

1\. spec/\<SPEC-feature\>.md 읽기

2\. Plan Mode로 구현 계획

3\. 사람 승인 후 구현

---

# 5부. 실행 메커니즘 — 어떻게 작동하는가

## 5.1 작업 루프 (Plan→Execute→Review→Ship)

모든 비사소한 작업은 이 순서를 따른다.

| 단계 | 모드 | 핵심 |
| :---- | :---- | :---- |
| Plan | Plan Mode (읽기 전용) | 편집 전 계획. 사람이 승인. |
| Execute | Auto-accept | 승인된 계획만 구현. |
| Review | 새 서브에이전트 | 작성자와 다른 컨텍스트로 검토. |
| Ship | Normal | 커밋, PR. |

**왜 Plan Mode가 먼저인가**: 시행착오 구현 \+ 롤백보다 10분 계획이 더 빠르다. 실무자 보고: 35분 작업이 계획 후 12분으로 줄었다. **사람의 승인이 가장 중요한 체크포인트다.** 여기서 방향이 틀리면 이후 모든 것이 헛수고다.

## 5.2 Ralph Wiggum Loop (장기 자율 실행)

4시간 이상 작업이나 야간 자율 실행에 사용한다.

**핵심 원칙**: 진행 상태는 파일 시스템에 기록하고, 에이전트 컨텍스트는 매 반복마다 완전히 초기화한다. 이유: 오류 로그와 수정이 쌓이면 초기 제약을 잊는다 (컨텍스트 붕괴). 초기화하면 항상 신선한 눈으로 현재 상태를 본다.

while true:

    agent \= 새 컨텍스트로 시작

    agent.read("progress.txt", "TODO.md", "AGENTS.md")

    task \= 미완료 작업 1개 선택

    agent.execute(task)

    if verify.sh 실패:

        LOG.md에 실패 기록

        continue (다음 반복, 새 컨텍스트)

    progress.txt 갱신

    if 모든 작업 완료: break

**"소원은 컴파일되지 않는다"**: 요구사항을 기계가 검증할 수 있는 형태로 번역해야 한다.

- ❌ "앱이 잘 작동하게 해" → AI가 판단 불가  
- ✅ `pytest tests/` exits 0 → 명확한 성공 기준

## 5.3 KV 캐시 — 왜 비용에 영향을 주는가

Anthropic의 KV 캐시는 5분 후 식는다. 캐시 미스 시 토큰 비용이 10배로 늘어난다.

실수하기 쉬운 패턴:

Antigravity로 30분 설계 →

Claude Code로 전환 →

AGENTS.md (\~5,000 토큰) 캐시 미스 →

매 메시지마다 5,000 토큰 × 10배 \= 50,000 토큰 청구

대응:

- 두 도구를 동시에 켜지 않는다  
- 설계 완료 → 도구 완전 종료 → Claude Code 시작  
- 세션은 짧고 자주 (5분 내 재진입하면 캐시 유지)

## 5.4 앰비언트 에이전트 (야간 메모리 통합)

사용자가 작업하지 않는 야간에 백그라운드로 실행된다. HARNESS/ambient.sh를 cron으로 매일 02:00에 실행한다.

수행 작업:

1. .agents/MEMORY/ 전체 파일 검토  
2. 중복 항목 통합, 오래된 사실 검증  
3. 최근 7일 세션 로그에서 놓친 인사이트 추출  
4. 변경 사항을 PR 초안으로 생성 (자동 머지 금지)

**왜 PR 초안인가**: 앰비언트 에이전트가 메모리를 잘못 정리하면 되돌려야 한다. 자동 머지를 금지하고 사람이 확인 후 머지한다.

\#\!/bin/bash

\# HARNESS/ambient.sh

\# 사용자 활성 체크 (30분 이내 활동이면 건너뜀)

LAST=$(stat \-c %Y .agents/sessions/\*.md 2\>/dev/null | sort \-n | tail \-1)

if \[ $(( $(date \+%s) \- ${LAST:-0} )) \-lt 1800 \]; then

    echo "사용자 활성 — 건너뜀"; exit 0

fi

claude \--headless \\

  \--prompt "

.agents/MEMORY/ 모든 파일을 읽고:

1\. 중복 항목 통합

2\. facts.md의 사실을 현재 코드베이스와 대조 검증

3\. 최근 7일 .agents/sessions/\*.md 에서 놓친 인사이트 추출

4\. 변경 사항을 .agents/ambient/garden-log.md 에 기록

5\. git으로 PR 초안 생성 (머지하지 말 것)

제약: src/ 수정 금지. .env\* 접근 금지."

---

# 6부. 품질 측정 — 얼마나 잘 구성되었는가

## 6.1 AI-Ready 루브릭 v4 (115점)

분기마다 이 루브릭으로 자가 평가한다. 80점 미만 카테고리가 다음 분기 개선 대상이다.

| 카테고리 | 배점 | 우수의 모습 |
| :---- | :---- | :---- |
| AI Navigation | 15 | AGENTS.md ≤150줄, WHAT/WHY/HOW, 조건부 로드 명시 |
| 문서 품질 | 15 | 이유+규칙+실행이 함께, 나침반이지 백과사전 아님 |
| 트라이벌 지식 외부화 | 15 | Non-Obvious Patterns ≥1개/모듈, corrections.md 누적 |
| 모듈 의존성 | 10 | 명시적 의존성 맵, 순환 임포트 없음 |
| 검증 게이트 | 15 | verify.sh 원커맨드, Stop 훅, 리뷰어 서브에이전트 |
| 스펙·테스트 규율 | 10 | 기능 전 스펙 작성, 테스트 선행 |
| 신선도 | 10 | 파일 경로 주기적 검증, AGENTS.md 변경 로그 |
| 에이전트 성능 | 10 | KV 캐시 인식, 서브에이전트 격리, 작업당 도구 호출 |
| 권한·안전 | 5 | deny 목록, .env 접근 금지, 마이그레이션 보호 |
| 자동화 | 5 | 주간 비평, stale PR 자동, 사람 승인 게이트 |
| 앰비언트 자율성 | 5 | 야간 가드닝, 활동 감지, PR 초안만 |
| **합계** | **115** |  |

**등급**:

- 100–115: AI-Native (야간 자율 실행 가능)  
- 80–99: Production-grade (감독 실행)  
- 55–79: Workable (매 PR 사람 관여)  
- \<55: AI-Hostile (도구 호출 폭증)

## 6.2 성숙도 단계와 진입 조건

| 단계 | 이름 | 진입 조건 |
| :---- | :---- | :---- |
| 1 | 미구성 | AI 도구 미사용 |
| 2 | 챗봇 보조 | AI 도구 사용, 구조 없음 |
| 3 | Human-in-Loop | AGENTS.md \+ verify.sh |
| 4 | Systematic Harness | 1+3 문서 모델, 훅, MEMORY 카테고리화 |
| 5 | Agentic Flywheel | 앰비언트 에이전트, 자가 평가 사이클 |

각 단계를 2주 이상 안정 운영 후 다음 단계로. 건너뛰면 도구 복잡성에 압도된다.

---

# 7부. 부트스트랩 절차 — 새 컴퓨터에서 시작하는 법

## 7.1 전체 흐름

① \_meta repo clone

② 프로젝트 repo clone (기존 코드 포함)

③ bootstrap.sh 실행 (symlink 생성)

④ Claude Code에게 하네스 파일 생성 지시

⑤ verify.sh로 검증

⑥ 일상 작업 시작

## 7.2 bootstrap.sh

\#\!/bin/bash

\# \_meta/templates/bootstrap.sh

set \-e

META\_PATH="${META\_PATH:-$HOME/projects/\_meta}"

DOMAIN\_PACK="${DOMAIN\_PACK:-none}"

if \[ \! \-d "$META\_PATH" \]; then

  echo "ERROR: \_meta 없음. 먼저 실행:"

  echo "  git clone \<\_meta-url\> $META\_PATH"

  exit 1

fi

mkdir \-p .agents .agents/MEMORY .agents/sessions .agents/ambient

\# symlink 생성

ln \-sfn "$META\_PATH/WHITEPAPER.md" ./WHITEPAPER.md

ln \-sfn "$META\_PATH/skills" ./skills-shared

if \[ "$DOMAIN\_PACK" \!= "none" \] && \[ \-d "$META\_PATH/domain-packs/$DOMAIN\_PACK" \]; then

  ln \-sfn "$META\_PATH/domain-packs/$DOMAIN\_PACK" ./.agents/domain-pack

fi

\# .gitignore 갱신

for item in "WHITEPAPER.md" "skills-shared" ".agents/domain-pack" ".claude/settings.local.json" ".env\*"; do

  grep \-qxF "$item" .gitignore 2\>/dev/null || echo "$item" \>\> .gitignore

done

echo "✓ Bootstrap 완료"

echo "  다음: Claude Code에서 WHITEPAPER.md와 설계서를 함께 주고 하네스 생성 지시"

## 7.3 Claude Code에게 주는 최초 지시

다음 두 파일을 읽으세요:

1\. @WHITEPAPER.md — 하네스 구조 기준

2\. @\<프로젝트 설계서\>.md — 이 프로젝트의 기술 스택과 아키텍처

WHITEPAPER.md의 3부\~4부 기준으로 하네스 파일을 생성해주세요.

설계서에서 기술 스택·명령어·아키텍처·금지 규칙을 추출해서 placeholder를 채우세요.

기존 코드 파일(src/, tests/ 등)은 수정하지 마세요.

생성할 파일만 추가합니다.

완료 후 생성한 파일 목록과 함께 7부의 점검 체크리스트를 실행하세요.

## 7.4 점검 체크리스트

생성 완료 후 확인:

- [ ] AGENTS.md 존재, ≤150줄, placeholder 없음, 이유가 포함된 금지 규칙  
- [ ] CLAUDE.md 존재, @AGENTS.md 참조  
- [ ] GEMINI.md 존재, 인계 프로토콜 포함  
- [ ] .agents/PLAYBOOK.md 존재  
- [ ] .agents/ARCHITECTURE.md 존재, 프로젝트 실제 구조 반영  
- [ ] .agents/DOMAIN.md 존재, 4섹션 채워짐  
- [ ] .agents/MEMORY/ 4파일 존재  
- [ ] .agents/TODO.md 초기화  
- [ ] .agents/progress.txt 초기화  
- [ ] .agents/handoff.md 초기화  
- [ ] .agents/LOG.md 초기화  
- [ ] .claude/settings.json 존재, deny 목록 포함, Stop 훅 포함  
- [ ] HARNESS/verify.sh 존재, 실행 가능 (chmod \+x)  
- [ ] HARNESS/prime-context.sh 존재, 실행 가능  
- [ ] .gitignore에 symlink·env 항목 추가  
- [ ] 기존 코드 파일 변경 없음 (git diff로 확인)

---

# 부록. 안티패턴 — 하지 말아야 할 것

## A.1 문서 안티패턴

❌ **AGENTS.md에 이유 없는 규칙** → AI가 유사 상황에서 스스로 판단 불가. 반드시 "이유: ..." 포함.

❌ **300줄 이상 AGENTS.md** → 지시 준수율 붕괴. PLAYBOOK.md로 위임.

❌ **훅으로 강제할 수 있는 것을 AGENTS.md에 조언으로** → 모델이 잊으면 지켜지지 않음. 중요한 규칙은 훅으로.

❌ **상상된 실패에 대한 규칙** → AGENTS.md 비대화의 주범. 관찰된 실패만 기록.

## A.2 운영 안티패턴

❌ **두 도구 동시 사용** → KV 캐시 폭증, 파일 충돌. 한 번에 하나.

❌ **handoff.md 없이 도구 전환** → 컨텍스트 손실. 항상 인계 노트.

❌ **단일 MEMORY.md 1000줄** → 중간 섹션 누락. 카테고리별 분리.

❌ **측정 없이 성숙도 단계 건너뜀** → 복잡성에 압도. 입증된 실패가 있을 때만 다음 단계.

❌ **앰비언트 에이전트 자동 머지** → 잘못된 메모리 통합 시 되돌릴 수 없음. PR 초안만.

---

# 8부. MCP · 스킬 · 서브에이전트 — 도구 확장 시스템

## 8.1 MCP 서버 — 외부 도구를 AI 도구로 연결

**왜 MCP인가**: Claude Code와 Antigravity가 TimescaleDB, KIS API, Prefect 등 외부 시스템을 직접 호출하려면 bash 명령으로 우회해야 한다. MCP는 이를 타입 안전한 함수 호출로 바꿔 준다. 한 번 등록하면 두 도구 모두 사용한다.

**왜 .mcp/servers.json을 공유하는가**: `.claude/`는 Claude Code 전용이다. `.mcp/`는 도구 무관 공유 설정이다. Antigravity도 같은 MCP 서버를 사용하므로 반드시 공유 위치에 둔다.

**중요 — lazy ToolSearch**: Claude Code v2.1.x+는 시작 시 도구 *이름만* 로드하고 실제 스키마는 호출 시점에 가져온다. 등록된 MCP 서버가 많아도 컨텍스트 비용은 최소화된다.

`.mcp/servers.json` 표준:

{

  "servers": {

    "postgres": {

      "command": "npx",

      "args": \["@modelcontextprotocol/server-postgres", "${DATABASE\_URL}"\],

      "env": {"DATABASE\_URL": "${DATABASE\_URL}"}

    },

    "filesystem": {

      "command": "npx",

      "args": \["@modelcontextprotocol/server-filesystem", "${PROJECT\_ROOT}"\]

    },

    "github": {

      "command": "npx",

      "args": \["@modelcontextprotocol/server-github"\],

      "env": {"GITHUB\_TOKEN": "${GITHUB\_TOKEN}"}

    }

  }

}

**퀀트 프로젝트 추가 예시**:

{

  "servers": {

    "timescaledb": {

      "command": "npx",

      "args": \["@modelcontextprotocol/server-postgres", "${TIMESCALE\_URL}"\]

    },

    "prefect": {

      "command": "python",

      "args": \["-m", "prefect\_mcp\_server"\],

      "env": {"PREFECT\_API\_URL": "${PREFECT\_API\_URL}"}

    }

  }

}

**MCP 등록 규칙**:

- 환경변수로 자격증명 주입. 절대 servers.json에 직접 입력하지 않는다.  
- servers.json은 커밋한다. 자격증명은 .env에 두고 gitignore한다.  
- 새 외부 시스템 추가 시 항상 MCP 서버 먼저 검토한다. bash 래퍼는 최후 수단이다.

---

## 8.2 스킬(Skill) — 온디맨드 전문성 레이어

**왜 스킬인가**: 특정 작업(예: KIS API 호출 코드 작성)에만 필요한 상세 가이드를 매 세션 컨텍스트에 올리면 낭비다. 스킬은 YAML 프론트매터(\~100토큰)만 항상 로드하고, 본문은 모델이 적용 판단 시에만 로드한다. 이것이 *점진적 공개(progressive disclosure)* 의 구현체다.

**구조**:

.claude/skills/\<name\>/SKILL.md      ← 프로젝트 전용 스킬

\_meta/skills/\<name\>/SKILL.md        ← 도메인 무관 공유 스킬 (symlink로 참조)

\_meta/domain-packs/\<d\>/skills/      ← 도메인 전용 스킬

**SKILL.md 형식**:

\---

name: kis-api-integration

description: \>

  KIS API를 호출하는 코드를 만들거나 수정할 때 사용.

  토큰 갱신, 레이트 리밋, WebSocket 연결, 에러 처리 패턴을 안내.

  트리거: "KIS", "한투", "kis\_adapter", "토큰 갱신" 키워드 포함 시.

allowed-tools: Read, Edit, Bash(pytest tests/data/\*)

\---

\# KIS API Integration Skill

\#\# 핵심 제약 (반드시 지킬 것)

\- 토큰 유효기간: 24시간. 만료 5분 전 갱신 시도.

\- WebSocket: 계정당 동시 1개. 초과 시 조용히 실패.

\- 레이트 리밋: REST API 초당 20건. 초과 시 429 반환.

\- 모든 API 호출은 src/data/kis\_adapter.py 경유. 직접 호출 금지.

\#\# 토큰 갱신 패턴

(구체적 코드 예시)

\#\# WebSocket 연결 패턴

(구체적 코드 예시)

\#\# 에러 처리 패턴

(구체적 코드 예시)

\#\# 참고

\- src/data/kis\_adapter.py

\- MEMORY/facts.md (KIS API 검증된 사실)

\- docs/adr/ADR-003-kis-api.md

**스킬 작성 규칙**:

- `description`에 트리거 키워드를 명시한다. 모델이 이 설명으로 로드 여부를 판단한다.  
- 스킬 본문은 *이 작업에만* 필요한 내용. 범용 가이드는 AGENTS.md에.  
- `allowed-tools`로 스킬이 사용할 수 있는 도구를 제한한다.  
- 스킬이 10개를 넘으면 카테고리별로 서브디렉토리로 분리한다.

**공유 스킬 목록** (`_meta/skills/`에 미리 준비):

| 스킬 이름 | 트리거 상황 |
| :---- | :---- |
| code-review | PR 리뷰 요청 시 |
| doc-writing | 문서·주석 작성 시 |
| test-generation | 테스트 파일 생성 시 |
| pr-description | PR 설명 작성 시 |
| refactoring | 리팩토링 작업 시 |
| git-workflow | 브랜치·커밋·머지 작업 시 |

---

## 8.3 서브에이전트 — 컨텍스트 격리로 품질 확보

**왜 서브에이전트인가**: 작성자가 리뷰어를 겸하면 자신의 실수를 보지 못한다. 서브에이전트는 *사전 컨텍스트 없이* 독립적 판단을 한다. Anthropic 측정: 작성자/리뷰어 분리 시 단일 에이전트 대비 품질 \+90.2%.

**컨텍스트 방화벽**: 서브에이전트는 자체 컨텍스트 윈도우로 실행된다. 메인 에이전트의 오류 로그, 시행착오 이력이 서브에이전트에게 보이지 않는다. 이것이 핵심이다.

**언제 서브에이전트를 쓰는가**:

- PR 생성 전 코드 리뷰  
- 보안 취약점 스캔  
- 아키텍처 규칙 위반 검토  
- 대량 로그 분석 (결과만 메인으로 전달)

**리뷰어 서브에이전트** `.claude/agents/reviewer.md`:

\---

name: reviewer

description: \>

  PR 생성 전 코드를 독립적으로 리뷰한다.

  작성 컨텍스트 없이 순수하게 코드만 보고 판단한다.

tools: Read, Grep, Glob, Bash(pytest \* \--co \-q)

model: claude-opus-4-7

\---

당신은 이 코드를 처음 보는 독립적 리뷰어입니다.

작성자의 의도나 배경을 알지 못하는 상태에서 판단합니다.

다음 순서로 검토하세요:

1\. AGENTS.md의 Critical Rules 위반 여부

2\. .agents/ARCHITECTURE.md의 모듈 의존성 규칙 위반

3\. .env, 하드코딩된 자격증명, API 키 노출

4\. 에러 처리 누락 (특히 외부 API 호출)

5\. 테스트 커버리지 (새 함수에 테스트 없음)

피드백 형식:

\- 심각도: critical | major | minor

\- 위치: 파일명:줄번호

\- 문제: (구체적으로)

\- 권장: (어떻게 수정)

critical이 하나라도 있으면 마지막에 "BLOCK: 머지 불가" 출력.

없으면 "APPROVE: 머지 가능" 출력.

**보안 스캐너 서브에이전트** `.claude/agents/security-scanner.md`:

\---

name: security-scanner

description: 보안 취약점과 자격증명 노출을 스캔한다.

tools: Read, Grep, Glob, Bash(ruff check \* \--select S)

model: claude-haiku-4-5

\---

다음을 스캔하고 발견사항만 보고하세요:

1\. 하드코딩된 API 키, 비밀번호, 토큰

2\. .env 파일이 gitignore에 없는 경우

3\. SQL 인젝션 가능성 (문자열 포맷으로 쿼리 조합)

4\. 외부 입력을 검증 없이 사용

5\. 로그에 민감 정보 출력

발견사항 없으면 "CLEAN" 출력.

**서브에이전트 실행 방식**:

\# Claude Code에서

/agent reviewer

\# 또는 HARNESS/verify.sh에 통합

claude \--agent reviewer \--headless

**멀티 에이전트 사용 기준**:

| 작업 | 권장 구성 |
| :---- | :---- |
| 일반 코딩 | 단일 에이전트 |
| PR 리뷰 | 단일 \+ reviewer 서브에이전트 |
| 보안 민감 변경 | 단일 \+ reviewer \+ security-scanner |
| 대량 로그 분석 | 분석 서브에이전트 → 결과만 메인으로 |
| 병렬 작업 (독립 모듈) | 워크트리 격리 후 각자 에이전트 |

단일 에이전트가 *입증된 실패*를 보일 때만 멀티로 전환한다. 멀티 에이전트는 토큰 10–15배를 소비한다.

---

# 9부. 메모리 아키텍처 — 세션을 넘어 지식을 유지하는 법

## 9.1 4계층 메모리 모델

**왜 계층이 필요한가**: 모든 정보를 하나의 파일에 쌓으면 모델이 중간 섹션을 놓친다. 더 중요한 문제는 *읽어야 할 시점이 다르다*는 것이다. 절차적 규칙은 매 세션 필요하지만, 이번 주 작업 로그는 디버깅 시에만 필요하다.

| 계층 | 파일 | 읽는 시점 | 편집 주체 |
| :---- | :---- | :---- | :---- |
| **절차적** | AGENTS.md, CLAUDE.md | 매 세션 자동 | 사람 (신중하게) |
| **장기 큐레이션** | .agents/MEMORY/\*.md | 관련 작업 시 | 에이전트 \+ 사람 검토 |
| **에피소딕** | .agents/sessions/\*.md, LOG.md | 디버깅·회고 시 | 에이전트 자동 |
| **작업 상태** | .agents/TODO.md, progress.txt | 매 세션 자동 | 에이전트 |

**계층별 운영 원칙**:

- **절차적**: 거의 변하지 않는다. 규칙 추가 시 "왜" 함께 기록.  
- **장기 큐레이션**: 누적되지만 주기적 정리 필수. 200줄 초과 시 분할.  
- **에피소딕**: append-only. 직접 편집하지 않는다. 앰비언트 에이전트가 통합.  
- **작업 상태**: 세션 시작·종료 시 항상 갱신. 이것이 없으면 멀티 세션 작업이 처음부터 다시 시작된다.

## 9.2 Sidecar \+ Ambient Garden 2계층 통합

**문제**: 메모리를 그냥 두면 두 가지 방향으로 망가진다.

- 아무것도 안 하면 → 중복·모순·stale 정보가 쌓인다.  
- 매 턴 통합하면 → 느리고 비용이 크다.

**해결**: 두 속도로 통합한다.

**Layer 1 — Sidecar (매 턴, 빠름)**

새 정보가 생길 때마다 즉시 기존 메모리와 비교한다.

새 정보 발생 시:

  기존 메모리에서 유사 항목 검색

  → 유사도 높고 모순: 새 정보로 교체 (supersede)

  → 유사도 높고 일치: 기존 강화 (reinforce)

  → 유사도 낮음: 새 항목 추가

이유: 중복이 생기는 즉시 막는다. 나중에 정리할 쓰레기가 쌓이지 않는다.

**Layer 2 — Ambient Garden (야간, 깊음)**

사용자가 idle인 야간에 전체 메모리를 점검한다.

야간 앰비언트 사이클:

1\. MEMORY/ 전체 로드

2\. 교차 세션 중복 탐지·통합

3\. facts.md 항목을 현재 코드베이스와 대조 검증

   → 코드에서 사라진 사실은 stale 표시

4\. 최근 7일 sessions/\*.md 분석

   → 놓친 인사이트 추출 → 적절한 카테고리로

5\. 90일 이상 미참조 항목 가지치기 (foundational은 유지)

6\. 새 관계 발견 (A 사실 ↔ B 사실 연결)

7\. 변경 사항 → PR 초안 (자동 머지 금지)

이유: Sidecar가 막지 못한 장기 중복·stale을 정리한다. 야간에 하므로 작업 중 비용 없음.

## 9.3 메모리 카테고리 상세

**facts.md** — 검증 가능한 사실. 코드베이스나 외부 시스템으로 확인 가능.

\# Facts

\- KIS API 토큰 유효기간: 24시간 (검증: 2026-04-15, src/data/kis\_adapter.py:42)

\- TimescaleDB chunk\_time\_interval: 1일 설정 중 (검증: migrations/2026-04-01)

\- KRX 정규장: 09:00–15:30 KST

\- Redis 최대 메모리: 2GB (docker-compose.yml)

**preferences.md** — 사용자가 표명한 선호. 확인 불가, 존중만 가능.

\# Preferences

\- 응답은 직접적·논리 우선 (설명보다 결론 먼저)

\- 코드 변수명: 영문, 주석: 한글

\- 함수형 스타일 선호 (클래스보다 함수)

\- 작업 시작 전 항상 계획 먼저 보여줄 것

**entities.md** — 외부 시스템·도구·서비스 접속 정보.

\# Entities

\#\# 외부 시스템

\- TimescaleDB: localhost:5432, DB명 quant\_prod, 환경변수 DATABASE\_URL

\- Redis: localhost:6379, 환경변수 REDIS\_URL

\- Prefect Cloud: workspace 'quant-ws', 환경변수 PREFECT\_API\_KEY

\- KIS API: https://openapi.koreainvestment.com, 환경변수 KIS\_APP\_KEY/KIS\_APP\_SECRET

\#\# 모니터링

\- Grafana: http://localhost:3000

\- Uptime Kuma: http://localhost:3001

**corrections.md** — 과거 실수와 교정. 같은 실수 반복을 막는 학습 기록.

\# Corrections

\#\#\# 2026-04-22: KIS WebSocket 동시 연결 초과

\- 실수: 5개 종목 동시 구독 시도

\- 결과: 연결 거부, 에러 없이 조용히 실패

\- 교정: 1개 연결 유지, 종목은 subscribe/unsubscribe로 교체

\- 학습: KIS 계정당 WebSocket 1개 한도. 공식 문서에 명시 안 됨.

\#\#\# 2026-04-15: TimescaleDB chunk 폭증

\- 실수: chunk\_time\_interval=1시간으로 설정

\- 결과: chunk 수 폭증, 쿼리 성능 10배 저하

\- 교정: 1일로 변경 (1분봉 기준 하루 390행)

\- 학습: chunk당 100K\~10M 행이 최적. 계산 후 설정.

**카테고리 분할 기준**: 하나의 파일이 200줄을 넘으면 분할한다.

MEMORY/

├── facts/

│   ├── kis-api.md

│   ├── timescaledb.md

│   └── krx-rules.md

├── preferences.md

├── entities.md

└── corrections/

    ├── 2026-Q2.md

    └── 2026-Q1.md

## 9.4 도메인 팩 진화 — 프로젝트 지식을 재사용 가능하게

**왜 도메인 팩이 필요한가**: 같은 KIS API를 사용하는 두 번째 퀀트 프로젝트를 만들 때, 첫 번째 프로젝트에서 발견한 모든 gotcha를 다시 발견해야 한다면 낭비다. 도메인 팩은 이 지식을 *프로젝트에서 분리해 재사용 가능하게* 만든다.

**진화 워크플로우**:

1\. 작업 중 새 gotcha 발견

   → 즉시 프로젝트의 .agents/DOMAIN.md에 기록

2\. 한 달에 한 번 검토

   → "이 항목이 다른 퀀트 프로젝트에도 적용되는가?"

   → Yes: \_meta/domain-packs/quant/DOMAIN.md로 승격

   → No: 프로젝트 DOMAIN.md에 유지

3\. 승격 후

   → 프로젝트 DOMAIN.md에서 해당 항목 삭제

   → (domain-pack symlink로 자동 참조)

4\. 두 번째 프로젝트 시작 시

   → domain-pack이 이미 quant 지식을 담고 있음

   → 처음부터 선배 프로젝트의 교훈을 안고 시작

**도메인 팩 DOMAIN.md 예시** (`_meta/domain-packs/quant/DOMAIN.md`):

\# Domain Pack: Quant Trading

\#\# Quick Commands

\- poetry run pytest tests/unit/strategy/ \-x \-q

\- poetry run python \-m src.data.kis\_adapter \--test-connection

\- docker compose ps

\- prefect deployment run 'pipeline/daily'

\#\# Key Files

\- src/data/kis\_adapter.py — KIS API 유일 진입점. 직접 호출 금지.

\- src/strategies/base.py — 모든 전략의 부모 클래스

\- docker-compose.yml — 전체 인프라 정의

\- .prefect/deployments/ — Prefect 배포 설정

\#\# Non-Obvious Patterns

\- KIS WebSocket 동시 연결 1개 한도 (공식 문서 미기재) — Why: 초과 시 조용히 실패

\- 백테스트 결과는 KST 기준 저장 필수 — Why: UTC 저장 시 날짜 경계에서 오류

\- TimescaleDB chunk\_time\_interval=1일 고정 — Why: 1분봉 390행/일 기준 최적

\- Redis pub/sub는 실시간 시세에만. 포지션 데이터는 PostgreSQL — Why: Redis는 영속성 미보장

\- KIS 토큰 갱신은 만료 5분 전 선제적으로 — Why: 만료 후 갱신 시 진행 중 주문 실패

\#\# See Also

\- ADR-003: KIS API 설계 결정

\- ADR-007: DuckDB 백테스트 도입 이유

\- corrections.md: 과거 KIS API 관련 실수 목록

**도메인 팩 카탈로그** (`_meta/domain-packs/INDEX.md`):

| Pack | 핵심 도메인 | 사용 프로젝트 | 마지막 갱신 |

|---|---|---|---|

| quant | KIS API, TimescaleDB, Prefect, KRX | quant-trading | 2026-05-01 |

| content-ip | STO, IP 평가, 라이선스 | \- | \- |

| finance-research | M\&A, IM 작성, DDQ | kyobo-work | 2026-04-15 |

| ops-automation | n8n, Notion, 뉴스 클리핑 | playground | 2026-04-01 |

6개월 이상 미사용 팩 → archive 폴더로 이동.

---

# 10부. 세션 이식성 — 작업 재개 프로토콜

## 10.1 왜 세션 이식성이 필요한가

Claude Code와 Antigravity는 컨텍스트를 공유하지 않는다. 도구를 전환하거나 새 컴퓨터로 이동하거나 다음날 작업을 재개할 때마다 "지금 어디까지 했는가"를 다시 파악하는 데 시간을 낭비한다.

이를 막는 방법은 단순하다: **상태를 파일 시스템에 기록하고, 항상 파일을 먼저 읽는다.**

## 10.2 재개 프로토콜

어떤 상황에서든 작업을 재개할 때 이 순서를 따른다:

1\. AGENTS.md 읽기 (이 프로젝트가 무엇인가)

2\. .agents/progress.txt 읽기 (마지막으로 어디까지 했는가)

3\. .agents/TODO.md 읽기 (다음 작업은 무엇인가)

4\. .agents/sessions/\<최신\>.md 읽기 (어제 무슨 일이 있었는가)

5\. .agents/handoff.md 읽기 (다른 도구에서 넘어온 게 있는가)

이 5개 파일이 "어떤 도구로도 재개 가능한 상태"를 표현한다.

**도구 종속 파일은 .agents/에 두지 않는다**: Claude Code의 `/compact` 결과, Antigravity의 대화 캐시 등 도구 전용 파일은 각자의 디렉토리(`.claude/`, `.antigravity/`)에만 둔다. `.agents/`는 도구 무관이어야 한다.

## 10.3 progress.txt 작성 규칙

형식:

마지막 작업: \<무엇을 했는가\>

완료 여부: 완료 | 진행 중 | 차단됨

차단 이유: \<차단됨인 경우\>

다음 단계: \<TODO.md의 어느 항목\>

마지막 갱신: YYYY-MM-DD HH:MM KST

담당 도구: Claude Code | Antigravity

예시:

마지막 작업: momentum\_v2 전략 백테스트 수정 (ATR 필터 추가)

완료 여부: 진행 중

차단 이유: TimescaleDB 쿼리 성능 문제 미해결

다음 단계: TODO.md \#3 (TimescaleDB 인덱스 최적화)

마지막 갱신: 2026-05-01 21:30 KST

담당 도구: Claude Code

## 10.4 세션 노트 작성 규칙

`.agents/sessions/YYYY-MM-DD.md` 형식:

\# 2026-05-01 세션 노트

\#\# 한 줄 요약

ATR 기반 변동성 필터를 momentum\_v2에 추가. 백테스트 실행 중 TimescaleDB 성능 문제 발견.

\#\# 수행한 작업

\- src/strategies/momentum\_v2.py: ATR 필터 함수 추가

\- tests/unit/strategy/test\_momentum\_v2.py: 테스트 3개 추가, 전부 통과

\#\# 발견한 것

\- TimescaleDB: 백테스트 쿼리가 전체 테이블 스캔 중. 인덱스 누락 확인.

\#\# 미해결 문제

\- TimescaleDB 인덱스 최적화 필요 → TODO.md \#3 추가

\#\# 내일 시작점

TODO.md \#3: TimescaleDB symbol+time 복합 인덱스 추가

---

# 부록 B. 안티패턴 추가

## B.1 메커니즘 안티패턴

❌ **MCP 없이 bash로 DB 직접 접근** → 타입 안전성 없음, 에러 처리 불안정. MCP 서버 먼저 검토.

❌ **스킬 description에 트리거 키워드 없음** → 모델이 스킬을 언제 쓸지 판단 불가. 반드시 "트리거: ..." 포함.

❌ **서브에이전트를 단순 작업에 사용** → 토큰 10–15배 소비. 단일 에이전트가 입증된 실패 후에만 전환.

❌ **도구 종속 파일을 .agents/에 저장** → 도구 전환 시 .agents/가 오염. 도구 전용은 .claude/ 등에만.

## B.2 메모리 안티패턴

❌ **corrections.md 미작성** → 같은 실수 반복. 실수 발견 즉시 기록이 규칙.

❌ **facts.md에 검증 날짜 없는 항목** → stale 여부 판단 불가. 반드시 "(검증: YYYY-MM-DD)" 포함.

❌ **도메인 팩 승격 없이 프로젝트 DOMAIN.md만 비대화** → 두 번째 프로젝트에서 재사용 불가. 한 달마다 검토·승격.

---

*WHITEPAPER v2.1 — 이유+규칙+실행이 함께 있는 AI 실행용 설계 헌법* *갱신 시 \_meta/WHITEPAPER.md 수정 → 모든 프로젝트 자동 반영 (symlink)*  
