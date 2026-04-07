# EduPilot Deployment Checklist

## Pre-Deployment Security Checklist

### Authentication & Authorization
- [ ] JWT secret key is at least 256 bits and stored in secrets manager (not in code)
- [ ] JWT token expiry is set to 1 hour (access) and 7 days (refresh)
- [ ] All API endpoints require authentication except `/health`, `/auth/login`, `/auth/register`
- [ ] RBAC roles are correctly assigned (Student, Instructor, Admin)
- [ ] CORS origins are restricted to known client domains

### Data Security
- [ ] All database connections use TLS
- [ ] PostgreSQL password is strong and rotated
- [ ] Redis is password-protected and not exposed publicly
- [ ] Sensitive fields (passwords, credentials) are encrypted at rest
- [ ] LMS credentials are stored encrypted, never in plain text logs
- [ ] FERPA audit logging is enabled for all student data access

### Network Security
- [ ] TLS 1.3 is enforced on all public endpoints
- [ ] SSL certificates are valid and auto-renewal is configured
- [ ] nginx rate limiting is active (100 req/min API, 10 req/min auth)
- [ ] All services communicate over internal Docker network only
- [ ] No services expose ports directly to the internet except nginx (80/443)

### Secrets Management
- [ ] All secrets are in environment variables or secrets manager
- [ ] `.env` files are not committed to git
- [ ] Docker secrets or Kubernetes secrets are used in production
- [ ] API keys (OpenAI, etc.) are rotated regularly

---

## Uptime Requirements

| Service | Target Uptime | Max Downtime/Month |
|---------|--------------|-------------------|
| API Gateway | 99.9% | 43 minutes |
| Web App | 99.9% | 43 minutes |
| LMS Scraper | 99.5% | 3.6 hours |
| AI Agent | 99.5% | 3.6 hours |
| Database | 99.99% | 4 minutes |

### Health Check Endpoints
- API Gateway: `GET /health`
- LMS Scraper: `GET /health`
- AI Agent: `GET /health`
- Transcription: `GET /health`
- Scheduler: `GET /health`

---

## Monitoring Setup

### Prometheus Metrics
- All services expose `/metrics` endpoint
- Prometheus scrapes every 15 seconds
- Key metrics: `http_request_duration_seconds`, `http_requests_total`, `process_cpu_seconds_total`

### Grafana Dashboards
- System Health: CPU, memory, disk per service
- API Performance: p50/p95/p99 response times, error rates
- Business Metrics: active students, queries/day, scraping success rate

### Alerting Rules (Alertmanager)
- Error rate > 5% for 5 minutes → PagerDuty + email
- Response time p95 > 10 seconds → email
- Service down > 1 minute → PagerDuty
- Disk usage > 80% → email
- Scraping failures 3 consecutive times → email to admin

### Log Aggregation
- All services ship logs to centralized logging (ELK/Loki)
- Log retention: 30 days
- Structured JSON logging with correlation IDs
- Security events logged separately with 90-day retention

---

## Deployment Steps

1. Run all tests: `bash scripts/run_all_tests.sh`
2. Build Docker images: `docker-compose build`
3. Push to registry: `docker-compose push`
4. Run database migrations: `docker-compose exec postgres psql -U postgres -d edupilot -f /migrations/004_add_performance_indexes.sql`
5. Deploy with rolling update: `docker-compose up --no-deps --build -d api-gateway`
6. Verify health checks pass
7. Monitor error rates for 15 minutes post-deployment
8. Tag release in git: `git tag v1.x.x`

---

## Rollback Procedure

If deployment fails:
1. `docker-compose up -d --no-deps api-gateway:previous-tag`
2. Verify health checks
3. Investigate failure in logs: `docker-compose logs api-gateway --tail=100`
