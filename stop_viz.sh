#!/usr/bin/env bash
#set -Eeuo pipefail

# Paths
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLASK_PORT=5000

echo "Stopping visualisation stack..."

# Step 1: Kill Flask server (assumes it runs on a known port like 5000)
FLASK_PID=$(lsof -ti tcp:$FLASK_PORT || true)
if [ -n "$FLASK_PID" ]; then
  echo "Killing Flask process on port $FLASK_PORT (PID: $FLASK_PID)..."
  kill "$FLASK_PID"
else
  echo "lask server not found on port $FLASK_PORT. It may already be stopped."
fi

# Step 2: Shut down Docker Compose services
echo "Stopping Docker Compose services (Grafana)..."
docker compose -f "$ROOT/docker_compose.yml" down

echo "✅ All services stopped."
