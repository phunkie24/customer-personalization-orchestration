# Customer Personalization Orchestrator

## Architecture Overview

A multi-agent system for automated personalized marketing using open-source technologies.

```
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway (FastAPI)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                    Orchestrator Service                      │
│           (Coordinates all agents via REST APIs)             │
└──┬────────┬────────┬────────┬────────┬─────────────────────┘
   │        │        │        │        │
   │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│Agent1│ │Agent2│ │Agent3│ │Agent4│ │Agent5│
│Segmt │ │  RAG │ │MsgGen│ │Comply│ │Exper │
└──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘
   │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼
┌────────────────────────────────────────┐
│         Shared Services Layer          │
│  - Database (PostgreSQL)               │
│  - Vector DB (Qdrant)                  │
│  - Message Queue (RabbitMQ)            │
│  - Redis Cache                         │
└────────────────────────────────────────┘
```

## Agents

### 1. Segmentation Agent (Port 5001)
- ML-based customer segmentation
- 500,000 customer dataset
- K-Means, DBSCAN clustering
- REST API for segment classification

### 2. Content Retrieval Agent (Port 5002)
- RAG-based content retrieval
- 5,000 marketing content pieces
- Qdrant vector database
- Sentence transformers embeddings

### 3. Message Generation Agent (Port 5003)
- LLM-based message generation
- Multiple variants (A/B/C)
- Tone and channel adaptation
- Uses Ollama (local LLM)

### 4. Compliance Agent (Port 5004)
- Content safety checking
- Brand guidelines validation
- Bias and toxicity detection
- Open-source detectors

### 5. Experiment Orchestrator (Port 5005)
- A/B/n testing framework
- Performance tracking
- Analytics dashboard
- ROI measurement

## Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI
- **Database**: PostgreSQL
- **Vector DB**: Qdrant
- **Message Queue**: RabbitMQ
- **Cache**: Redis
- **ML Libraries**: scikit-learn, pandas, numpy
- **LLM**: Ollama (Llama 3 or Mistral)
- **Embeddings**: sentence-transformers
- **Containerization**: Docker & Docker Compose

## Quick Start

```bash
# Clone repository
git clone <repo-url>
cd customer-personalization-orchestrator

# Generate sample data
python scripts/generate_data.py

# Start all services
docker-compose up -d

# Check health
curl http://localhost:8000/health

# Run a full personalization flow
curl -X POST http://localhost:8000/personalize/C12345
```

## Directory Structure

```
.
├── agent1-segmentation/       # Customer segmentation service
├── agent2-content-retrieval/  # RAG content retrieval
├── agent3-message-generation/ # LLM message generation
├── agent4-compliance/         # Safety & compliance
├── agent5-experiment-orchestrator/ # A/B testing
├── orchestrator/              # Main orchestration service
├── shared/                    # Shared utilities
├── data/                      # Generated datasets
├── tests/                     # Integration tests
├── docs/                      # Documentation
└── docker-compose.yml         # Docker orchestration
```

## API Endpoints

### Orchestrator (Port 8000)
- `POST /personalize/{customer_id}` - Full personalization flow
- `GET /health` - Health check
- `GET /metrics` - System metrics

### Agent 1 - Segmentation (Port 5001)
- `POST /segment` - Classify customer
- `GET /segments` - List all segments

### Agent 2 - Content Retrieval (Port 5002)
- `POST /retrieve` - Get relevant content
- `POST /search` - Search content

### Agent 3 - Message Generation (Port 5003)
- `POST /generate` - Generate messages
- `POST /regenerate` - Regenerate variant

### Agent 4 - Compliance (Port 5004)
- `POST /validate` - Validate content
- `GET /rules` - Get compliance rules

### Agent 5 - Experiment (Port 5005)
- `POST /deploy` - Deploy experiment
- `GET /results/{experiment_id}` - Get results

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run individual agent
cd agent1-segmentation
python app.py

# Run tests
pytest tests/

# Generate new data
python scripts/generate_data.py --customers 500000 --content 5000
```

## Deployment

```bash
# Build all images
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Scale agents
docker-compose up -d --scale agent1-segmentation=3

# Stop all
docker-compose down
```

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Load tests
locust -f tests/load_test.py

# Coverage
pytest --cov=. tests/
```

## Monitoring

- Prometheus metrics: http://localhost:9090
- Grafana dashboard: http://localhost:3000
- RabbitMQ management: http://localhost:15672
- Qdrant dashboard: http://localhost:6333/dashboard

## Performance

- Average latency: <200ms per agent
- Throughput: 1000 requests/minute
- Segmentation: 100ms
- Content retrieval: 50ms
- Message generation: 2-5s (LLM dependent)
- Compliance check: 100ms
- Experiment deployment: 50ms

## License

MIT License
