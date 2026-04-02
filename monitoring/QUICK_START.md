# EduPilot Monitoring - Quick Start Guide

Get the EduPilot monitoring infrastructure up and running in minutes.

## Prerequisites

- Docker and Docker Compose installed
- EduPilot services running (or ready to start)
- At least 2GB free disk space for metrics storage

## Step 1: Start Monitoring Infrastructure

### Option A: Start Everything Together

```bash
# From the project root directory
docker-compose -f docker-compose.yml -f monitoring/docker-compose.monitoring.yml up -d
```

### Option B: Start Monitoring Separately

```bash
# Start EduPilot services first
docker-compose up -d

# Then start monitoring
docker-compose -f monitoring/docker-compose.monitoring.yml up -d
```

## Step 2: Verify Services

Wait 30-60 seconds for all services to start, then check:

```bash
# Check all containers are running
docker ps | grep edupilot

# You should see:
# - edupilot-prometheus
# - edupilot-grafana
# - edupilot-postgres-exporter
# - edupilot-redis-exporter
# - edupilot-cadvisor
# - edupilot-node-exporter
```

## Step 3: Access Prometheus

1. Open http://localhost:9090 in your browser
2. Click **Status > Targets** in the top menu
3. Verify all targets show as "UP" (may take 1-2 minutes)

**Expected targets:**
- prometheus (self-monitoring)
- api-gateway
- ai-agent
- lms-scraper
- transcription
- scheduler
- postgres
- redis
- cadvisor
- node

## Step 4: Access Grafana

1. Open http://localhost:3002 in your browser
2. Login with:
   - **Username:** admin
   - **Password:** admin
3. Change the password when prompted (or skip for development)

## Step 5: Explore Metrics

### In Prometheus

1. Go to http://localhost:9090
2. Click the **Graph** tab
3. Try these queries:

**Total requests per second:**
```
sum(rate(http_requests_total[1m]))
```

**Average response time:**
```
rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])
```

**Error rate:**
```
sum(rate(http_errors_total[5m])) / sum(rate(http_requests_total[5m])) * 100
```

### In Grafana

1. Go to http://localhost:3002
2. Click **Explore** (compass icon) in the left sidebar
3. Select **Prometheus** datasource
4. Enter the same queries as above
5. Click **Run query**

## Step 6: Create Your First Dashboard

1. In Grafana, click **+ > Dashboard**
2. Click **Add visualization**
3. Select **Prometheus** datasource
4. Enter query: `sum(rate(http_requests_total[1m])) by (service)`
5. Set visualization type to **Time series**
6. Click **Apply**
7. Click **Save dashboard** (disk icon)
8. Name it "EduPilot Overview"

## Common Queries for Monitoring

### Service Health

**Check if all services are up:**
```
up
```

**Services that are down:**
```
up == 0
```

### Performance

**Requests per second by service:**
```
sum(rate(http_requests_total[1m])) by (service)
```

**95th percentile response time:**
```
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

**Slow endpoints (>1 second):**
```
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
```

### Errors

**Error count by service:**
```
sum(rate(http_errors_total[5m])) by (service)
```

**Error rate percentage:**
```
sum(rate(http_errors_total[5m])) / sum(rate(http_requests_total[5m])) * 100
```

**4xx vs 5xx errors:**
```
sum(rate(http_errors_total{status=~"4.."}[5m])) by (service)
sum(rate(http_errors_total{status=~"5.."}[5m])) by (service)
```

### Resources

**Memory usage by container:**
```
container_memory_usage_bytes{name=~"edupilot-.*"} / 1024 / 1024
```

**CPU usage by container:**
```
rate(container_cpu_usage_seconds_total{name=~"edupilot-.*"}[5m]) * 100
```

**Database connections:**
```
pg_stat_database_numbackends{datname="edupilot"}
```

**Redis memory usage:**
```
redis_memory_used_bytes / 1024 / 1024
```

## Troubleshooting

### Prometheus shows targets as "DOWN"

**Check if services are running:**
```bash
docker ps | grep edupilot
```

**Check if /metrics endpoints are accessible:**
```bash
curl http://localhost:5000/metrics  # API Gateway
curl http://localhost:8001/metrics  # AI Agent
curl http://localhost:8002/metrics  # LMS Scraper
curl http://localhost:8003/metrics  # Transcription
curl http://localhost:8004/metrics  # Scheduler
```

**Check Prometheus logs:**
```bash
docker logs edupilot-prometheus
```

### Grafana shows "No data"

**Verify Prometheus datasource:**
1. Go to **Configuration > Data Sources**
2. Click **Prometheus**
3. Click **Test** button
4. Should show "Data source is working"

**Check time range:**
- Make sure the time range selector (top right) is set to "Last 5 minutes" or "Last 15 minutes"
- Services need to be running for a few minutes to generate metrics

### Can't access Prometheus or Grafana

**Check if containers are running:**
```bash
docker ps | grep -E "prometheus|grafana"
```

**Check if ports are available:**
```bash
# Linux/Mac
netstat -an | grep -E "9090|3002"

# Windows
netstat -an | findstr "9090 3002"
```

**Restart monitoring stack:**
```bash
docker-compose -f monitoring/docker-compose.monitoring.yml restart
```

## Next Steps

1. **Create custom dashboards** for your specific needs
2. **Set up alerting** for critical metrics (see README.md)
3. **Import community dashboards** from https://grafana.com/grafana/dashboards/
4. **Configure retention** based on your storage capacity
5. **Review metrics regularly** to understand system behavior

## Stopping Monitoring

```bash
# Stop monitoring infrastructure
docker-compose -f monitoring/docker-compose.monitoring.yml down

# Stop and remove volumes (deletes all metrics data)
docker-compose -f monitoring/docker-compose.monitoring.yml down -v
```

## Getting Help

- See [README.md](./README.md) for detailed documentation
- Check [Prometheus documentation](https://prometheus.io/docs/)
- Check [Grafana documentation](https://grafana.com/docs/)
- Review service logs: `docker logs <container-name>`

## Useful Commands

```bash
# View Prometheus logs
docker logs -f edupilot-prometheus

# View Grafana logs
docker logs -f edupilot-grafana

# Restart Prometheus
docker-compose -f monitoring/docker-compose.monitoring.yml restart prometheus

# Check Prometheus configuration
docker exec edupilot-prometheus promtool check config /etc/prometheus/prometheus.yml

# Query Prometheus API
curl 'http://localhost:9090/api/v1/query?query=up'

# Check Grafana health
curl http://localhost:3002/api/health
```
