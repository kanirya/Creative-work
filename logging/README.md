# EduPilot Centralized Logging Infrastructure

This directory contains the centralized logging infrastructure for the EduPilot system using the ELK stack (Elasticsearch, Logstash, Kibana) with Filebeat for log shipping.

## Overview

The logging infrastructure provides:
- **Centralized log aggregation** from all EduPilot services
- **30-day log retention** with automatic deletion
- **Structured log parsing** for .NET (Serilog) and Python services
- **Real-time log visualization** via Kibana
- **Correlation ID tracking** across all services
- **Log level filtering** and search capabilities

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EduPilot Services                        │
│  (API Gateway, AI Agent, LMS Scraper, Transcription, etc.) │
└────────────────────┬────────────────────────────────────────┘
                     │ Docker logs
                     ▼
              ┌──────────────┐
              │   Filebeat   │ ◄── Collects container logs
              └──────┬───────┘
                     │ Ships logs
                     ▼
              ┌──────────────┐
              │   Logstash   │ ◄── Parses and enriches logs
              └──────┬───────┘
                     │ Indexes logs
                     ▼
              ┌──────────────┐
              │Elasticsearch │ ◄── Stores logs (30-day retention)
              └──────┬───────┘
                     │ Queries
                     ▼
              ┌──────────────┐
              │    Kibana    │ ◄── Visualizes logs
              └──────────────┘
```

## Components

### Elasticsearch
- **Purpose**: Log storage and search engine
- **Port**: 9200 (HTTP API), 9300 (Node communication)
- **Retention**: 30 days (automatic deletion via ILM policy)
- **Index Pattern**: `edupilot-logs-YYYY.MM.DD`

### Logstash
- **Purpose**: Log parsing, enrichment, and routing
- **Ports**: 
  - 5044 (Beats input from Filebeat)
  - 5000 (TCP input for direct log shipping)
  - 9600 (Monitoring API)
- **Features**:
  - JSON log parsing
  - Correlation ID extraction
  - Service name tagging
  - Log level normalization

### Kibana
- **Purpose**: Log visualization and analysis
- **Port**: 5601
- **Access**: http://localhost:5601
- **Features**:
  - Real-time log streaming
  - Advanced search and filtering
  - Dashboard creation
  - Log pattern analysis

### Filebeat
- **Purpose**: Log shipping from Docker containers
- **Features**:
  - Automatic Docker container discovery
  - Docker metadata enrichment
  - JSON log decoding
  - Excludes logging infrastructure containers

## Quick Start

### 1. Start the Logging Infrastructure

```bash
# Start EduPilot services and logging infrastructure together
docker-compose -f docker-compose.yml -f logging/docker-compose.logging.yml up -d

# Or start logging infrastructure separately
cd logging
docker-compose -f docker-compose.logging.yml up -d
```

### 2. Configure Elasticsearch

Wait for Elasticsearch to be ready, then run the setup script:

**Linux/Mac:**
```bash
./logging/scripts/setup-elasticsearch.sh
```

**Windows (PowerShell):**
```powershell
.\logging\scripts\setup-elasticsearch.ps1
```

This script will:
- Create the index lifecycle policy (30-day retention)
- Create the index template for log structure
- Create the initial index with proper alias

### 3. Access Kibana

1. Open http://localhost:5601 in your browser
2. Navigate to **Discover** in the left sidebar
3. Create an index pattern: `edupilot-logs-*`
4. Select `@timestamp` as the time field
5. Start exploring your logs!

## Log Format

### .NET API Gateway (Serilog)
```
[2024-01-15T10:30:45.123Z] [Information] [abc-123-def] Query processed for student 550e8400-e29b-41d4-a716-446655440000
```

### Python Services (Standard Logging)
```
2024-01-15 10:30:45,123 - app.services.query_processor - INFO - [abc-123-def] - Processing query for student 550e8400-e29b-41d4-a716-446655440000
```

### Indexed Fields in Elasticsearch

- `@timestamp`: Log timestamp
- `service`: Service name (api-gateway, ai-agent, lms-scraper, transcription, scheduler)
- `level`: Log level (info, warning, error, fatal)
- `correlation_id`: Request correlation ID for tracing
- `message`: Original log message
- `log_message`: Parsed log message content
- `logger_name`: Logger name (Python services)
- `container.name`: Docker container name
- `container.id`: Docker container ID
- `exception`: Exception details (if present)
- `stack_trace`: Stack trace (if present)

## Searching Logs

### Kibana Query Examples

**Find all errors:**
```
level:error
```

**Find logs for a specific service:**
```
service:api-gateway
```

**Find logs by correlation ID:**
```
correlation_id:"abc-123-def"
```

**Find errors in AI Agent service:**
```
service:ai-agent AND level:error
```

**Find logs with specific text:**
```
log_message:"authentication failed"
```

**Time range queries:**
```
@timestamp:[now-1h TO now]
```

## Log Retention Policy

The logging infrastructure implements a 30-day retention policy using Elasticsearch Index Lifecycle Management (ILM):

### Phases

1. **Hot Phase** (0-7 days)
   - Active indexing and searching
   - Daily rollover or when index reaches 50GB
   - High priority (100)

2. **Warm Phase** (7-30 days)
   - Read-only, optimized for search
   - Force merge to 1 segment
   - Shrink to 1 shard
   - Medium priority (50)

3. **Delete Phase** (30+ days)
   - Automatic deletion of old indices
   - Frees up storage space

### Monitoring Retention

Check ILM policy status:
```bash
curl http://localhost:9200/_ilm/policy/edupilot-logs-policy
```

View indices and their lifecycle phase:
```bash
curl http://localhost:9200/_cat/indices/edupilot-logs-*?v
```

## Configuration Files

### Logstash Pipeline
- **Location**: `logging/logstash/pipeline/logstash.conf`
- **Purpose**: Defines log parsing rules and output configuration
- **Customization**: Add custom grok patterns or filters here

### Filebeat Configuration
- **Location**: `logging/filebeat/filebeat.yml`
- **Purpose**: Configures Docker log collection
- **Customization**: Add additional input sources or processors

### Elasticsearch Templates
- **ILM Policy**: `logging/elasticsearch/index-lifecycle-policy.json`
- **Index Template**: `logging/elasticsearch/index-template.json`
- **Customization**: Modify retention period or index settings

## Troubleshooting

### Elasticsearch not starting
```bash
# Check Elasticsearch logs
docker logs edupilot-elasticsearch

