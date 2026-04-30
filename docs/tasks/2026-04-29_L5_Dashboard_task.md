# [L5 Monitor] L1 데이터 수집 검증용 대시보드 태스크

이 문서는 `2026-04-29_L5_Dashboard_plan.md` 설계에 기반하여 Claude Code가 실행할 작업 목록입니다.

## 1. Grafana Datasource Provisioning
- `[ ]` `grafana/provisioning/datasources/timescaledb.yaml` 파일 생성
- `[ ]` TimescaleDB (PostgreSQL) 접속 정보 설정 (host: timescaledb:5432, user/db 등)
- `[ ]` 쿼리 빌더 및 TimescaleDB 확장 기능 활성화 옵션 명시

## 2. Grafana Dashboard Provisioning
- `[ ]` `grafana/provisioning/dashboards/dashboards.yaml` 파일 생성
- `[ ]` `/etc/grafana/provisioning/dashboards` 경로와 JSON 파일을 매핑하는 프로비저닝 설정 작성

## 3. 대시보드 JSON 원형 생성
- `[ ]` `grafana/provisioning/dashboards/l1_market_data.json` 빈 대시보드 파일 뼈대 생성
- `[ ]` (옵션) Claude Code가 JSON의 복잡한 구조를 직접 작성하기 어렵다면, 기본적인 Variable(종목 선택)과 패널 1~2개 정도의 뼈대만 만들고, 구체적인 레이아웃은 수동으로 Grafana UI에서 저장한 뒤 덮어쓰도록 유도.

## 4. 적용 및 검증
- `[ ]` `docker-compose restart grafana` 커맨드 실행 (또는 사용자에게 실행 안내)
- `[ ]` `docs/tasks/daily_log.md` 파일에 L5 대시보드 구축 태스크 상태를 `[Done]`으로 변경
