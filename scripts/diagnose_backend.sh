#!/bin/bash

# 백엔드 상태 진단 스크립트
# 사용법: ./scripts/diagnose_backend.sh

SERVER_IP="158.247.245.197"
SERVER_USER="root"
PROJECT_DIR="/root/auto-dashboard"

echo "🔍 백엔드 시스템 진단을 시작합니다..."
echo "Target: $SERVER_USER@$SERVER_IP"
echo "----------------------------------------"

ssh $SERVER_USER@$SERVER_IP << 'ENDSSH'
    cd /root/auto-dashboard

    echo "1️⃣  Docker 컨테이너 상태 확인:"
    docker compose --env-file .env.production ps
    echo ""

    echo "2️⃣  최근 백엔드 에러 로그 (Last 20 lines with ERROR):"
    docker compose --env-file .env.production logs backend --tail=200 | grep "ERROR" | tail -n 20 || echo "✅ 최근 에러 로그 없음"
    echo ""

    echo "3️⃣  데이터베이스 연결 및 봇 상태 확인:"
    docker compose --env-file .env.production exec -T postgres psql -U trading_user -d trading_db -c "
        SELECT 'Total Bots' as metric, count(*) as value FROM bot_instances
        UNION ALL
        SELECT 'Running Bots', count(*) FROM bot_instances WHERE is_running = true
        UNION ALL
        SELECT 'Active Positions', count(*) FROM positions WHERE size > 0;
    " || echo "❌ DB 연결 실패"
    echo ""

    echo "4️⃣  Redis 상태 확인:"
    docker compose --env-file .env.production exec -T redis redis-cli ping || echo "❌ Redis 연결 실패"
    echo ""
ENDSSH

echo "----------------------------------------"
echo "✅ 진단 완료"