# Increase memory if needed (edit docker-compose.logging.yml)
ES_JAVA_OPTS=-Xms1g -Xmx1g
```

### Logs not appearing in Kibana
```bash
# Check Filebeat is running
docker logs edupilot-filebeat

# Check Logstash is processing logs
docker logs edupilot-logstash

# Verify Elasticsearch indices
curl http://localhost:9200/_cat/indices?v
```

### High disk usage
```bash
# Check index sizes
curl http://localhost:9200/_cat/indices/edupilot-logs-*?v&s=store.size:desc

# Manually delete old indices if needed
curl -X DELETE http://localhost:9200/edupilot-logs-2024.01.01
```

### Filebeat permission issues
```bash
# Ensure Filebeat has access to Docker socket
docker exec edupilot-filebeat ls -la /var/run/docker.sock
```

## Performance Tuning

### For High Log Volume

1. **Increase Logstash workers** (edit `logstash/config/logstash.yml`):
   ```yaml
   pipeline.workers: 4
   pipeline.batch.size: 250
   ```

2. **Increase Elasticsearch heap** (edit `docker-compose.logging.yml`):
   ```yaml
   ES_JAVA_OPTS: "-Xms2g -Xmx2g"
   ```

3. **Add Elasticsearch replicas** for high availability:
   ```json
   "number_of_replicas": 1
   ```

### For Low Resource Environments

1. **Reduce Elasticsearch heap**:
   ```yaml
   ES_JAVA_OPTS: "-Xms256m -Xmx256m"
   ```

2. **Disable Kibana** if not needed:
   ```bash
   docker-compose -f docker-compose.logging.yml stop kibana
   ```

## Integration with Services

All EduPilot services are already configured with structured logging:

### .NET API Gateway
- Uses Serilog with structured logging
- Includes correlation IDs in all log entries
- Logs to stdout (captured by Docker)

### Python Microservices
- Use Python's logging module with JSON formatting
- Include correlation IDs from request headers
- Log to stdout (captured by Docker)

### No Code Changes Required
The logging infrastructure automatically collects logs from all services via Docker container logs. No application code changes are needed.

## Maintenance

### Regular Tasks

1. **Monitor disk usage**:
   ```bash
   docker exec edupilot-elasticsearch df -h /usr/share/elasticsearch/data
   ```

2. **Check ILM policy execution**:
   ```bash
   curl http://localhost:9200/_ilm/status
   ```

3. **Review Kibana dashboards** for anomalies

### Backup Elasticsearch Indices

```bash
# Create snapshot repository
curl -X PUT "http://localhost:9200/_snapshot/backup_repo" -H 'Content-Type: application/json' -d'
{
  "type": "fs",
  "settings": {
    "location": "/usr/share/elasticsearch/backup"
  }
}'

# Create snapshot
curl -X PUT "http://localhost:9200/_snapshot/backup_repo/snapshot_1?wait_for_completion=true"
```

## Security Considerations

### Production Deployment

For production environments, enable security features:

1. **Enable Elasticsearch security**:
   ```yaml
   xpack.security.enabled: true
   ```

2. **Configure TLS/SSL** for Elasticsearch communication

3. **Set up authentication** for Kibana access

4. **Restrict network access** to logging infrastructure

5. **Use secrets management** for credentials

## Monitoring

### Health Checks

```bash
# Elasticsearch cluster health
curl http://localhost:9200/_cluster/health?pretty

# Logstash node stats
curl http://localhost:9600/_node/stats?pretty

# Kibana status
curl http://localhost:5601/api/status
```

### Metrics to Monitor

- Elasticsearch cluster health (green/yellow/red)
- Index size and document count
- Logstash pipeline throughput
- Filebeat event rate
- Disk usage on Elasticsearch data volume

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Docker container logs
3. Consult Elastic Stack documentation: https://www.elastic.co/guide/
4. Check EduPilot system requirements documentation

## References

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash Documentation](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Filebeat Documentation](https://www.elastic.co/guide/en/beats/filebeat/current/index.html)
- [Index Lifecycle Management](https://www.elastic.co/guide/en/elasticsearch/reference/current/index-lifecycle-management.html)
