# System Architecture

## Overview

The Customer Personalization Orchestrator is a microservices-based system that uses 5 specialized AI agents to deliver personalized marketing messages at scale.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                             │
│                    (API Clients, UI, etc.)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/REST
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    API Gateway (Port 8000)                       │
│                        Orchestrator                              │
│           Routes requests to appropriate agents                  │
└──┬────────┬────────┬────────┬────────┬─────────────────────────┘
   │        │        │        │        │
   │        │        │        │        │ HTTP/REST APIs
   ▼        ▼        ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Agent1│ │Agent2│ │Agent3│ │Agent4│ │Agent5│
│5001  │ │5002  │ │5003  │ │5004  │ │5005  │
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
   │        │        │        │        │
   │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼
┌────────────────────────────────────────────┐
│         Infrastructure Layer                │
│  ┌──────────┐  ┌────────┐  ┌───────────┐  │
│  │PostgreSQL│  │Qdrant  │  │  Ollama   │  │
│  │  (DB)    │  │(Vector)│  │   (LLM)   │  │
│  └──────────┘  └────────┘  └───────────┘  │
│  ┌──────────┐  ┌────────┐                 │
│  │  Redis   │  │RabbitMQ│                 │
│  │ (Cache)  │  │ (Queue)│                 │
│  └──────────┘  └────────┘                 │
└────────────────────────────────────────────┘
```

## Agent Details

### Agent 1: Customer Segmentation (Port 5001)

**Purpose**: Classify customers into meaningful segments using ML

**Technology Stack**:
- scikit-learn (K-Means, DBSCAN)
- pandas, numpy
- PostgreSQL for customer data
- PCA for dimensionality reduction

**Key Features**:
- Loads 500,000 customer records
- 8 distinct customer segments
- Real-time prediction with confidence scores
- Automatic model retraining

**API Endpoints**:
- `POST /segment` - Classify a customer
- `GET /segments` - List all segments
- `POST /retrain` - Retrain the model

**Data Model**:
```python
Input: customer_id
Features: age, income, purchase_frequency, AOV, LTV, recency, engagement
Output: segment_id, segment_type, confidence, profile
```

### Agent 2: Content Retrieval (Port 5002)

**Purpose**: Retrieve relevant marketing content using RAG

**Technology Stack**:
- Qdrant (vector database)
- sentence-transformers (embeddings)
- Semantic search with cosine similarity

**Key Features**:
- 5,000 indexed marketing content pieces
- Vector embeddings for semantic search
- Compliance-filtered results
- Real-time retrieval (<50ms)

**API Endpoints**:
- `POST /retrieve` - Get content for segment
- `POST /search` - Direct content search
- `POST /reindex` - Reindex all content

**Data Flow**:
```
Segment Profile → Query Embedding → Vector Search → Top-K Results → Filter by Compliance
```

### Agent 3: Message Generation (Port 5003)

**Purpose**: Generate personalized message variants using LLM

**Technology Stack**:
- Ollama (local LLM - Llama 3)
- Template-based fallback
- Multi-tone generation

**Key Features**:
- 2-5 second generation time
- Multiple variants (A/B/C testing)
- Tone adaptation (professional, casual, friendly, urgent)
- Channel-specific formatting (email, SMS, push)

**API Endpoints**:
- `POST /generate` - Generate message variants
- `POST /regenerate` - Regenerate specific variant

**Prompt Engineering**:
```
Context: Segment profile + Content snippets
Instructions: Tone, channel, length, CTA requirements
Output: Personalized message variants
```

### Agent 4: Compliance & Safety (Port 5004)

**Purpose**: Validate messages for safety and compliance

**Technology Stack**:
- Rule-based validation
- Pattern matching (regex)
- Multi-layer checks

**Validation Rules**:
1. **Content Safety** (Critical)
   - No profanity
   - No discriminatory language
   - No spam indicators

2. **Brand Compliance** (High)
   - Brand voice consistency
   - No false claims
   - Tone appropriateness

3. **Technical** (Medium)
   - Character limits by channel
   - Required disclaimers

**API Endpoints**:
- `POST /validate` - Validate messages
- `GET /rules` - Get compliance rules
- `GET /banned-words` - Get banned word list

**Output**:
- Pass/fail per variant
- Risk score
- Detailed recommendations

### Agent 5: Experiment Orchestrator (Port 5005)

**Purpose**: Deploy and track A/B/n experiments

**Technology Stack**:
- PostgreSQL for experiment data
- Redis for real-time metrics
- Statistical analysis

**Key Features**:
- Random variant assignment
- Real-time metrics tracking
- Winner determination with confidence
- ROI calculation

**API Endpoints**:
- `POST /deploy` - Deploy experiment
- `GET /results/{id}` - Get experiment results
- `GET /experiments` - List active experiments
- `POST /record-event` - Track interaction

**Metrics Tracked**:
- Impressions
- Click-through rate (CTR)
- Conversion rate
- Revenue per variant
- Return on investment (ROI)

## Orchestrator

**Purpose**: Coordinate all agents for end-to-end personalization

**Flow**:
```
1. Receive customer_id + channel
2. Call Agent 1: Segment customer
3. Call Agent 2: Retrieve content for segment
4. Call Agent 3: Generate message variants
5. Call Agent 4: Validate compliance
6. Call Agent 5: Deploy experiment
7. Return complete response
```

**Error Handling**:
- Retry logic (3 attempts)
- Circuit breaker pattern
- Graceful degradation
- Detailed error logging

**Performance**:
- Average latency: <2 seconds
- Parallel agent calls where possible
- Caching of frequent requests

## Data Flow

### Complete Personalization Flow

```
Customer ID
    ↓
