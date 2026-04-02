# Centralized Logging - Quick Start Guide

Get the EduPilot centralized logging infrastructure up and running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- At least 2GB of free RAM
- At least 10GB of free disk space

## Step 1: Start the Logging Stack

```bash
# From the project root directory
docker-compose -f docker-compose.yml -f logging/docker-compose.logging.yml up -d
```

This will start:
- ✅ Elasticsearch (log storage)
- ✅ Logstash (log processing)
- ✅ Kibana (log visualization)
- ✅ Filebeat (log shipping)

## Step 2: Wait for Services to be Ready

```bash
# Check if all services are healthy
docker-compose -f logging/docker-compose.logging.yml ps
```

Wait until all services show "healthy" status (may take 1-2 minutes).

## Step 3: Configure Elasticsearch

**Linux/Mac:**
```bash
./logging/scripts/setup-elasticsearch.sh
```

**Windows (PowerShell):**
```powershell
.\logging\scripts\setup-elasticsearch.ps1
```

This configures:
- 30-day log retention policy
- Index template for structured logs
- Initial index for log storage

## Step 4: Access Kibana

1. Open your browser and navigate to: **http://localhost:5601**

2. Click on the menu icon (☰) in the top-left corner

3. Navigate to **Management** → **Stack Management** → **Kibana** → **Index Patterns**

4. Click **Create index pattern**

5. Enter the index pattern: `edupilot-logs-*`

6. Click **Next step**

7. Select `@timestamp` as the time field

8. Click **Create index pattern**

## Step 5: View Your Logs

1. Click on the menu icon (☰) in the top-left corner

2. Navigate to **Analytics** → **Discover**

3. You should now see logs from all EduPilot services!

## Common Searches

Try these searches in the Kibana search bar:

### View all errors
```
level:error
```

### View logs from a specific service
```
service:api-gateway
```

### View logs with a correlation ID
```
correlation_id:"your-correlation-id"
```

### View recent errors in AI Agent
```
service:ai-agent AND level:error AND @timestamp:[now-1h TO now]
```

## Verify Everything is Working

### Check Elasticsearch
```bash
curl http://localhost:9200/_cluster/health?pretty
```

Expected output: `"status" : "green"` or `"yellow"`

### Check Logstash
```bash
curl http://localhost:9600/_node/stats?pretty
```

Expected: JSON response with pipeline statistics

### Check Indices
```bash
curl http://localhost:9200/_cat/indices/edupilot-logs-*?v
```

Expected: List of indices with document counts

## Stopping the Logging Stack

```bash
# Stop all services
docker-compose -f logging/docker-compose.logging.yml down

# Stop and remove volumes (WARNING: deletes all logs)
docker-compose -f logging/docker-compose.logging.yml down -v
```

## Troubleshooting

### Elasticsearch won't start
- **Issue**: Not enough memory
- **Solution**: Increase Docker memory limit to at least 4GB

### No logs appearing in Kibana
- **Issue**: Filebeat not collecting logs
- **Solution**: Check Filebeat logs: `docker logs edupilot-filebeat`

### Kibana shows "No results found"
- **Issue**: Index pattern not created or no logs yet
- **Solution**: 
  1. Verify services are running: `docker-compose ps`
  2. Check if indices exist: `curl http://localhost:9200/_cat/indices?v`
  3. Recreate index pattern in Kibana

### Port conflicts
- **Issue**: Ports 5601, 9200, or 5044 already in use
- **Solution**: Edit `logging/docker-compose.logging.yml` to use different ports

## Next Steps

- Read the full [README.md](./README.md) for advanced configuration
- Create custom Kibana dashboards for your use cases
- Set up alerting for critical errors
- Configure log retention policies

## Need Help?

- Check the [README.md](./README.md) for detailed documentation
- Review Docker logs: `docker logs <container-name>`
- Verify service health: `docker-compose ps`

## Summary

You now have:
- ✅ Centralized log aggregation from all services
- ✅ 30-day automatic log retention
- ✅ Real-time log visualization in Kibana
- ✅ Correlation ID tracking across services
- ✅ Structured log parsing and indexing

Happy logging! 🎉
