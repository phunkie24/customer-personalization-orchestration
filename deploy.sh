#!/bin/bash

# Customer Personalization Orchestrator - Deployment Script
# This script builds and deploys all services using Docker Compose

set -e  # Exit on error

echo "============================================================"
echo "Customer Personalization Orchestrator - Deployment"
echo "============================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    exit 1
fi

# Generate data if not exists
if [ ! -f "data/customers.csv" ]; then
    echo -e "${YELLOW}Generating sample data...${NC}"
    python scripts/generate_data.py
    echo -e "${GREEN}✓ Data generated${NC}"
else
    echo -e "${GREEN}✓ Data already exists${NC}"
fi

# Stop any existing containers
echo ""
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose down

# Build images
echo ""
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose build

# Start infrastructure services first
echo ""
echo -e "${YELLOW}Starting infrastructure services...${NC}"
docker-compose up -d postgres redis qdrant rabbitmq ollama

# Wait for infrastructure to be healthy
echo ""
echo -e "${YELLOW}Waiting for infrastructure services to be healthy...${NC}"
sleep 10

# Check postgres
echo -n "Checking PostgreSQL... "
for i in {1..30}; do
    if docker-compose exec -T postgres pg_isready -U user > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 1
done

# Check redis
echo -n "Checking Redis... "
for i in {1..30}; do
    if docker-compose exec -T redis redis-cli ping > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 1
done

# Check qdrant
echo -n "Checking Qdrant... "
for i in {1..30}; do
    if curl -s http://localhost:6333/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 1
done

# Pull Ollama model
echo ""
echo -e "${YELLOW}Pulling Ollama model (this may take a few minutes)...${NC}"
docker-compose exec -T ollama ollama pull llama3 || echo -e "${YELLOW}Warning: Could not pull llama3 model. Message generation will use templates.${NC}"

# Start agent services
echo ""
echo -e "${YELLOW}Starting agent services...${NC}"
docker-compose up -d agent1-segmentation agent2-content-retrieval agent3-message-generation agent4-compliance agent5-experiment-orchestrator

# Wait for agents to be ready
echo ""
echo -e "${YELLOW}Waiting for agents to be ready...${NC}"
sleep 20

# Check agents
for agent in agent1-segmentation agent2-content-retrieval agent3-message-generation agent4-compliance agent5-experiment-orchestrator; do
    port=""
    case $agent in
        agent1-segmentation) port=5001 ;;
        agent2-content-retrieval) port=5002 ;;
        agent3-message-generation) port=5003 ;;
        agent4-compliance) port=5004 ;;
        agent5-experiment-orchestrator) port=5005 ;;
    esac
    
    echo -n "Checking $agent... "
    for i in {1..60}; do
        if curl -s http://localhost:$port/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC}"
            break
        fi
        if [ $i -eq 60 ]; then
            echo -e "${RED}✗ Timeout${NC}"
        fi
        sleep 1
    done
done

# Start orchestrator
echo ""
echo -e "${YELLOW}Starting orchestrator...${NC}"
docker-compose up -d orchestrator

# Wait for orchestrator
echo -n "Checking orchestrator... "
sleep 10
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        break
    fi
    sleep 1
done

# Show status
echo ""
echo "============================================================"
echo -e "${GREEN}Deployment Complete!${NC}"
echo "============================================================"
echo ""
echo "Services:"
echo "  • Orchestrator:        http://localhost:8000"
echo "  • Segmentation:        http://localhost:5001"
echo "  • Content Retrieval:   http://localhost:5002"
echo "  • Message Generation:  http://localhost:5003"
echo "  • Compliance:          http://localhost:5004"
echo "  • Experiment:          http://localhost:5005"
echo ""
echo "Infrastructure:"
echo "  • PostgreSQL:          localhost:5432"
echo "  • Redis:               localhost:6379"
echo "  • Qdrant:              http://localhost:6333"
echo "  • RabbitMQ:            http://localhost:15672"
echo "  • Ollama:              http://localhost:11434"
echo ""
echo "To test the system:"
echo "  curl -X POST http://localhost:8000/personalize/C00000001"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"
echo ""
echo "To stop all services:"
echo "  docker-compose down"
echo ""
