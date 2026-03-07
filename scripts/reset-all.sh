#!/bin/bash

echo "🔄 Resetting all database data..."

read -p "⚠️  This will destroy ALL data in both databases. Continue? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🛑 Stopping all containers..."
    docker-compose --profile all down -v
    
    echo "🧹 Cleaning up volumes..."
    docker volume prune -f
    
    echo "✅ All data reset completed!"
    echo "💡 Use './start-mysql.sh' or './start-postgres.sh' to restart"
else
    echo "❌ Reset cancelled"
fi
