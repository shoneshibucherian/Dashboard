#!/usr/bin/env bash
#set -Eeuo pipefail

# Paths
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FLASK_FILE="$ROOT/modified_serve.py"
DASHBOARD_NAME="modified"  # Update if needed
GRAFANA_PORT=3000
FLASK_PORT=5000

# Read variables from user_config.ini
HOST_IP=$(curl -s ifconfig.me)
mongodb_uri=$(grep ip ../user_config.ini | awk '{print $3}')
python_env=$(grep python_env_path ../user_config.ini | awk '{print $3}')
table=$(grep table ../user_config.ini | awk '{print $3}')
db=$(grep db_name ../user_config.ini | awk '{print $3}')
docker=$(grep docker ../user_config.ini | awk '{print $3}')

echo "Starting Flask server..."
echo "Using Flask file: $FLASK_FILE | DB: $db | Table: $table"
nohup "$python_env" -u "$FLASK_FILE" "${mongodb_uri}" "$db" "$table" > /tmp/output.log 2>&1 &
FLASK_PID=$!
sleep 2  # Give Flask time to start
echo "the value of docker flag is $docker"
# Handle Grafana based on the docker flag
if [[ "$docker" == "yes" || "$docker" == "Yes" || "$docker" == "YES" ]]; then
  echo "Starting Grafana container..."
  docker compose -f "$ROOT/docker_compose.yml" up -d

  echo "Waiting for Grafana to become ready..."
  until curl -s "http://localhost:${GRAFANA_PORT}/api/health" | grep -q '"database":'; do
    sleep 2
  done
  echo "Grafana is up!"   
  echo "Grafana (Docker): http://${HOST_IP}:${GRAFANA_PORT}/"
  echo "Dashboard:     http://${HOST_IP}:${GRAFANA_PORT}/d/${DASHBOARD_NAME}/${DASHBOARD_NAME}?orgId=1&from=now-7d&to=now&timezone=UTC&var-IP=${HOST_IP}"
else
  echo "Docker flag is set to 'no'. Skipping Grafana container startup."
  echo "Please make sure Grafana is already installed and running locally."
  echo "All services are running!"
  echo "Host IP:     ${HOST_IP}"
  echo " Copy the Host IP above and paste it in the variable field of the provided grafana panel."

fi
