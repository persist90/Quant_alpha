# [L5 Monitor] L1 데이터 수집 검증용 대시보드 구축 계획

L2(시그널) 로직을 짜기 전에 눈으로 데이터(L1)를 확인하는 것은 퀀트 시스템 구축에서 매우 탁월한 접근입니다. 쓰레기 데이터가 들어가면 쓰레기 시그널이 나오기 때문입니다. (Garbage In, Garbage Out)

현재 프로젝트의 인프라(`docker-compose.yml`)에 이미 **Grafana**가 포함되어 있으므로, 이를 적극 활용하여 TimescaleDB와 연동하는 **데이터 퀄리티 및 수집 모니터링 대시보드**를 구축하는 아이디어를 제안합니다.

## User Review Required

> [!IMPORTANT]
> 대시보드의 목적과 시각화 패널 구성에 대한 의견을 확인해 주세요. 추가하고 싶은 지표가 있다면 말씀해 주시면 반영하겠습니다.

**제안하는 대시보드의 3가지 주요 역할:**
1. **파이프라인 헬스체크 (Pipeline Health)**: 어제 수집이 정상적으로 돌았는가?
2. **개별 종목 시각화 (Market Visualizer)**: 주가와 거래량이 맞게 들어왔는가? (캔들 차트)
3. **데이터 무결성 검증 (Data Integrity)**: 결측치(NaN)나 상장폐지/정지 등으로 데이터가 끊긴 종목은 없는가?

## Proposed Changes



### 1. Grafana Datasource 자동화 설정 (Provisioning)
Grafana UI에서 수동으로 DB를 연결할 필요 없이, 도커 컨테이너가 뜰 때 자동으로 TimescaleDB를 바라보도록 설정합니다.

#### [NEW] [grafana/provisioning/datasources/timescaledb.yaml](file:///Users/keonyoungsong/projects/quant-alpha/grafana/provisioning/datasources/timescaledb.yaml)
- type: `postgres`
- host: `timescaledb:5432`
- user: `quant` / database: `quant_db`
- TimescaleDB 쿼리 빌더 활성화

### 2. Grafana Dashboard 자동 로드 설정
작성할 대시보드 JSON 파일을 자동으로 로드하는 설정을 추가합니다.

#### [NEW] [grafana/provisioning/dashboards/dashboards.yaml](file:///Users/keonyoungsong/projects/quant-alpha/grafana/provisioning/dashboards/dashboards.yaml)
- `grafana/provisioning/dashboards` 디렉토리 내의 json 파일을 읽어오도록 경로 매핑.

### 3. Dashboard 패널 설계 (JSON 코드화)
클로드 코드가 Grafana 대시보드의 원형이 되는 JSON 파일을 직접 생성합니다. 

#### [NEW] [grafana/provisioning/dashboards/l1_market_data.json](file:///Users/keonyoungsong/projects/quant-alpha/grafana/provisioning/dashboards/l1_market_data.json)
아래 3개의 Row로 패널을 구성하는 JSON 템플릿 작성:

**Row 1: Pipeline Status (파이프라인 상태)**
- `Stat Panel`: **마지막 수집 시간** (`SELECT max(last_updated) FROM daily_price`)
- `Stat Panel`: **오늘 수집된 일봉 갯수** (KOSDAQ 150이면 150개 내외여야 함)
- `Stat Panel`: **오늘 수집된 4H봉 갯수**

**Row 2: Data Visualizer (데이터 육안 검증)**
- `Variable (변수)`: 상단 드롭다운에서 조회할 종목(Ticker) 선택 (`SELECT DISTINCT ticker FROM daily_price`)
- `Time Series Panel`: 선택된 종목의 **종가(Close) 라인 차트**
- `Bar Chart Panel`: 선택된 종목의 **거래량(Volume) 바 차트** (하단 배치)

**Row 3: Data Quality Alerts (결측치 및 이상치 감지)**
- `Table Panel`: **결측치 감지표** (최근 5일 내 volume=0 이거나 close가 NULL인 종목 리스트 쿼리)
- `Table Panel`: **미수집 감지표** (KOSDAQ 150 종목 중 오늘 날짜 데이터가 없는 종목 리스트)

## Verification Plan

### Manual Verification
1. `docker-compose restart grafana` 실행.
2. 브라우저에서 `localhost:3000` 접속 (admin / quant1234).
3. "L1 Market Data Monitor" 대시보드가 자동으로 생성되어 있는지 확인.
4. 상단 티커 드롭다운을 변경했을 때 주가/거래량 차트가 즉각적으로 변하는지 육안 확인.
5. (L1 수집 파이프라인이 정상 작동한 이후) Missing Data 테이블에 이상 종목이 잡히는지 확인.
