#!/bin/bash
echo "🛑 Stopping A³E Staging Environment"

# Stop Docker Compose
if [ -f "docker-compose.staging.yml" ]; then
    docker-compose -f docker-compose.staging.yml down
fi

# Kill any Python processes
pkill -f "src.a3e.main"

# Stop Redis if we started it
if pgrep -f "redis-server.*6380" > /dev/null; then
    pkill -f "redis-server.*6380"
fi

echo "✅ Staging environment stopped"
