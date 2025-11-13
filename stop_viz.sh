#!/usr/bin/env bash
#set -Eeuo pipefail

# Paths
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLASK_PORT=5000

# Load docker flag from config
docker_flag=$(grep docker ../user_config.ini | awk '{print $3}')

echo "Stopping visualization stack..."

##########################
# Step 1: Stop Flask API #
##########################
FLASK_PID=$(lsof -ti tcp:$FLASK_PORT || true)
if [ -n "$FLASK_PID" ]; then
  echo "Killing Flask process on port $FLASK_PORT (PID: $FLASK_PID)..."
  kill "$FLASK_PID"
else
  echo "Flask server not found on port $FLASK_PORT. It may already be stopped."
fi

#############################################
# Step 2: Stop Grafana container if enabled #
#############################################
if [[ "$docker_flag" == "yes" || "$docker_flag" == "Yes" || "$docker_flag" == "YES" ]]; then
  echo "Docker flag is yes — stopping Docker Compose services (Grafana)..."
  docker compose -f "$ROOT/docker_compose.yml" down
else
  echo "Docker flag is 'no' — skipping Docker shutdown since Grafana is expected to be installed locally."
fi

echo " All services stopped."
