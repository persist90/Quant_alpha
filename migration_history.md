# Quant Alpha — Migration History

**작성일:** 2026-04-22  
**환경:** Apple M1 Mac (arm64), macOS Darwin 24.6.0  
**작업 디렉토리:** `~/projects/quant-alpha/`

---

## 1. 아키텍처 철학

### 핵심 원칙
- **로컬 우선, 클라우드 독립:** 모든 인프라를 Mac 로컬에서 Docker로 운영. 외부 의존성 최소화.
- **시계열 특화 저장소:** 주가/팩터 데이터의 특성(고빈도 삽입, 시간 범위 조회)에 맞춰 TimescaleDB 채택. 일반 PostgreSQL 대비 압축·파티셔닝 자동화.
- **선언형 인프라:** 모든 서비스 설정을 `docker-compose.yml`과 Grafana provisioning YAML로 코드화. 재현 가능한 환경 보장.
- **헬스체크 기반 의존성:** `depends_on: condition: service_healthy`로 서비스 기동 순서를 런타임이 아닌 선언부에서 제어.
- **데이터/설정 분리:** 설정 파일은 로컬 바인드 마운트(`./grafana/provisioning`), 데이터는 Docker Named Volume으로 분리하여 설정 변경 시 데이터 소실 방지.

### 기술 스택 선택 근거

| 역할 | 선택 | 이유 |
|------|------|------|
| 시계열 DB | TimescaleDB (pg16) | PostgreSQL 호환 + 하이퍼테이블 자동 파티셔닝, 압축, 보존 정책 |
| 캐시/메시지큐 | Redis (alpine) | 저지연 팩터 캐싱, 주문 신호 큐잉에 적합 |
| 시각화 | Grafana OSS | TimescaleDB 네이티브 지원, 프로비저닝 자동화 가능 |
| 워크플로우 | Prefect 3 | Python 기반 스케줄링, 백테스트·데이터 수집 파이프라인 관리 |
| 서비스 모니터링 | Uptime Kuma | 경량 셀프호스팅, 각 엔드포인트 헬스 대시보드 |
| 외부 접근 | Tailscale | WireGuard 기반 VPN, 포트포워딩 없이 안전한 원격 접속 |

---

## 2. 구축 이력 및 핵심 결정 사항

### 2026-04-22 — 초기 환경 구축

#### Homebrew & Docker 설치
- Homebrew 5.1.1 기설치 확인.
- `brew install --cask docker` 실행 시 `/usr/local/cli-plugins`, `/usr/local/bin/kubectl` 생성에 sudo 필요 → 비인터랙티브 셸에서 실패.
- **해결:** 터미널에서 직접 `sudo mkdir -p /usr/local/cli-plugins && sudo chown $(whoami) /usr/local/cli-plugins` 실행 후 재설치.
- Docker compose 플러그인이 `/Applications/Docker.app/Contents/Resources/cli-plugins/docker-compose`에 위치하나 자동 링크 실패 → 수동으로 `~/.docker/cli-plugins/`에 심볼릭 링크 생성.

#### docker-compose.yml 설계 결정
- `restart: always`: 맥 재부팅 후 Docker Desktop이 뜨면 서비스 자동 복구.
- Grafana → TimescaleDB 의존성: `service_healthy` 조건으로 DB 준비 전 Grafana 기동 방지.
- Prefect Worker → Prefect Server 의존성: 동일 이유.
- Uptime Kuma 헬스체크 초기 설정 `wget --spider`가 302 리다이렉트를 실패로 처리 → `curl -w '%{http_code}'`로 교체.

#### TimescaleDB 초기화
- `init_db.sh`가 로컬에서 `psql`을 호출하나 Mac에 psql 미설치 → `docker exec quant_timescaledb psql`로 우회.
- 압축 정책 설정 시 `timescaledb.compress` 미설정 상태에서 `add_compression_policy` 호출 → `ALTER TABLE ... SET (timescaledb.compress)` 선행 필요.
- `verify.sh`도 동일하게 로컬 `psql`/`redis-cli` 의존 → `docker exec` 기반으로 수정.

#### Grafana 데이터소스 자동 프로비저닝
- `grafana/provisioning/datasources/timescaledb.yml` 바인드 마운트로 컨테이너 기동 시 자동 등록.
- API 검증: `POST /api/datasources/uid/{uid}/health` → `{"status":"OK","message":"Database Connection OK"}` 확인.

---

## 3. 현재 상태 (2026-04-22 기준)

### 서비스 상태

