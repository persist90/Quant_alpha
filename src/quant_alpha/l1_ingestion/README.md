# L1 Ingestion Module

이 모듈은 시장 데이터, 재무제표 등 원시 데이터(Raw Data)를 수집하여 DB에 적재하는 역할을 담당합니다.

### 1. What does this module configure/own?
- 외부 API(KRX, DART, Yahoo Finance 등) 연동 로직
- 데이터 스키마 검증 및 정제(결측치 기본 처리)
- 원시 데이터의 PostgreSQL 적재

### 2. What are common modification patterns?
- 새로운 데이터 소스(예: 대체 데이터, 뉴스 크롤러) 추가.
- API 엔드포인트 변경에 따른 파서 수정.

### 3. What non-obvious patterns cause failures?
- DART API의 일일 호출 한도 초과.
- 공휴일/휴장일 처리 누락으로 인한 빈 데이터프레임 적재 시도 에러.
- 상장폐지된 종목의 식별자(티커) 충돌.

### 4. What are the cross-module dependencies?
- 이 모듈이 실패하면 `l2_signal`에서 전일자 데이터를 가져오지 못해 전체 파이프라인이 정지됩니다.
- 의존성: `PostgreSQL` (쓰기 권한 필요).

### 5. What tribal knowledge is hidden?
- 데이터 수집 시 항상 **UTC 기준으로 수집하되 DB 적재 시 KST(Asia/Seoul)로 명시적 변환**해야 합니다.
- API 타임아웃은 최소 30초 이상으로 설정해야 DART 서버 지연에 대응할 수 있습니다.
