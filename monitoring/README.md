# EduPilot Monitoring Infrastructure

This directory contains the monitoring infrastructure for the EduPilot system using Prometheus for metrics collection and Grafana for visualization.

## Overview

The monitoring infrastructure provides:
- **Metrics collection** from all EduPilot services (API Gateway, Python microservices)
- **Response time tracking** for all HTTP endpoints
- **Error rate monitoring** with status code breakdown
- **Resource usage metrics** (CPU, memory, disk, network)
- **Database and cache metrics** (PostgreSQL, Redis)
- **Container metrics** via cAdvisor
- **Real-time visualization** via Grafana dashboards
- **30-day metrics retention** with automatic cleanup

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EduPilot Services                        │
│  (API Gateway, AI Agent, LMS Scraper, Transcription, etc.) │
└────────────────────┬────────────────────────────────────────┘
                     │ /metrics endpoints
                     ▼
              ┌──────────────┐
              │  Prometheus  │ ◄── Scrapes metrics every 15s
              └──────┬───────┘
                     │ Stores time-series data
                     │
                     ▼
              ┌──────────────┐
              │   Grafana    │ ◄── Visualizes metrics
              └──────────────┘
```

### Additional Exporters

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PostgreSQL  │────▶│   Postgres   │────▶│  Prometheus  │
│   Database   │     │   Exporter   │     │              │
└──────────────┘     └──────────────┘     └──────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│    Redis     │────▶│    Redis     │────▶│  Prometheus  │
│    Cache     │     │   Exporter   │     │              │
└──────────────┘     └──────────────┘     └──────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Docker     │────▶│   cAdvisor   │────▶│  Prometheus  │
│  Containers  │     │              │     │              │
└──────────────┘     └──────────────┘     └──────────────┘

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Host System │────▶│     Node     │────▶│  Prometheus  │
│              │     │   Exporter   │     │              │
└──────────────┘     └──────────────┘     └──────────────┘
```

## Components

### Prometheus
- **Purpose**: Metrics collection, storage, and querying
- **Port**: 9090
- **Access**: http://localhost:9090
- **Retention**: 30 days
- **Scrape Interval**: 15 seconds
- **Features**:
  - Time-series database
  - PromQL query language
  - Service discovery
  - Alerting rules (optional)

### Grafana
- **Purpose**: Metrics visualization and dashboards
- **Port**: 3002
- **Access**: http://localhost:3002
- **Default Credentials**: admin/admin (change on first login)
- **Features**:
  - Pre-configured Prometheus datasource
  - Custom dashboards
  - Alerting and notifications
  - User management

### Postgres Exporter
- **Purpose**: PostgreSQL database metrics
- **Port**: 9187
- **Metrics**:
  - Connection pool stats
  - Query performance
  - Database size
  - Transaction rates
  - Lock statistics

### Redis Exporter
- **Purpose**: Redis cache metrics
- **Port**: 9121
- **Metrics**:
  - Memory usage
  - Key statistics
  - Command statistics
  - Hit/miss rates
  - Client connections

### cAdvisor
- **Purpose**: Container resource metrics
- **Port**: 8081
- **Metrics**:
  - CPU usage per container
  - Memory usage per container
  - Network I/O
  - Disk I/O
  - Container lifecycle events

### Node Exporter
- **Purpose**: Host system metrics
- **Port**: 9100
- **Metrics**:
  - CPU usage
  - Memory usage
  - Disk usage
  - Network statistics
  - System load

## Quick Start

### 1. Start the Monitoring Infrastructure

```bash
# Start EduPilot services and monitoring infrastructure together
docker-compose -f docker-compose.yml -f monitoring/docker-compose.monitoring.yml up -d

# Or start monitoring infrastructure separately
cd monitoring
docker-compose -f docker-compose.monitoring.yml up -d
```

### 2. Verify Services are Running

```bash
# Check all monitoring containers
docker ps | grep edupilot

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana health
curl http://localhost:3002/api/health
```

### 3. Access Monitoring Interfaces

**Prometheus:**
1. Open http://localhost:9090
2. Navigate to **Status > Targets** to verify all services are being scraped
3. Use the **Graph** tab to query metrics

**Grafana:**
1. Open http://localhost:3002
2. Login with admin/admin (change password on first login)
3. Navigate to **Dashboards** to view pre-configured dashboards
4. Create custom dashboards as needed

## Metrics Collected

### HTTP Request Metrics (All Services)

**Request Count:**
```
http_requests_total{method="GET", endpoint="/api/query", status="200"}
```

**Request Duration:**
```
http_request_duration_seconds{method="POST", endpoint="/api/query"}
```

**Requests In Progress:**
```
http_requests_in_progress{method="GET", endpoint="/health"}
```

**Error Count:**
```
http_errors_total{method="POST", endpoint="/api/scrape", status="500"}
```

### .NET API Gateway Metrics