| 컨테이너 | 이미지 | 포트 | 상태 |
|----------|--------|------|------|
| quant_timescaledb | timescale/timescaledb:latest-pg16 | 5432 | healthy |
| quant_redis | redis:alpine | 6379 | healthy |
| quant_grafana | grafana/grafana-oss:latest | 3000 | healthy |
| quant_uptime_kuma | louislam/uptime-kuma:latest | 3001 | healthy |
| quant_prefect_server | prefecthq/prefect:3-latest | 4200 | healthy |
| quant_prefect_worker | prefecthq/prefect:3-latest | — | running |

### DB 스키마 (quant_db)

```sql
-- TimescaleDB v2.26.3 / PostgreSQL 16

ohlcv      -- 하이퍼테이블, 압축 ON, 7일 압축정책, 2년 보존정책
  time TIMESTAMPTZ, symbol TEXT, open/high/low/close/volume DOUBLE PRECISION

signals    -- 하이퍼테이블, 압축 ON, 7일 압축정책
  time TIMESTAMPTZ, symbol TEXT, factor_name TEXT, value DOUBLE PRECISION

positions  -- 하이퍼테이블, 압축 OFF (미해결 과제 참조)
  time TIMESTAMPTZ, symbol TEXT, quantity/avg_price/pnl DOUBLE PRECISION
```

### 접속 정보

| 서비스 | URL | 계정 |
|--------|-----|------|
| Grafana | http://localhost:3000 | admin / quant1234 |
| Uptime Kuma | http://localhost:3001 | 최초 접속 시 설정 필요 |
| Prefect UI | http://localhost:4200 | 없음 |
| PostgreSQL | localhost:5432 | quant / quant1234 / quant_db |
| Redis | localhost:6379 | 없음 |

---

## 4. 미해결 과제

### 즉시 처리 필요
- [ ] **Uptime Kuma 관리자 계정 생성** — http://localhost:3001 최초 접속 후 계정 설정 (브라우저에서 직접).
- [ ] **Tailscale 활성화** — `sudo tailscaled & tailscale up` 실행 후 브라우저 로그인 필요. 완료 전까지 외부 접근 불가.

### 보안 강화 (운영 전 권장)
- [ ] **Redis 비밀번호 설정** — 현재 무인증. 외부 노출 예정이면 `docker-compose.yml` Redis command에 `--requirepass <password>` 추가 후 재시작.
- [ ] **positions 테이블 압축 설정** — `ALTER TABLE positions SET (timescaledb.compress, timescaledb.compress_segmentby='symbol')` + `add_compression_policy` 미적용 상태.
- [ ] **Grafana 계정 분리** — 현재 admin 단일 계정. 읽기 전용 뷰어 계정 추가 권장.

### 향후 개발
- [ ] **데이터 수집 파이프라인** — `flows/` 디렉토리에 Prefect Flow 작성 (yfinance, KIS API 등).
- [ ] **Grafana 대시보드** — `grafana/provisioning/dashboards/`에 JSON 파일 추가하면 자동 로드됨.
- [ ] **백테스트 연동** — `backtest/` 결과를 `signals` 테이블에 삽입하는 로더 작성.
- [ ] **Mac 재부팅 자동화** — Docker Desktop 로그인 항목 등록 확인 (`시스템 설정 > 일반 > 로그인 항목`).

---

## 5. 운영 명령어 레퍼런스

```bash
cd ~/projects/quant-alpha

# 상태 확인
docker compose ps
bash verify.sh

# 재시작 / 중단 / 시작
docker compose restart
docker compose stop
docker compose start

# 로그 확인
docker compose logs --tail=50 timescaledb
docker compose logs --tail=50 grafana

# DB 접속
docker exec -it quant_timescaledb psql -U quant -d quant_db

# DB 백업
docker exec quant_timescaledb pg_dump -U quant quant_db > backup_$(date +%Y%m%d).sql

# 설정 변경 후 재적용 (이미지 재빌드 없이)
docker compose up -d --no-deps <서비스명>
```

---

## 6. 파일 구조

```
~/projects/quant-alpha/
├── docker-compose.yml                  # 전체 인프라 선언
├── .env                                # 환경변수 (비밀번호, 포트)
├── init_db.sh                          # TimescaleDB 스키마 초기화
├── verify.sh                           # 전체 서비스 헬스체크
├── migration_history.md                # 이 파일
├── flows/                              # Prefect 워크플로우 (.py)
└── grafana/
    └── provisioning/
        ├── datasources/
        │   └── timescaledb.yml         # TimescaleDB 자동 연결
        └── dashboards/
            └── dashboard.yml           # 대시보드 자동 로드 설정
```
