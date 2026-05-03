#!/bin/bash
# 새 PC DB 복원 스크립트
# 사용법: bash restore_db.sh
# 전제: docker-compose up -d timescaledb 실행 후 healthy 상태

set -e

DUMP_FILE="quant_db_backup.dump"

if [ ! -f "$DUMP_FILE" ]; then
  echo "ERROR: $DUMP_FILE 없음. USB에서 이 폴더로 복사 후 재실행."
  exit 1
fi

echo "▶ 덤프 파일 컨테이너로 복사..."
docker cp "$DUMP_FILE" quant_timescaledb:/tmp/quant_db_backup.dump

echo "▶ DB 복원 중 (몇 분 소요)..."
docker exec quant_timescaledb bash -c "
  pg_restore -U quant -d quant_db \
    --no-owner --no-acl \
    --disable-triggers \
    -F c /tmp/quant_db_backup.dump
" 2>&1 | grep -v "^pg_restore: warning" || true

echo "▶ 복원 결과 확인..."
docker exec quant_timescaledb psql -U quant -d quant_db -c "
  SELECT '일봉' AS 테이블, COUNT(*) AS 행수 FROM daily_price
  UNION ALL
  SELECT '4H봉', COUNT(*) FROM intraday_price_4h;
"

echo "✓ DB 복원 완료"