[Agent 1: Segmentation]
    ↓
Segment Profile
    ↓
[Agent 2: Content Retrieval]
    ↓
Relevant Content
    ↓
[Agent 3: Message Generation]
    ↓
Message Variants (A, B, C)
    ↓
[Agent 4: Compliance]
    ↓
Approved Variants
    ↓
[Agent 5: Experiment]
    ↓
Deployed Message + Tracking
```

## Infrastructure Components

### PostgreSQL
- **Purpose**: Relational data storage
- **Stores**: Customer data, experiment results, assignments
- **Port**: 5432
- **Schema**: Normalized with indexes on customer_id, experiment_id

### Redis
- **Purpose**: Caching and session storage
- **Caches**: Segment predictions, content results
- **Port**: 6379
- **TTL**: Configurable (default 1 hour)

### Qdrant
- **Purpose**: Vector database for semantic search
- **Stores**: Content embeddings (384 dimensions)
- **Port**: 6333
- **Distance**: Cosine similarity

### RabbitMQ
- **Purpose**: Message queue for async tasks
- **Use Cases**: Event tracking, batch processing
- **Port**: 5672, 15672 (management)

### Ollama
- **Purpose**: Local LLM inference
- **Model**: Llama 3 (7B parameters)
- **Port**: 11434
- **Fallback**: Template-based generation

## Scalability

### Horizontal Scaling
```bash
# Scale specific agents
docker-compose up -d --scale agent1-segmentation=3
docker-compose up -d --scale agent2-content-retrieval=2
```

### Load Balancing
- Add Nginx/HAProxy in front of agents
- Round-robin distribution
- Health check integration

### Database Optimization
- Read replicas for PostgreSQL
- Redis cluster for distributed caching
- Qdrant sharding for large datasets

### Performance Targets
- **Throughput**: 1000 requests/minute
- **Latency**: P95 < 2 seconds
- **Availability**: 99.9% uptime

## Security

### Network Security
- Internal Docker network
- Exposed ports: Only 8000 (orchestrator)
- TLS/SSL for production

### Data Security
- Environment variables for secrets
- No sensitive data in logs
- Encrypted database connections

### API Security
- Rate limiting
- API key authentication (production)
- Input validation

## Monitoring

### Health Checks
All services expose `/health` endpoint:
```json
{
  "service_name": "agent1-segmentation",
  "status": "healthy",
  "version": "1.0.0",
  "dependencies": {...}
}
```

### Metrics
- Request count
- Latency (P50, P95, P99)
- Error rate
- Agent-specific metrics

### Logging
- Structured JSON logs
- Log levels: INFO, WARNING, ERROR
- Centralized log aggregation (recommended)

## Deployment Strategies

### Development
```bash
docker-compose up -d
```

### Production
- Use orchestration (Kubernetes)
- Implement CI/CD pipeline
- Blue-green deployment
- Canary releases

## Disaster Recovery

### Backup Strategy
- Daily PostgreSQL backups
- Qdrant collection snapshots
- Configuration version control

### Recovery Plan
1. Restore database from backup
2. Rebuild Qdrant index
3. Restart services
4. Verify health checks

## Technology Choices Rationale

1. **FastAPI**: Modern, async, auto-documentation
2. **Docker**: Consistent environments, easy deployment
3. **PostgreSQL**: Reliable, ACID compliance, rich features
4. **Qdrant**: Fast vector search, easy integration
5. **Ollama**: Local LLM, no API costs, privacy
6. **scikit-learn**: Mature ML library, well-documented

## Future Enhancements

1. **ML Improvements**
   - Deep learning for segmentation
   - Fine-tuned LLMs
   - Reinforcement learning for optimization

2. **Features**
   - Multi-language support
   - Real-time personalization
   - Advanced A/B testing (multi-armed bandit)

3. **Scale**
   - Kubernetes deployment
   - Multi-region support
   - CDN integration

4. **Analytics**
   - Advanced reporting dashboard
   - Predictive analytics
   - Customer journey mapping