**HTTP Metrics:**
- `http_requests_received_total` - Total HTTP requests
- `http_requests_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Current requests being processed

**Process Metrics:**
- `process_cpu_seconds_total` - CPU time
- `process_working_set_bytes` - Memory usage
- `process_open_handles` - Open file handles
- `dotnet_collection_count_total` - GC collections

### Python Service Metrics

**Custom Metrics:**
- `http_requests_total` - Total requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `http_requests_in_progress` - Active requests
- `http_errors_total` - Error count by type

**Process Metrics:**
- `process_cpu_seconds_total` - CPU usage
- `process_resident_memory_bytes` - Memory usage
- `process_open_fds` - Open file descriptors

### Database Metrics (PostgreSQL)

- `pg_up` - Database availability
- `pg_stat_database_numbackends` - Active connections
- `pg_stat_database_xact_commit` - Committed transactions
- `pg_stat_database_xact_rollback` - Rolled back transactions
- `pg_database_size_bytes` - Database size
- `pg_stat_activity_count` - Active queries

### Cache Metrics (Redis)

- `redis_up` - Redis availability
- `redis_memory_used_bytes` - Memory usage
- `redis_connected_clients` - Connected clients
- `redis_commands_processed_total` - Total commands
- `redis_keyspace_hits_total` - Cache hits
- `redis_keyspace_misses_total` - Cache misses

### Container Metrics (cAdvisor)

- `container_cpu_usage_seconds_total` - CPU usage per container
- `container_memory_usage_bytes` - Memory usage per container
- `container_network_receive_bytes_total` - Network RX
- `container_network_transmit_bytes_total` - Network TX
- `container_fs_usage_bytes` - Disk usage

## Querying Metrics

### Prometheus Query Examples

**Average response time for API Gateway:**
```promql
rate(http_request_duration_seconds_sum{service="api-gateway"}[5m]) 
/ 
rate(http_request_duration_seconds_count{service="api-gateway"}[5m])
```

**Error rate percentage:**
```promql
sum(rate(http_errors_total[5m])) 
/ 
sum(rate(http_requests_total[5m])) * 100
```

**Requests per second by service:**
```promql
sum(rate(http_requests_total[1m])) by (service)
```

**95th percentile response time:**
```promql
histogram_quantile(0.95, 
  rate(http_request_duration_seconds_bucket[5m])
)
```

**Memory usage by container:**
```promql
container_memory_usage_bytes{name=~"edupilot-.*"}
```

**Database connection count:**
```promql
pg_stat_database_numbackends{datname="edupilot"}
```

**Redis cache hit rate:**
```promql
rate(redis_keyspace_hits_total[5m]) 
/ 
(rate(redis_keyspace_hits_total[5m]) + rate(redis_keyspace_misses_total[5m]))
```

## Creating Grafana Dashboards

### Import Pre-built Dashboards

Grafana has many community dashboards available:

1. Go to **Dashboards > Import**
2. Enter dashboard ID or upload JSON
3. Select Prometheus datasource

**Recommended Dashboard IDs:**
- **1860** - Node Exporter Full
- **893** - Docker and System Monitoring
- **763** - Redis Dashboard
- **9628** - PostgreSQL Database

### Create Custom Dashboard

1. Click **+ > Dashboard**
2. Click **Add visualization**
3. Select **Prometheus** datasource
4. Enter PromQL query
5. Configure visualization type (graph, gauge, table, etc.)
6. Set thresholds and alerts
7. Save dashboard

### Example Panel Queries

**API Response Time:**
```promql
histogram_quantile(0.95, 
  sum(rate(http_request_duration_seconds_bucket{service="api-gateway"}[5m])) by (le)
)
```

**Service Error Rate:**
```promql
sum(rate(http_errors_total[5m])) by (service)
```

**Container CPU Usage:**
```promql
rate(container_cpu_usage_seconds_total{name=~"edupilot-.*"}[5m]) * 100
```

## Alerting (Optional)

### Configure Alertmanager

1. Create `monitoring/alertmanager/alertmanager.yml`:
```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'email'

receivers:
  - name: 'email'
    email_configs:
      - to: 'alerts@example.com'
        from: 'prometheus@example.com'
        smarthost: 'smtp.example.com:587'
        auth_username: 'prometheus@example.com'
        auth_password: 'password'
```

2. Create alert rules in `monitoring/prometheus/alerts/rules.yml`:
```yaml
groups:
  - name: edupilot_alerts
    interval: 30s
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_errors_total[5m])) 
          / 
          sum(rate(http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }}"

      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95, 
            rate(http_request_duration_seconds_bucket[5m])
          ) > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.job }} is down"
          description: "Service has been down for more than 1 minute"
```

3. Update `prometheus.yml` to include alert rules:
```yaml
rule_files:
  - "alerts/*.yml"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

## Metrics Retention

Prometheus stores metrics for 30 days by default (configured in docker-compose.monitoring.yml):

```yaml
command:
  - '--storage.tsdb.retention.time=30d'
```

To change retention:
1. Edit `monitoring/docker-compose.monitoring.yml`
2. Modify the `--storage.tsdb.retention.time` flag
3. Restart Prometheus: `docker-compose restart prometheus`

## Performance Tuning

### For High Metric Volume

