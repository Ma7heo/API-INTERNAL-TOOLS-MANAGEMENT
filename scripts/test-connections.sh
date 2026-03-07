#!/bin/bash

echo "🧪 Testing database connections..."

# Test MySQL if running
if docker ps | grep -q "internal-tools-mysql"; then
    echo "📡 Testing MySQL connection..."
    if docker exec internal-tools-mysql mysql -u${MYSQL_USER:-dev} -p${MYSQL_PASSWORD:-dev123} -e "SELECT 'MySQL OK' as status;" ${MYSQL_DATABASE:-internal_tools} 2>/dev/null; then
        echo "✅ MySQL connection successful"
        echo "🔗 phpMyAdmin: http://localhost:${PHPMYADMIN_PORT:-8080}"
    else
        echo "❌ MySQL connection failed"
    fi
else
    echo "⚫ MySQL not running"
fi

echo ""

# Test PostgreSQL if running  
if docker ps | grep -q "internal-tools-postgres"; then
    echo "📡 Testing PostgreSQL connection..."
    if docker exec internal-tools-postgres psql -U ${POSTGRES_USER:-dev} -d ${POSTGRES_DATABASE:-internal_tools} -c "SELECT 'PostgreSQL OK' as status;" 2>/dev/null; then
        echo "✅ PostgreSQL connection successful"
        echo "🔗 pgAdmin: http://localhost:${PGADMIN_PORT:-8081}"
    else
        echo "❌ PostgreSQL connection failed"
    fi
else
    echo "⚫ PostgreSQL not running"
fi

echo ""
echo "📋 Current running containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
