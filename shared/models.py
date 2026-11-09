"""
Shared data models and schemas used across all agents
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class SegmentType(str, Enum):
    HIGH_VALUE = "high_value"
    MEDIUM_VALUE = "medium_value"
    LOW_VALUE = "low_value"
    TECH_ENTHUSIAST = "tech_enthusiast"
    BUDGET_CONSCIOUS = "budget_conscious"
    LUXURY_SEEKER = "luxury_seeker"
    FREQUENT_BUYER = "frequent_buyer"
    OCCASIONAL_BUYER = "occasional_buyer"


class Channel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push_notification"
    WHATSAPP = "whatsapp"


class MessageTone(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    URGENT = "urgent"
    PROMOTIONAL = "promotional"


# Agent 1: Segmentation Models
class CustomerData(BaseModel):
    customer_id: str
    age: Optional[int] = None
    income: Optional[float] = None
    purchase_frequency: Optional[int] = None
    average_order_value: Optional[float] = None
    lifetime_value: Optional[float] = None
    recency_days: Optional[int] = None
    product_categories: Optional[List[str]] = None
    engagement_score: Optional[float] = None


class SegmentProfile(BaseModel):
    segment_id: str
    segment_type: SegmentType
    description: str
    characteristics: Dict[str, Any]
    size: int
    average_value: float


class SegmentationRequest(BaseModel):
    customer_id: str


class SegmentationResponse(BaseModel):
    customer_id: str
    segment_id: str
    segment_type: SegmentType
    confidence: float
    segment_profile: SegmentProfile
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Agent 2: Content Retrieval Models
class ContentMetadata(BaseModel):
    content_id: str
    title: str
    source: str
    content_type: str
    category: str
    tags: List[str]
    compliance_approved: bool
    created_at: datetime
    updated_at: datetime


class ContentSnippet(BaseModel):
    content_id: str
    text: str
    score: float
    metadata: ContentMetadata


class ContentRetrievalRequest(BaseModel):
    segment: SegmentProfile
    query: Optional[str] = None
    top_k: int = 3
    filters: Optional[Dict[str, Any]] = None


class ContentRetrievalResponse(BaseModel):
    segment_id: str
    content_snippets: List[ContentSnippet]
    total_retrieved: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Agent 3: Message Generation Models
class MessageVariant(BaseModel):
    variant_id: str
    message_text: str
    subject: Optional[str] = None
    tone: MessageTone
    channel: Channel
    personalization_tokens: Dict[str, str]
    metadata: Dict[str, Any]


class MessageGenerationRequest(BaseModel):
    segment: SegmentProfile
    content: ContentRetrievalResponse
    channel: Channel
    num_variants: int = 3
    tone: Optional[MessageTone] = None


class MessageGenerationResponse(BaseModel):
    customer_id: Optional[str] = None
    segment_id: str
    variants: List[MessageVariant]
    generated_at: datetime = Field(default_factory=datetime.utcnow)


# Agent 4: Compliance Models
class ComplianceRule(BaseModel):
    rule_id: str
    rule_name: str
    rule_type: str
    severity: str
    description: str


class ComplianceCheck(BaseModel):
    rule_id: str
    rule_name: str
    passed: bool
    score: Optional[float] = None
    details: str


class ComplianceReport(BaseModel):
    variant_id: str
    overall_passed: bool
    checks: List[ComplianceCheck]
    risk_score: float
    recommendations: List[str]


class ComplianceValidationRequest(BaseModel):
    messages: MessageGenerationResponse


class ComplianceValidationResponse(BaseModel):
    segment_id: str
    reports: List[ComplianceReport]
    all_passed: bool
    approved_variants: List[str]
    rejected_variants: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Agent 5: Experiment Models
class ExperimentConfig(BaseModel):
    experiment_name: str
    test_type: str = "A/B/n"
    sample_size: int
    duration_days: int
    success_metrics: List[str]


class ExperimentAssignment(BaseModel):
    customer_id: str
    variant_id: str
    assigned_at: datetime


class ExperimentMetrics(BaseModel):
    variant_id: str
    impressions: int
    clicks: int
    conversions: int
    click_rate: float
    conversion_rate: float
    revenue: float
    roi: float


class ExperimentDeployRequest(BaseModel):
    customer_id: str
    messages: ComplianceValidationResponse
    config: Optional[ExperimentConfig] = None


class ExperimentDeployResponse(BaseModel):
    experiment_id: str
    customer_id: str
    assigned_variant: MessageVariant
    deployed_at: datetime
    expected_completion: datetime


class ExperimentResults(BaseModel):
    experiment_id: str
    status: str
    metrics: List[ExperimentMetrics]
    winner: Optional[str] = None
    confidence_level: Optional[float] = None
    insights: List[str]


# Orchestrator Models
class PersonalizationRequest(BaseModel):
    customer_id: str
    channel: Channel = Channel.EMAIL
    force_regenerate: bool = False


class PersonalizationResponse(BaseModel):
    customer_id: str
    segment: SegmentationResponse
    content: ContentRetrievalResponse
    messages: MessageGenerationResponse
    compliance: ComplianceValidationResponse
    experiment: ExperimentDeployResponse
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Health Check Models
class HealthCheck(BaseModel):
    service_name: str
    status: str
    version: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    dependencies: Optional[Dict[str, str]] = None


# Error Models
class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trace_id: Optional[str] = None
