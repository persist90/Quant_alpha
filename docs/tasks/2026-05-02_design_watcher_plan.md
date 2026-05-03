# 설계 자동 검증 모니터링 스크립트 기획서

> **작성자**: Gemini (Architect)
> **구현자**: Claude Code (Executor)

## 1. 목적
설계자(Gemini)가 `docs/tasks/` 폴더에 `_draft.md` (초안) 파일을 생성하거나 수정하면, 이를 감지하여 자동으로 Claude Code를 백그라운드에서 실행하고 비판적 리뷰 결과(`DESIGN_REVIEW.md`)를 생성하는 스크립트를 구축합니다.

## 2. 요구사항 (Claude가 구현할 내용)
- **파일명**: `scripts/design_watcher.py`
- **의존성**: 외부 라이브러리(`watchdog` 등) 없이 Python 기본 라이브러리(`os`, `time`, `subprocess`)만 사용할 것.
- **감시 경로**: `docs/tasks/` 폴더
- **트리거 조건**: `_draft.md`로 끝나는 파일이 수정되거나 생성될 때.
- **실행 로직 (Subprocess)**:
  - 파일 변경 감지 시 즉시 터미널 명령어 호출:
    `claude -p "You are a Senior Architect. Review [변경된파일경로] critically. Find logical flaws and missing contexts. Save your critique to docs/tasks/DESIGN_REVIEW.md. Do not execute any code."`
  - (주의) `claude` 명령어 호출 시 non-interactive 모드인 `-p` 옵션을 사용해야 함.
- **터미널 출력**:
  - 모니터링 시작: `"[Monitoring] docs/tasks/ 폴더 감시 중..."`
  - 감지 및 리뷰 시작: `"[Trigger] 파일 변경 감지. Claude 리뷰 시작..."`
  - 완료: `"[Success] DESIGN_REVIEW.md 생성 완료. 제미나이에게 수정을 지시하세요."`

## 3. 테스트 방법
스크립트 실행 후 `docs/tasks/test_draft.md` 파일을 생성하여 정상적으로 `DESIGN_REVIEW.md`가 튀어나오는지 확인합니다.
