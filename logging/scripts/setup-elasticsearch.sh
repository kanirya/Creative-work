#!/bin/bash

# Setup script for Elasticsearch index lifecycle policy and template
# This script configures 30-day log retention for EduPilot logs

set -e

ELASTICSEARCH_URL="${ELASTICSEARCH_URL:-http://localhost:9200}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Waiting for Elasticsearch to be ready..."
until curl -s "$ELASTICSEARCH_URL/_cluster/health" > /dev/null; do
  echo "Elasticsearch is unavailable - sleeping"
  sleep 5
done

echo "Elasticsearch is up - configuring index lifecycle policy"

# Create index lifecycle policy for 30-day retention
echo "Creating index lifecycle policy..."
curl -X PUT "$ELASTICSEARCH_URL/_ilm/policy/edupilot-logs-policy" \
  -H 'Content-Type: application/json' \
  -d @"$PARENT_DIR/elasticsearch/index-lifecycle-policy.json"

echo ""
echo "Index lifecycle policy created successfully"

# Create index template
echo "Creating index template..."
curl -X PUT "$ELASTICSEARCH_URL/_index_template/edupilot-logs-template" \
  -H 'Content-Type: application/json' \
  -d @"$PARENT_DIR/elasticsearch/index-template.json"

echo ""
echo "Index template created successfully"

# Create initial index with alias
echo "Creating initial index..."
curl -X PUT "$ELASTICSEARCH_URL/edupilot-logs-000001" \
  -H 'Content-Type: application/json' \
  -d '{
    "aliases": {
      "edupilot-logs": {
        "is_write_index": true
      }
    }
  }'

echo ""
echo "Initial index created successfully"

echo ""
echo "Elasticsearch setup complete!"
echo "Logs will be retained for 30 days and automatically deleted after that period."
echo ""
echo "Access Kibana at: http://localhost:5601"
echo "Elasticsearch API: $ELASTICSEARCH_URL"
