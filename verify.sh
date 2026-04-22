#!/bin/bash
# 전체 서비스 상태 검증 스크립트
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}[OK]${NC}   $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
info() { echo -e "${YELLOW}[INFO]${NC} $1"; }

echo ""
echo "========================================="
echo "  Quant Alpha 서비스 상태 검증"
echo "========================================="
echo ""

# Docker 컨테이너 상태
info "Docker 컨테이너 상태:"
docker compose ps
echo ""

# TimescaleDB 연결 테스트
info "TimescaleDB 연결 테스트..."
if docker exec quant_timescaledb pg_isready -U quant -d quant_db >/dev/null 2>&1; then
    VER=$(docker exec quant_timescaledb psql -U quant -d quant_db -t -c "SELECT extversion FROM pg_extension WHERE extname='timescaledb';" 2>/dev/null | xargs)
    ok "TimescaleDB v${VER} 연결 성공 (localhost:5432)"
else
    fail "TimescaleDB 연결 실패"
fi

# Redis 연결 테스트
info "Redis 연결 테스트..."
if docker exec quant_redis redis-cli ping 2>/dev/null | grep -q "PONG"; then
    ok "Redis 연결 성공 (localhost:6379)"
else
    fail "Redis 연결 실패"
fi

# Grafana 상태 테스트
info "Grafana 상태 테스트..."
if curl -s http://localhost:3000/api/health 2>/dev/null | grep -q "ok"; then
    ok "Grafana 정상 동작 (http://localhost:3000)"
else
    fail "Grafana 응답 없음"
fi

# Uptime Kuma 테스트
info "Uptime Kuma 상태 테스트..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:3001 2>/dev/null | grep -qE "200|301|302"; then
    ok "Uptime Kuma 정상 동작 (http://localhost:3001)"
else
    fail "Uptime Kuma 응답 없음"
fi

# Prefect 서버 테스트
info "Prefect 서버 상태 테스트..."
if curl -s http://localhost:4200/api/health 2>/dev/null | grep -q "true\|healthy\|ok"; then
    ok "Prefect 서버 정상 동작 (http://localhost:4200)"
else
    fail "Prefect 서버 응답 없음"
fi

echo ""
echo "========================================="
echo "  접속 정보"
echo "========================================="
echo "  Grafana     → http://localhost:3000  (admin / quant1234)"
echo "  Uptime Kuma → http://localhost:3001"
echo "  Prefect UI  → http://localhost:4200"
echo "  PostgreSQL  → localhost:5432  (quant / quant1234 / quant_db)"
echo "  Redis       → localhost:6379"
echo "========================================="
