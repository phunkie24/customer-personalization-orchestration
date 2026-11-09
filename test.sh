#!/bin/bash

# Simple test script for Customer Personalization Orchestrator

echo "============================================================"
echo "Customer Personalization Orchestrator - Quick Test"
echo "============================================================"
echo ""

# Check if services are running
echo "Checking service health..."
echo ""

# Test orchestrator
echo -n "Orchestrator: "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Healthy"
else
    echo "✗ Not responding"
    exit 1
fi

# Test agents
for i in 1 2 3 4 5; do
    port=$((5000 + i))
    agent_name="Agent $i"
    echo -n "$agent_name: "
    if curl -s http://localhost:$port/health > /dev/null 2>&1; then
        echo "✓ Healthy"
    else
        echo "✗ Not responding"
    fi
done

echo ""
echo "Running end-to-end test..."
echo ""

# Test personalization
customer_id="C00000001"
echo "Personalizing for customer: $customer_id"

response=$(curl -s -X POST "http://localhost:8000/personalize/$customer_id?channel=email")

if [ $? -eq 0 ]; then
    echo "✓ Personalization successful"
    echo ""
    echo "Response summary:"
    echo "$response" | python3 -m json.tool 2>/dev/null | grep -E "(customer_id|segment_id|total_retrieved|processing_time_ms|experiment_id)" | head -10
    echo ""
else
    echo "✗ Personalization failed"
    exit 1
fi

echo ""
echo "Testing multiple customers..."
for customer_id in "C00000001" "C00000100" "C00000500"; do
    echo -n "Testing $customer_id... "
    response=$(curl -s -X POST "http://localhost:8000/personalize/$customer_id?channel=email")
    if [ $? -eq 0 ]; then
        echo "✓"
    else
        echo "✗"
    fi
done

echo ""
echo "============================================================"
echo "Tests Complete!"
echo "============================================================"
echo ""
echo "Full API documentation: http://localhost:8000/docs"
echo "View logs: docker-compose logs -f"
