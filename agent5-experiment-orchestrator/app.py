"""
Agent 5: Experiment Orchestrator (Fixed)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime
import random
import uuid

from shared.models import HealthCheck
from shared.utils import setup_logging, timing_decorator

app = FastAPI(title="Experiment Orchestrator", version="1.0.0")
logger = setup_logging("experiment-orchestrator-agent")

class ExperimentConfig(BaseModel):
    experiment_name: str
    experiment_type: str = "ab_test"
    sample_size: int = 1000
    duration_days: int = 7
    success_metrics: List[str] = ["conversion_rate"]

class MessageVariant(BaseModel):
    variant_id: str
    message_text: str
    tone: str
    channel: str

class DeployRequest(BaseModel):
    experiment_config: ExperimentConfig
    message_variants: List[MessageVariant]
    customer_id: str
    segment_id: str

class DeployResponse(BaseModel):
    experiment_id: str
    assigned_variant: str
    variant_details: MessageVariant
    status: str
    timestamp: datetime

# In-memory storage
experiments = {}
metrics = {}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Experiment Orchestrator Agent...")
    logger.info("Experiment Orchestrator Agent ready!")

@app.get("/", response_model=HealthCheck)
async def root():
    return HealthCheck(
        service_name="experiment-orchestrator-agent",
        status="healthy",
        version="1.0.0"
    )

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        service_name="experiment-orchestrator-agent",
        status="healthy",
        version="1.0.0"
    )

@app.post("/deploy", response_model=DeployResponse)
@timing_decorator
async def deploy_experiment(request: DeployRequest):
    try:
        logger.info(f"Deploying experiment for customer {request.customer_id}")
        
        # Generate experiment ID
        experiment_id = f"EXP_{uuid.uuid4().hex[:8].upper()}"
        
        # Randomly assign variant
        assigned_variant = random.choice([v.variant_id for v in request.message_variants])
        variant = next(v for v in request.message_variants if v.variant_id == assigned_variant)
        
        # Store experiment
        experiments[experiment_id] = {
            "config": request.experiment_config.dict(),
            "variants": [v.dict() for v in request.message_variants],
            "customer_id": request.customer_id,
            "segment_id": request.segment_id,
            "assigned_variant": assigned_variant,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Initialize metrics
        metrics[experiment_id] = {
            "impressions": 1,
            "clicks": 0,
            "conversions": 0
        }
        
        response = DeployResponse(
            experiment_id=experiment_id,
            assigned_variant=assigned_variant,
            variant_details=variant,
            status="deployed",
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Experiment {experiment_id} deployed with variant {assigned_variant}")
        return response
        
    except Exception as e:
        logger.error(f"Deployment error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/results/{experiment_id}")
async def get_results(experiment_id: str):
    try:
        if experiment_id not in experiments:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        experiment = experiments[experiment_id]
        experiment_metrics = metrics.get(experiment_id, {})
        
        # Simulate some metrics
        impressions = experiment_metrics.get("impressions", 1)
        clicks = random.randint(0, impressions)
        conversions = random.randint(0, clicks)
        
        return {
            "experiment_id": experiment_id,
            "status": "running",
            "metrics": {
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "click_rate": clicks / impressions if impressions > 0 else 0,
                "conversion_rate": conversions / clicks if clicks > 0 else 0
            },
            "config": experiment["config"],
            "assigned_variant": experiment["assigned_variant"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Results error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/experiments")
async def list_experiments():
    return {
        "experiments": list(experiments.keys()),
        "total": len(experiments)
    }

@app.post("/record-event")
async def record_event(experiment_id: str, event_type: str):
    try:
        if experiment_id not in metrics:
            metrics[experiment_id] = {"impressions": 0, "clicks": 0, "conversions": 0}
        
        if event_type in metrics[experiment_id]:
            metrics[experiment_id][event_type] += 1
        
        return {"status": "recorded", "experiment_id": experiment_id, "event_type": event_type}
        
    except Exception as e:
        logger.error(f"Event recording error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5005)