1. **Increase Prometheus storage**:
```yaml
volumes:
  prometheus-data:
    driver: local
    driver_opts:
      type: none
      device: /path/to/large/disk
      o: bind
```

2. **Adjust scrape interval** (edit `prometheus.yml`):
```yaml
global:
  scrape_interval: 30s  # Increase from 15s
```

3. **Enable metric relabeling** to drop unnecessary metrics:
```yaml
scrape_configs:
  - job_name: 'api-gateway'
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'go_.*'
        action: drop
```

### For Low Resource Environments

1. **Reduce retention period**:
```yaml
command:
  - '--storage.tsdb.retention.time=7d'
```

2. **Disable unnecessary exporters**:
```bash
docker-compose -f docker-compose.monitoring.yml stop cadvisor node-exporter
```

## Troubleshooting

### Prometheus not scraping targets

```bash
# Check Prometheus logs
docker logs edupilot-prometheus

# Verify target configuration
curl http://localhost:9090/api/v1/targets

# Check service /metrics endpoints
curl http://localhost:5000/metrics  # API Gateway
curl http://localhost:8001/metrics  # AI Agent
```

### Grafana not showing data

```bash
# Check Grafana logs
docker logs edupilot-grafana

# Verify Prometheus datasource
curl http://localhost:3002/api/datasources

# Test Prometheus connection from Grafana
# Go to Configuration > Data Sources > Prometheus > Test
```

### High disk usage

```bash
# Check Prometheus data size
docker exec edupilot-prometheus du -sh /prometheus

# Manually clean old data
docker exec edupilot-prometheus rm -rf /prometheus/wal/*

# Reduce retention period (see Performance Tuning)
```

### Metrics not appearing

```bash
# Check if service is exposing /metrics endpoint
curl http://localhost:8001/metrics

# Verify prometheus-client is installed (Python services)
docker exec edupilot-ai-agent pip list | grep prometheus

# Check for errors in service logs
docker logs edupilot-ai-agent
```

## Integration with Services

### Python Services

All Python services use the `prometheus_client` library with custom middleware:

**Middleware location:**
- `services/ai-agent/app/middleware/metrics.py`
- `services/lms-scraper/app/middleware/metrics.py`
- `services/transcription/app/middleware/metrics.py`
- `services/scheduler/app/middleware/metrics.py`

**Metrics exposed:**
- `http_requests_total` - Request counter
- `http_request_duration_seconds` - Duration histogram
- `http_requests_in_progress` - Active requests gauge
- `http_errors_total` - Error counter

### .NET API Gateway

The API Gateway uses `prometheus-net.AspNetCore` package:

**Configuration in Program.cs:**
```csharp
app.UseHttpMetrics();  // Middleware
app.MapMetrics();      // /metrics endpoint
```

**Metrics exposed:**
- `http_requests_received_total` - Request counter
- `http_requests_duration_seconds` - Duration histogram
- `http_requests_in_progress` - Active requests gauge
- Process and runtime metrics

## Maintenance

### Regular Tasks

1. **Monitor disk usage**:
```bash
docker exec edupilot-prometheus df -h /prometheus
```

2. **Check scrape health**:
```bash
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'
```

3. **Review Grafana dashboards** for anomalies

4. **Update alert rules** based on observed patterns

### Backup Prometheus Data

```bash
# Stop Prometheus
docker-compose -f monitoring/docker-compose.monitoring.yml stop prometheus

# Backup data directory
docker run --rm -v edupilot_prometheus-data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus-backup.tar.gz /data

# Restart Prometheus
docker-compose -f monitoring/docker-compose.monitoring.yml start prometheus
```

### Restore Prometheus Data

```bash
# Stop Prometheus
docker-compose -f monitoring/docker-compose.monitoring.yml stop prometheus

# Restore data
docker run --rm -v edupilot_prometheus-data:/data -v $(pwd):/backup alpine tar xzf /backup/prometheus-backup.tar.gz -C /

# Restart Prometheus
docker-compose -f monitoring/docker-compose.monitoring.yml start prometheus
```

## Security Considerations

### Production Deployment

For production environments:

1. **Enable authentication** for Prometheus:
```yaml
# Add to prometheus.yml
basic_auth_users:
  admin: $2y$10$...  # bcrypt hash
```

2. **Secure Grafana**:
   - Change default admin password
   - Enable HTTPS
   - Configure OAuth/LDAP authentication
   - Restrict dashboard editing

3. **Network security**:
   - Use internal Docker networks
   - Restrict port exposure
   - Use reverse proxy with authentication

4. **Sensitive metrics**:
   - Avoid exposing PII in metric labels
   - Use metric relabeling to drop sensitive data
   - Implement RBAC in Grafana

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Docker container logs
3. Consult Prometheus documentation: https://prometheus.io/docs/
4. Consult Grafana documentation: https://grafana.com/docs/

## References

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [prometheus-net Documentation](https://github.com/prometheus-net/prometheus-net)
- [prometheus_client Documentation](https://github.com/prometheus/client_python)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboard Best Practices](https://grafana.com/docs/grafana/latest/best-practices/best-practices-for-creating-dashboards/)
