# Databricks notebook source
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from datetime import datetime
from typing import List, Optional

from shared.models import (
    ContentRetrievalRequest, ContentRetrievalResponse,
    ContentSnippet, ContentMetadata, SegmentProfile, HealthCheck
)
from shared.utils import setup_logging, timing_decorator

app = FastAPI(
    title="Content Retrieval Agent",
    description="Content retrieval service",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = setup_logging("content-retrieval-agent")

class ContentRetrievalService:
    def __init__(self):
        self.content_df = None
        
    def load_content_data(self, data_path='../data/content.csv'):
        logger.info(f"Loading content from {data_path}")
        try:
            self.content_df = pd.read_csv(data_path)
            logger.info(f"Loaded {len(self.content_df)} content pieces")
            return True
        except Exception as e:
            logger.error(f"Error loading content: {e}")
            return False
    
    def retrieve_content(
        self, 
        segment: SegmentProfile, 
        query: Optional[str] = None,
        top_k: int = 3,
        filters: Optional[dict] = None
    ) -> List[ContentSnippet]:
        logger.info(f"Retrieving content for segment {segment.segment_id}")
        
        # Filter by segment and compliance
        filtered = self.content_df[
            self.content_df['compliance_approved'] == True
        ].copy()
        
        # Match segment type
        segment_type = segment.segment_type.value
        filtered['match'] = filtered['target_segment'].fillna('').str.contains(
            segment_type, case=False, na=False
        )
        filtered = filtered.sort_values(['match', 'performance_score'], ascending=[False, False])
        
        # Get top results
        results = filtered.head(top_k)
        
        # Convert to response format
        snippets = []
        for _, row in results.iterrows():
            metadata = ContentMetadata(
                content_id=str(row['content_id']),
                title=str(row['title']),
                source="marketing_library",
                content_type=str(row['content_type']),
                category=str(row['category']),
                tags=str(row['tags']).split(',') if pd.notna(row['tags']) else [],
                compliance_approved=bool(row['compliance_approved']),
                created_at=datetime.fromisoformat(str(row['created_at'])),
                updated_at=datetime.utcnow()
            )
            
            snippet = ContentSnippet(
                content_id=str(row['content_id']),
                text=str(row['text'])[:500],
                score=float(row['performance_score']) / 10.0,
                metadata=metadata
            )
            snippets.append(snippet)
        
        logger.info(f"Retrieved {len(snippets)} content snippets")
        return snippets

service = ContentRetrievalService()

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Content Retrieval Agent...")
    service.load_content_data()
    logger.info("Content Retrieval Agent ready!")

@app.get("/", response_model=HealthCheck)
async def root():
    content_count = len(service.content_df) if service.content_df is not None else 0
    return HealthCheck(
        service_name="content-retrieval-agent",
        status="healthy",
        version="1.0.0",
        dependencies={
            "indexed_content": str(content_count),
            "retrieval_method": "simple_matching"
        }
    )

@app.get("/health", response_model=HealthCheck)
async def health_check():
    return HealthCheck(
        service_name="content-retrieval-agent",
        status="healthy",
        version="1.0.0"
    )

@app.post("/retrieve", response_model=ContentRetrievalResponse)
@timing_decorator
async def retrieve_content(request: ContentRetrievalRequest):
    try:
        logger.info(f"Content retrieval for segment {request.segment.segment_id}")
        
        snippets = service.retrieve_content(
            segment=request.segment,
            query=request.query,
            top_k=request.top_k,
            filters=request.filters
        )
        
        response = ContentRetrievalResponse(
            segment_id=request.segment.segment_id,
            content_snippets=snippets,
            total_retrieved=len(snippets),
            timestamp=datetime.utcnow()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Content retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_content(query: str, top_k: int = 5):
    try:
        filtered = service.content_df[
            service.content_df['compliance_approved'] == True
        ].copy()
        
        query_lower = query.lower()
        filtered['score'] = filtered.apply(
            lambda row: (
                (query_lower in str(row['title']).lower()) * 2 +
                (query_lower in str(row['text']).lower()) * 1
            ),
            axis=1
        )
        
        results = filtered.nlargest(top_k, 'score')
        
        return {
            "query": query,
            "results": [
                {
                    "content_id": str(row['content_id']),
                    "title": str(row['title']),
                    "text": str(row['text'])[:200],
                    "score": float(row['score'])
                }
                for _, row in results.iterrows()
            ]
        }
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reindex")
async def reindex_content():
    try:
        logger.info("Reloading content...")
        service.load_content_data()
        return {"status": "success", "message": "Content reloaded successfully"}
    except Exception as e:
        logger.error(f"Reload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)