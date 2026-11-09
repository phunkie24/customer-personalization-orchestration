# Quick Start Guide

## Prerequisites

- Docker 20.10+
- Docker Compose 1.29+
- Python 3.11+ (for data generation)
- 8GB RAM minimum
- 20GB disk space

## Installation Steps

### 1. Clone or Extract Repository

```bash
cd customer-personalization-orchestrator
```

### 2. Generate Sample Data

```bash
python scripts/generate_data.py
```

This will generate:
- 500,000 customer records
- 5,000 marketing content pieces
- 100 historical experiments

### 3. Deploy All Services

```bash
./deploy.sh
```

This script will:
- Build all Docker images
- Start infrastructure services (PostgreSQL, Redis, Qdrant, RabbitMQ, Ollama)
- Wait for services to be healthy
- Start all 5 agents
- Start the orchestrator
- Perform health checks

Deployment takes approximately 5-10 minutes.

### 4. Verify Deployment

Check that all services are running:

```bash
docker-compose ps
```

All services should show "Up" and "healthy" status.

### 5. Test the System

#### Individual Agent Tests

```bash
# Test Segmentation Agent
curl -X POST http://localhost:5001/segment \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"C00000001"}'

# Test Content Retrieval Agent
curl http://localhost:5002/search?query=smartphone&top_k=3

# Test Message Generation (requires segment data)
curl http://localhost:5003/health

# Test Compliance Agent
curl http://localhost:5004/rules

# Test Experiment Orchestrator
curl http://localhost:5005/experiments
```

#### End-to-End Test

```bash
# Run full personalization flow
curl -X POST "http://localhost:8000/personalize/C00000001?channel=email"
```

Expected response includes:
- Customer segment
- Retrieved content
- Generated message variants
- Compliance validation
- Experiment assignment

#### Run Integration Tests

```bash
# Install test dependencies
pip install pytest httpx

# Run tests
pytest tests/test_integration.py -v
```

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Orchestrator | http://localhost:8000 | Main entry point |
| Agent 1 - Segmentation | http://localhost:5001 | Customer segmentation |
| Agent 2 - Content Retrieval | http://localhost:5002 | RAG-based content |
| Agent 3 - Message Generation | http://localhost:5003 | LLM message gen |
| Agent 4 - Compliance | http://localhost:5004 | Safety validation |
| Agent 5 - Experiment | http://localhost:5005 | A/B testing |
| PostgreSQL | localhost:5432 | Database |
| Redis | localhost:6379 | Cache |
| Qdrant | http://localhost:6333 | Vector DB |
| RabbitMQ Admin | http://localhost:15672 | Message queue |
| Ollama | http://localhost:11434 | LLM service |

## API Examples

### 1. Personalize for a Customer

```bash
curl -X POST "http://localhost:8000/personalize/C00000001" \
  -H "Content-Type: application/json"
```

### 2. Get Segment Information

```bash
curl -X POST http://localhost:5001/segment \
  -H "Content-Type: application/json" \
  -d '{"customer_id":"C00000001"}'
```

### 3. Search Content

```bash
curl "http://localhost:5002/search?query=premium+products&top_k=5"
```

### 4. Get Experiment Results

```bash
curl "http://localhost:5005/results/EXP001"
```

### 5. Check System Health

```bash
curl http://localhost:8000/agents/health
```

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f agent1-segmentation

# Last 100 lines
docker-compose logs --tail=100
```

### Check Container Status

```bash
docker-compose ps
```

### View Resource Usage

```bash
docker stats
```

## Troubleshooting

### Service Not Starting

```bash
# Check logs
docker-compose logs <service-name>

# Restart service
docker-compose restart <service-name>
```

### Out of Memory

```bash
# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory

# Or scale down agents
docker-compose up -d --scale agent1-segmentation=1
```

### Slow Performance

1. Ensure Ollama model is downloaded:
```bash
docker-compose exec ollama ollama list
```

2. Check database connections:
```bash
docker-compose exec postgres psql -U user -d personalization -c "SELECT 1"
```

3. Verify Qdrant is indexed:
```bash
curl http://localhost:6333/collections/marketing_content
```

### Reset Everything

```bash
# Stop and remove all containers, networks, volumes
docker-compose down -v

# Remove images
docker-compose rm -f

# Rebuild
./deploy.sh
```

## Scaling

### Scale Individual Agents

```bash
# Scale segmentation agent to 3 instances
docker-compose up -d --scale agent1-segmentation=3

# Scale content retrieval to 2 instances
docker-compose up -d --scale agent2-content-retrieval=2
```

### Add Load Balancer

For production, add Nginx or HAProxy in front of agents.

## Development

### Run Single Agent Locally

```bash
cd agent1-segmentation
python app.py
```

### Modify Agent Code

1. Edit agent code
2. Rebuild specific service:
```bash
docker-compose build agent1-segmentation
docker-compose up -d agent1-segmentation
```

### Add New Features

1. Update agent code
2. Update shared models if needed
3. Rebuild and restart
4. Run tests

## Production Considerations

1. **Security**:
   - Change default passwords
   - Use secrets management
   - Enable SSL/TLS
   - Implement authentication

2. **Monitoring**:
   - Add Prometheus + Grafana
   - Set up alerts
   - Log aggregation (ELK stack)

3. **Performance**:
   - Use production WSGI server
   - Enable caching
   - Optimize database indexes
   - Use CDN for static assets

4. **Reliability**:
   - Implement circuit breakers
   - Add retry logic
   - Set up health checks
   - Use message queues for async tasks

## Support

For issues or questions:
1. Check logs: `docker-compose logs`
2. Verify service health: `curl http://localhost:8000/agents/health`
3. Run integration tests: `pytest tests/`
4. Check data files exist in `./data/`

## Stopping the System

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove everything including volumes
docker-compose down -v
```
