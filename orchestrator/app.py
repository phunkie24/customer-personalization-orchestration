# Databricks notebook source
"""
Main Orchestrator Service
Coordinates all 5 agents to provide end-to-end personalization
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import time
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.models import (
    PersonalizationRequest, PersonalizationResponse,
    SegmentationRequest, ContentRetrievalRequest,
    MessageGenerationRequest, ComplianceValidationRequest,
    ExperimentDeployRequest, HealthCheck, Channel
)
from shared.utils import setup_logging, timing_decorator, Config, retry

# Initialize FastAPI app
app = FastAPI(
    title="Customer Personalization Orchestrator",
    description="Main orchestration service for multi-agent personalization",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logger = setup_logging("orchestrator")


class OrchestratorService:
    """Main orchestration service"""
    
    def __init__(self):
        self.segmentation_url = Config.SEGMENTATION_URL
        self.content_url = Config.CONTENT_RETRIEVAL_URL
        self.message_gen_url = Config.MESSAGE_GENERATION_URL
        self.compliance_url = Config.COMPLIANCE_URL
        self.experiment_url = Config.EXPERIMENT_URL
        
    @retry(max_attempts=3, delay=1.0)
    async def call_agent(self, url: str, endpoint: str, data: dict = None):
        """Call an agent service"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            full_url = f"{url}{endpoint}"
            
            if data:
                response = await client.post(full_url, json=data)
            else:
                response = await client.get(full_url)
            
            response.raise_for_status()
            return response.json()
    
    async def health_check_agents(self) -> dict:
        """Check health of all agents"""
        agents = {
            "segmentation": self.segmentation_url,
            "content_retrieval": self.content_url,
            "message_generation": self.message_gen_url,
            "compliance": self.compliance_url,
            "experiment": self.experiment_url
        }
        
        health_status = {}
        
        for name, url in agents.items():
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    response = await client.get(f"{url}/health")
                    health_status[name] = "healthy" if response.status_code == 200 else "unhealthy"
            except Exception as e:
                logger.error(f"Health check failed for {name}: {e}")
                health_status[name] = "unhealthy"
        
        return health_status
    
    async def orchestrate_personalization(
        self,
        customer_id: str,
        channel: Channel
    ) -> PersonalizationResponse:
        """Orchestrate the full personalization flow"""
        
        start_time = time.time()
        
        # Step 1: Segment Customer
        logger.info(f"[1/5] Segmenting customer {customer_id}")
        segmentation_request = SegmentationRequest(customer_id=customer_id)
        segmentation_response = await self.call_agent(
            self.segmentation_url,
            "/segment",
            segmentation_request.dict()
        )
        logger.info(f"✓ Customer assigned to segment: {segmentation_response['segment_id']}")
        
        # Step 2: Retrieve Content
        logger.info(f"[2/5] Retrieving content for segment {segmentation_response['segment_id']}")
        content_request = ContentRetrievalRequest(
            segment=segmentation_response['segment_profile'],
            top_k=3
        )
        content_response = await self.call_agent(
            self.content_url,
            "/retrieve",
            content_request.dict()
        )
        logger.info(f"✓ Retrieved {content_response['total_retrieved']} content pieces")
        
        # Step 3: Generate Messages
        logger.info(f"[3/5] Generating personalized messages")
        message_gen_request = MessageGenerationRequest(
            segment=segmentation_response['segment_profile'],
            content=content_response,
            channel=channel,
            num_variants=3
        )
        message_response = await self.call_agent(
            self.message_gen_url,
            "/generate",
            message_gen_request.dict()
        )
        logger.info(f"✓ Generated {len(message_response['variants'])} message variants")
        
        # Step 4: Validate Compliance
        logger.info(f"[4/5] Validating compliance")
        compliance_request = ComplianceValidationRequest(
            messages=message_response
        )
        compliance_response = await self.call_agent(
            self.compliance_url,
            "/validate",
            compliance_request.dict()
        )
        approved_count = len(compliance_response['approved_variants'])
        logger.info(f"✓ {approved_count} variants approved")
        
        # Step 5: Deploy Experiment
        logger.info(f"[5/5] Deploying A/B/n experiment")
        experiment_request = ExperimentDeployRequest(
            customer_id=customer_id,
            messages=compliance_response
        )
        experiment_response = await self.call_agent(
            self.experiment_url,
            "/deploy",
            experiment_request.dict()
        )
        logger.info(f"✓ Experiment {experiment_response['experiment_id']} deployed")
        
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000
        
        # Build response
        response = PersonalizationResponse(
            customer_id=customer_id,
            segment=segmentation_response,
            content=content_response,
            messages=message_response,
            compliance=compliance_response,
            experiment=experiment_response,
            processing_time_ms=processing_time_ms,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f" Personalization complete in {processing_time_ms:.0f}ms")
        return response


# Initialize service
service = OrchestratorService()


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Starting Main Orchestrator...")
    logger.info("Checking agent health...")
    
    health = await service.health_check_agents()
    for agent, status in health.items():
        logger.info(f"  {agent}: {status}")
    
    logger.info("Main Orchestrator ready!")


@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint"""
    agent_health = await service.health_check_agents()
    
    return HealthCheck(
        service_name="orchestrator",
        status="healthy",
        version="1.0.0",
        dependencies=agent_health
    )


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        service_name="orchestrator",
        status="healthy",
        version="1.0.0"
    )


@app.post("/personalize/{customer_id}", response_model=PersonalizationResponse)
@timing_decorator
async def personalize_customer(
    customer_id: str,
    channel: Channel = Channel.EMAIL
):
    """
    Execute full personalization flow for a customer
    
    This endpoint orchestrates all 5 agents:
    1. Segmentation - Classify customer
    2. Content Retrieval - Get relevant content
    3. Message Generation - Create personalized messages
    4. Compliance - Validate messages
    5. Experiment - Deploy A/B test
    """
    try:
        logger.info(f"Starting personalization for customer {customer_id}")
        
        response = await service.orchestrate_personalization(
            customer_id=customer_id,
            channel=channel
        )
        
        return response
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Agent call failed: {e}")
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Agent error: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Personalization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/health")
async def check_agents_health():
    """Check health of all agents"""
    health = await service.health_check_agents()
    all_healthy = all(status == "healthy" for status in health.values())
    
    return {
        "status": "healthy" if all_healthy else "degraded",
        "agents": health,
        "timestamp": datetime.utcnow()
    }


@app.get("/metrics")
async def get_metrics():
    """Get system metrics"""
    # In production, this would return real metrics
    return {
        "total_requests": 0,
        "avg_latency_ms": 0,
        "success_rate": 1.0,
        "timestamp": datetime.utcnow()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)