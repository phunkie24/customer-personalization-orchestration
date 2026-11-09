"""
Agent 1: Customer Segmentation Service
Uses ML clustering to segment customers
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import joblib
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.models import (
    SegmentationRequest, SegmentationResponse, 
    SegmentProfile, SegmentType, HealthCheck
)
from shared.utils import setup_logging, timing_decorator

# Initialize FastAPI app
app = FastAPI(
    title="Segmentation Agent",
    description="ML-based customer segmentation service",
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
logger = setup_logging("segmentation-agent")

# Global variables for models and data
scaler = None
kmeans_model = None
pca_model = None
customer_data = None
segment_profiles = {}


class SegmentationService:
    """Customer segmentation service"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.pca = None
        self.customer_df = None
        self.segment_mapping = {
            0: SegmentType.HIGH_VALUE,
            1: SegmentType.TECH_ENTHUSIAST,
            2: SegmentType.BUDGET_CONSCIOUS,
            3: SegmentType.FREQUENT_BUYER,
            4: SegmentType.OCCASIONAL_BUYER,
            5: SegmentType.LUXURY_SEEKER,
            6: SegmentType.MEDIUM_VALUE,
            7: SegmentType.LOW_VALUE,
        }
    
    def load_data(self, data_path='../data/customers.csv'):
        """Load customer data"""
        logger.info(f"Loading customer data from {data_path}")
        try:
            self.customer_df = pd.read_csv(data_path)
            logger.info(f"Loaded {len(self.customer_df)} customers")
            return True
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return False
    
    def train_segmentation_model(self, n_clusters=8):
        """Train segmentation model"""
        logger.info("Training segmentation model...")
        
        # Select features for segmentation
        features = ['age', 'income', 'purchase_frequency', 
                   'average_order_value', 'lifetime_value', 
                   'recency_days', 'engagement_score']
        
        X = self.customer_df[features].fillna(self.customer_df[features].mean())
        
        # Standardize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Apply PCA for dimensionality reduction
        self.pca = PCA(n_components=5)
        X_pca = self.pca.fit_transform(X_scaled)
        
        # Train K-Means
        self.kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = self.kmeans.fit_predict(X_pca)
        
        # Add cluster labels to dataframe
        self.customer_df['segment_cluster'] = clusters
        
        # Generate segment profiles
        self._generate_segment_profiles()
        
        logger.info(f"Training complete. Created {n_clusters} segments")
        return clusters
    
    def _generate_segment_profiles(self):
        """Generate profiles for each segment"""
        global segment_profiles
        
        for cluster_id in range(self.kmeans.n_clusters):
            segment_customers = self.customer_df[
                self.customer_df['segment_cluster'] == cluster_id
            ]
            
            profile = SegmentProfile(
                segment_id=f"SEG_{cluster_id}",
                segment_type=self.segment_mapping.get(cluster_id, SegmentType.MEDIUM_VALUE),
                description=self._generate_segment_description(cluster_id, segment_customers),
                characteristics={
                    'avg_age': float(segment_customers['age'].mean()),
                    'avg_income': float(segment_customers['income'].mean()),
                    'avg_ltv': float(segment_customers['lifetime_value'].mean()),
                    'avg_purchase_freq': float(segment_customers['purchase_frequency'].mean()),
                    'avg_order_value': float(segment_customers['average_order_value'].mean()),
                    'avg_recency': float(segment_customers['recency_days'].mean()),
                    'avg_engagement': float(segment_customers['engagement_score'].mean()),
                },
                size=len(segment_customers),
                average_value=float(segment_customers['lifetime_value'].mean())
            )
            segment_profiles[f"SEG_{cluster_id}"] = profile
    
    def _generate_segment_description(self, cluster_id, segment_data):
        """Generate human-readable segment description"""
        avg_ltv = segment_data['lifetime_value'].mean()
        avg_freq = segment_data['purchase_frequency'].mean()
        avg_age = segment_data['age'].mean()
        
        if avg_ltv > 10000 and avg_freq > 10:
            return "High-value customers with frequent purchases and strong brand loyalty"
        elif avg_ltv > 5000:
            return "Medium-value customers with consistent purchase behavior"
        elif avg_freq > 8:
            return "Frequent buyers with moderate transaction values"
        elif avg_age < 35:
            return "Young, tech-savvy customers with growing purchase potential"
        else:
            return "Emerging customers with growth opportunities"
    
    def predict_segment(self, customer_id: str):
        """Predict segment for a customer"""
        customer = self.customer_df[
            self.customer_df['customer_id'] == customer_id
        ]
        
        if len(customer) == 0:
            raise ValueError(f"Customer {customer_id} not found")
        
        features = ['age', 'income', 'purchase_frequency', 
                   'average_order_value', 'lifetime_value', 
                   'recency_days', 'engagement_score']
        
        X = customer[features].values
        X_scaled = self.scaler.transform(X)
        X_pca = self.pca.transform(X_scaled)
        
        cluster = self.kmeans.predict(X_pca)[0]
        
        # Calculate confidence based on distance to cluster center
        distances = self.kmeans.transform(X_pca)[0]
        min_distance = distances[cluster]
        confidence = 1.0 / (1.0 + min_distance)
        
        segment_id = f"SEG_{cluster}"
        profile = segment_profiles[segment_id]
        
        return cluster, confidence, profile
    
    def save_models(self, model_dir='models'):
        """Save trained models"""
        os.makedirs(model_dir, exist_ok=True)
        joblib.dump(self.scaler, f'{model_dir}/scaler.pkl')
        joblib.dump(self.kmeans, f'{model_dir}/kmeans.pkl')
        joblib.dump(self.pca, f'{model_dir}/pca.pkl')
        logger.info(f"Models saved to {model_dir}")
    
    def load_models(self, model_dir='models'):
        """Load trained models"""
        self.scaler = joblib.load(f'{model_dir}/scaler.pkl')
        self.kmeans = joblib.load(f'{model_dir}/kmeans.pkl')
        self.pca = joblib.load(f'{model_dir}/pca.pkl')
        logger.info(f"Models loaded from {model_dir}")


