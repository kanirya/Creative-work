# Centralized Logging Deployment Guide

This guide covers deploying the EduPilot centralized logging infrastructure in different environments.

## Table of Contents

- [Development Environment](#development-environment)
- [Production Environment](#production-environment)
- [Cloud Deployment](#cloud-deployment)
- [Security Hardening](#security-hardening)
- [Scaling](#scaling)
- [Monitoring](#monitoring)

## Development Environment

### Quick Setup

```bash
# Start logging infrastructure
make logging-start

# Wait 60 seconds for Elasticsearch to be ready
sleep 60

# Configure Elasticsearch
make logging-setup

# Access Kibana
make kibana
```

### Development Configuration

The default configuration is optimized for development:
- Single-node Elasticsearch cluster
- No security enabled
- Minimal resource allocation (512MB heap)
- All ports exposed for easy access

## Production Environment

### Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available
- At least 50GB disk space for logs
- Firewall configured to restrict access

### Production Deployment Steps

#### 1. Update Environment Variables

Create a `.env` file in the `logging/` directory:

```bash
# Elasticsearch
ES_JAVA_OPTS=-Xms2g -Xmx2g
ELASTICSEARCH_PASSWORD=your-secure-password

# Kibana
KIBANA_ENCRYPTION_KEY=your-32-character-encryption-key

# Logstash
LOGSTASH_JAVA_OPTS=-Xms1g -Xmx1g
```

#### 2. Enable Security

Edit `logging/docker-compose.logging.yml`:

```yaml
elasticsearch:
  environment:
    - xpack.security.enabled=true
    - ELASTIC_PASSWORD=${ELASTICSEARCH_PASSWORD}
    - xpack.security.transport.ssl.enabled=true
    - xpack.security.http.ssl.enabled=true
```

#### 3. Configure TLS/SSL

Generate certificates:

```bash
# Create certificates directory
mkdir -p logging/certs

# Generate CA
docker run --rm -v $(pwd)/logging/certs:/certs \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0 \
  bin/elasticsearch-certutil ca --pem --out /certs/ca.zip

# Extract CA
cd logging/certs && unzip ca.zip && cd ../..

# Generate certificates for Elasticsearch
docker run --rm -v $(pwd)/logging/certs:/certs \
  docker.elastic.co/elasticsearch/elasticsearch:8.11.0 \
  bin/elasticsearch-certutil cert --ca-cert /certs/ca/ca.crt \
  --ca-key /certs/ca/ca.key --pem --out /certs/certs.zip

# Extract certificates
cd logging/certs && unzip certs.zip && cd ../..
```

#### 4. Update Volume Mounts

Add certificate volumes to `docker-compose.logging.yml`:

```yaml
elasticsearch:
  volumes:
    - elasticsearch-data:/usr/share/elasticsearch/data
    - ./certs:/usr/share/elasticsearch/config/certs:ro
```

#### 5. Configure Nginx Reverse Proxy

Add to your nginx configuration:

```nginx
# Kibana
location /kibana/ {
    proxy_pass http://localhost:5601/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Authentication
    auth_basic "Restricted Access";
    auth_basic_user_file /etc/nginx/.htpasswd;
}

# Elasticsearch (restrict to internal network only)
location /elasticsearch/ {
    proxy_pass http://localhost:9200/;
    allow 10.0.0.0/8;
    deny all;
}
```

#### 6. Start Production Stack

```bash
# Start with production configuration
docker-compose -f docker-compose.yml -f logging/docker-compose.logging.yml up -d

# Wait for services to be ready
sleep 60

# Configure Elasticsearch
make logging-setup

# Verify health
make logging-status
```

### Production Checklist

- [ ] Security enabled (xpack.security.enabled=true)
- [ ] TLS/SSL configured for Elasticsearch
- [ ] Strong passwords set for all users
- [ ] Kibana behind authentication (nginx basic auth or SSO)
- [ ] Firewall rules configured
- [ ] Elasticsearch ports not exposed publicly
- [ ] Resource limits configured
- [ ] Backup strategy implemented
- [ ] Monitoring and alerting configured
- [ ] Log retention policy verified (30 days)

## Cloud Deployment

### AWS Deployment

#### Using EC2

1. **Launch EC2 Instance**
   - Instance type: t3.large or larger
   - Storage: 50GB+ EBS volume
   - Security group: Allow ports 5601 (Kibana) from your IP only

2. **Install Docker**
   ```bash
   sudo yum update -y
   sudo yum install -y docker
   sudo service docker start
   sudo usermod -a -G docker ec2-user
   ```

3. **Install Docker Compose**
   ```bash
   sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
   sudo chmod +x /usr/local/bin/docker-compose
   ```

4. **Deploy Logging Stack**
   ```bash
   git clone <your-repo>
   cd edupilot
   make logging-start
   sleep 60
   make logging-setup
   ```

#### Using ECS (Elastic Container Service)

1. Create ECS cluster
2. Create task definitions for each service
3. Configure service discovery
4. Set up Application Load Balancer for Kibana
5. Configure CloudWatch for container logs

#### Using Elastic Cloud

For managed Elasticsearch, Logstash, and Kibana:

1. Sign up for Elastic Cloud: https://cloud.elastic.co/
2. Create deployment
3. Update Logstash configuration to point to cloud endpoint
4. Update Filebeat to ship to cloud Logstash

### Azure Deployment

#### Using Azure Container Instances

```bash
# Create resource group
az group create --name edupilot-logging --location eastus

# Create container instances
az container create \
  --resource-group edupilot-logging \
  --name elasticsearch \
  --image docker.elastic.co/elasticsearch/elasticsearch:8.11.0 \
  --ports 9200 9300 \
  --memory 4 \
  --cpu 2
```

### Google Cloud Deployment

#### Using GKE (Google Kubernetes Engine)

1. Create GKE cluster
2. Deploy using Helm charts
3. Configure persistent volumes
4. Set up Cloud Load Balancer

## Security Hardening

### 1. Enable Authentication

```yaml
# docker-compose.logging.yml
elasticsearch:
  environment:
    - xpack.security.enabled=true
    - ELASTIC_PASSWORD=${ELASTICSEARCH_PASSWORD}
```

### 2. Create User Roles

```bash
# Create read-only user for developers
curl -X POST "http://localhost:9200/_security/user/developer" \
  -H 'Content-Type: application/json' \
  -u elastic:${ELASTICSEARCH_PASSWORD} \
  -d '{
    "password": "developer-password",
    "roles": ["kibana_user", "monitoring_user"],
    "full_name": "Developer User"
  }'
```

### 3. Configure IP Whitelisting

```yaml
# docker-compose.logging.yml
kibana:
  environment:
    - SERVER_PUBLICBASEURL=https://logs.yourdomain.com
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    - ELASTICSEARCH_USERNAME=kibana_system
    - ELASTICSEARCH_PASSWORD=${KIBANA_PASSWORD}
```

### 4. Enable Audit Logging

```yaml
elasticsearch:
  environment:
    - xpack.security.audit.enabled=true
```

### 5. Encrypt Data at Rest

Use encrypted volumes:

```bash
# AWS EBS encryption
aws ec2 create-volume --encrypted --size 50 --availability-zone us-east-1a

# Azure disk encryption
az disk create --resource-group myResourceGroup --name myEncryptedDisk --encryption-type EncryptionAtRestWithPlatformKey
```

## Scaling

### Horizontal Scaling

#### Add Elasticsearch Nodes

```yaml
# docker-compose.logging.yml
elasticsearch-node-2:
  image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
  environment:
    - cluster.name=edupilot-logs
    - discovery.seed_hosts=elasticsearch
    - cluster.initial_master_nodes=edupilot-es-node,edupilot-es-node-2
```

#### Add Logstash Instances

```yaml
logstash-2:
  image: docker.elastic.co/logstash/logstash:8.11.0
  environment:
    - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
```

Configure load balancer to distribute logs across Logstash instances.

### Vertical Scaling

#### Increase Elasticsearch Heap

```yaml
elasticsearch:
  environment:
    - "ES_JAVA_OPTS=-Xms4g -Xmx4g"
```

#### Increase Logstash Workers

```yaml
# logstash/config/logstash.yml
pipeline.workers: 8
pipeline.batch.size: 250
```

### Auto-Scaling (Kubernetes)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: logstash-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: logstash
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Monitoring

### Elasticsearch Monitoring

```bash
# Cluster health
curl http://localhost:9200/_cluster/health?pretty

# Node stats
curl http://localhost:9200/_nodes/stats?pretty

# Index stats
curl http://localhost:9200/_cat/indices?v
```

### Logstash Monitoring

```bash
# Node info
curl http://localhost:9600/_node?pretty

# Pipeline stats
curl http://localhost:9600/_node/stats/pipelines?pretty
```

### Kibana Monitoring

Access monitoring dashboards in Kibana:
1. Navigate to Stack Monitoring
2. View Elasticsearch, Logstash, and Kibana metrics

### External Monitoring

#### Prometheus Integration

```yaml
# Add Elasticsearch exporter
elasticsearch-exporter:
  image: quay.io/prometheuscommunity/elasticsearch-exporter:latest
  command:
    - '--es.uri=http://elasticsearch:9200'
  ports:
    - "9114:9114"
```

#### Grafana Dashboards

Import pre-built dashboards:
- Elasticsearch Overview: Dashboard ID 266
- Logstash Overview: Dashboard ID 12019

## Backup and Disaster Recovery

### Automated Backups

```bash
# Create snapshot repository
curl -X PUT "http://localhost:9200/_snapshot/backup_repo" \
  -H 'Content-Type: application/json' \
  -d '{
    "type": "fs",
    "settings": {
      "location": "/usr/share/elasticsearch/backup",
      "compress": true
    }
  }'

# Create daily snapshot
curl -X PUT "http://localhost:9200/_snapshot/backup_repo/snapshot_$(date +%Y%m%d)" \
  -H 'Content-Type: application/json' \
  -d '{
    "indices": "edupilot-logs-*",
    "ignore_unavailable": true,
    "include_global_state": false
  }'
```

### Restore from Backup

```bash
# List snapshots
curl http://localhost:9200/_snapshot/backup_repo/_all?pretty

# Restore snapshot
curl -X POST "http://localhost:9200/_snapshot/backup_repo/snapshot_20240115/_restore" \
  -H 'Content-Type: application/json' \
  -d '{
    "indices": "edupilot-logs-2024.01.15",
    "ignore_unavailable": true
  }'
```

## Troubleshooting Production Issues

### High Memory Usage

```bash
# Check heap usage
curl http://localhost:9200/_nodes/stats/jvm?pretty

# Reduce heap if needed
ES_JAVA_OPTS=-Xms2g -Xmx2g
```

### Slow Queries

```bash
# Enable slow log
curl -X PUT "http://localhost:9200/edupilot-logs-*/_settings" \
  -H 'Content-Type: application/json' \
  -d '{
    "index.search.slowlog.threshold.query.warn": "10s",
    "index.search.slowlog.threshold.query.info": "5s"
  }'
```

### Disk Space Issues

```bash
# Check disk usage
df -h /var/lib/docker/volumes/

# Force delete old indices
curl -X DELETE "http://localhost:9200/edupilot-logs-2024.01.01"
```

## Performance Tuning

### Elasticsearch

```yaml
# Increase thread pool
elasticsearch:
  environment:
    - thread_pool.write.queue_size=1000
    - thread_pool.search.queue_size=1000
```

### Logstash

```yaml
# Optimize pipeline
pipeline.workers: 4
pipeline.batch.size: 250
pipeline.batch.delay: 50
```

### Filebeat

```yaml
# Increase bulk size
output.logstash:
  bulk_max_size: 2048
  worker: 2
```

## Cost Optimization

### Reduce Storage Costs

1. **Decrease retention period** (if acceptable):
   ```json
   "delete": {
     "min_age": "14d"
   }
   ```

2. **Enable compression**:
   ```json
   "index.codec": "best_compression"
   ```

3. **Use cold/frozen tiers** for old data

### Reduce Compute Costs

1. **Right-size instances** based on actual usage
2. **Use spot instances** for non-critical environments
3. **Scale down during off-hours**

## Compliance

### GDPR Compliance

- Implement data retention policies
- Enable audit logging
- Provide data export capabilities
- Implement right to be forgotten

### HIPAA Compliance

- Enable encryption at rest and in transit
- Implement access controls
- Enable audit logging
- Regular security assessments

## Support and Maintenance

### Regular Maintenance Tasks

- [ ] Weekly: Review disk usage
- [ ] Weekly: Check for failed indices
- [ ] Monthly: Review and optimize queries
- [ ] Monthly: Update Elastic Stack versions
- [ ] Quarterly: Review retention policies
- [ ] Quarterly: Security audit

### Upgrade Procedure

1. Backup all data
2. Test upgrade in staging
3. Upgrade Elasticsearch first
4. Upgrade Kibana
5. Upgrade Logstash
6. Upgrade Filebeat
7. Verify all services

## Additional Resources

- [Elastic Stack Documentation](https://www.elastic.co/guide/)
- [Production Best Practices](https://www.elastic.co/guide/en/elasticsearch/reference/current/setup.html)
- [Security Best Practices](https://www.elastic.co/guide/en/elasticsearch/reference/current/security-settings.html)
- [Performance Tuning](https://www.elastic.co/guide/en/elasticsearch/reference/current/tune-for-indexing-speed.html)
