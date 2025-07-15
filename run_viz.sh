#!/usr/bin/env bash
#set -Eeuo pipefail

# Paths
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLASK_FILE="$ROOT/modified_serve.py"
DASHBOARD_NAME="modified"  # Update this to your actual dashboard title if needed
GRAFANA_PORT=3000
FLASK_PORT=5000
HOST_IP=$(grep host_addr ../user_config.ini | awk '{print $3}')  # Replace with your external IP or domain name
mongodb_uri=$(grep ip ../user_config.ini | awk '{print $3}')
python_env=$(grep python_env_path ../user_config.ini | awk '{print $3}')
table=$(grep table ../user_config.ini | awk '{print $3}')
db=$(grep db_name ../user_config.ini | awk '{print $3}')
echo " Starting Flask server..."
echo $FLASK_FILE $db $table
nohup "$python_env" -u "$FLASK_FILE" "${mongodb_uri}" "$db" "$table" > /tmp/output.log &
FLASK_PID=$!
sleep 2  # Give Flask time to bind the port

echo "Starting Grafana container..."
docker compose -f "$ROOT/docker_compose.yml" up -d

echo "Waiting for Grafana to become ready..."
until curl -s "http://localhost:${GRAFANA_PORT}/api/health" | grep -q '"database":'; do
  sleep 2
done
echo "Grafana is up!"

# Wait a little to ensure dashboard is provisioned
sleep 3

# Final output
echo ""
echo " All services are running!"
echo "Flask API:     http://${HOST_IP}:${FLASK_PORT}/"
echo "Grafana:       http://${HOST_IP}:${GRAFANA_PORT}/"
echo "Dashboard:     http://${HOST_IP}:${GRAFANA_PORT}/d/modified/modified?orgId=1&from=now-7d&to=now&timezone=UTC&var-IP=${HOST_IP}"
echo ""