# Initialize service
service = SegmentationService()


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Starting Segmentation Agent...")
    
    # Load or train models
    model_dir = 'models'
    if os.path.exists(f'{model_dir}/kmeans.pkl'):
        logger.info("Loading existing models...")
        service.load_models(model_dir)
        service.load_data()
        service._generate_segment_profiles()
    else:
        logger.info("Training new models...")
        if service.load_data():
            service.train_segmentation_model()
            service.save_models(model_dir)
    
    logger.info("Segmentation Agent ready!")


@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint"""
    return HealthCheck(
        service_name="segmentation-agent",
        status="healthy",
        version="1.0.0",
        dependencies={
            "customers_loaded": str(len(service.customer_df) if service.customer_df is not None else 0),
            "segments": str(len(segment_profiles))
        }
    )


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        service_name="segmentation-agent",
        status="healthy",
        version="1.0.0"
    )


@app.post("/segment", response_model=SegmentationResponse)
@timing_decorator
async def segment_customer(request: SegmentationRequest):
    """Segment a customer"""
    try:
        logger.info(f"Segmenting customer {request.customer_id}")
        
        cluster, confidence, profile = service.predict_segment(request.customer_id)
        
        response = SegmentationResponse(
            customer_id=request.customer_id,
            segment_id=profile.segment_id,
            segment_type=profile.segment_type,
            confidence=confidence,
            segment_profile=profile,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Customer {request.customer_id} assigned to {profile.segment_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Customer not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Segmentation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/segments")
async def list_segments():
    """List all segment profiles"""
    return {
        "segments": list(segment_profiles.values()),
        "total": len(segment_profiles)
    }


@app.post("/retrain")
async def retrain_model():
    """Retrain segmentation model"""
    try:
        logger.info("Retraining model...")
        service.train_segmentation_model()
        service.save_models()
        return {"status": "success", "message": "Model retrained successfully"}
    except Exception as e:
        logger.error(f"Retraining error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)
