"""
Agent 4: Compliance & Safety Service
Validates content for brand guidelines, safety, and compliance
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import re
import os
import sys
from datetime import datetime
from typing import List
import string

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.models import (
    ComplianceValidationRequest, ComplianceValidationResponse,
    ComplianceReport, ComplianceCheck, ComplianceRule, HealthCheck
)
from shared.utils import setup_logging, timing_decorator

# Initialize FastAPI app
app = FastAPI(
    title="Compliance Agent",
    description="Content safety and compliance validation service",
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
logger = setup_logging("compliance-agent")


class ComplianceService:
    """Content compliance and safety service"""
    
    def __init__(self):
        self.rules = self._load_compliance_rules()
        self.banned_words = self._load_banned_words()
        self.required_disclaimers = self._load_required_disclaimers()
        
    def _load_compliance_rules(self) -> List[ComplianceRule]:
        """Load compliance rules"""
        return [
            ComplianceRule(
                rule_id="R001",
                rule_name="No Profanity",
                rule_type="content_safety",
                severity="critical",
                description="Content must not contain profane or offensive language"
            ),
            ComplianceRule(
                rule_id="R002",
                rule_name="No Discriminatory Language",
                rule_type="content_safety",
                severity="critical",
                description="Content must not contain discriminatory language"
            ),
            ComplianceRule(
                rule_id="R003",
                rule_name="No False Claims",
                rule_type="brand_compliance",
                severity="high",
                description="Content must not make false or misleading claims"
            ),
            ComplianceRule(
                rule_id="R004",
                rule_name="Brand Voice Consistency",
                rule_type="brand_compliance",
                severity="medium",
                description="Content must maintain consistent brand voice"
            ),
            ComplianceRule(
                rule_id="R005",
                rule_name="Legal Disclaimers",
                rule_type="legal_compliance",
                severity="high",
                description="Required legal disclaimers must be present"
            ),
            ComplianceRule(
                rule_id="R006",
                rule_name="Character Limits",
                rule_type="technical",
                severity="medium",
                description="Content must respect channel character limits"
            ),
            ComplianceRule(
                rule_id="R007",
                rule_name="No Spam Indicators",
                rule_type="content_safety",
                severity="high",
                description="Content must not contain spam indicators"
            ),
            ComplianceRule(
                rule_id="R008",
                rule_name="Tone Appropriateness",
                rule_type="brand_compliance",
                severity="low",
                description="Tone must be appropriate for target segment"
            ),
        ]
    
    def _load_banned_words(self) -> set:
        """Load list of banned words"""
        # Simplified list - in production, this would be comprehensive
        return {
            'guaranteed', 'free', 'winner', 'congratulations',
            'click here', 'act now', 'limited time only',
            'earn money', 'get rich', 'no risk'
        }
    
    def _load_required_disclaimers(self) -> dict:
        """Load required disclaimers by content type"""
        return {
            'promotion': "Terms and conditions apply",
            'financial': "Past performance does not guarantee future results",
            'health': "Consult with a healthcare professional"
        }
    
    def check_profanity(self, text: str) -> ComplianceCheck:
        """Check for profane language"""
        # Simplified profanity check
        profane_words = {'damn', 'hell', 'crap', 'stupid', 'fuck'}  # Simplified list
        
        text_lower = text.lower()
        found_words = [word for word in profane_words if word in text_lower]
        
        passed = len(found_words) == 0
        
        return ComplianceCheck(
            rule_id="R001",
            rule_name="No Profanity",
            passed=passed,
            score=1.0 if passed else 0.0,
            details=f"Found profane words: {found_words}" if not passed else "No profanity detected"
        )
    
    def check_discriminatory_language(self, text: str) -> ComplianceCheck:
        """Check for discriminatory language"""
        # Simplified discrimination check
        discriminatory_patterns = [
            r'\b(race|ethnic|gender|age|religion|disability)\s+(bias|discrimination)',
            r'\b(inferior|superior)\s+(race|gender|group)',
        ]
        
        found_patterns = []
        for pattern in discriminatory_patterns:
            if re.search(pattern, text.lower()):
                found_patterns.append(pattern)
        
        passed = len(found_patterns) == 0
        
        return ComplianceCheck(
            rule_id="R002",
            rule_name="No Discriminatory Language",
            passed=passed,
            score=1.0 if passed else 0.0,
            details="No discriminatory language detected" if passed else f"Potential issues found: {len(found_patterns)}"
        )
    
    def check_false_claims(self, text: str) -> ComplianceCheck:
        """Check for false or misleading claims"""
        # Check for absolute claims without qualifiers
        absolute_claims = [
            'guaranteed', 'always works', 'never fails', 
            '100% effective', 'proven results', 'scientifically proven'
        ]
        
        text_lower = text.lower()
        found_claims = [claim for claim in absolute_claims if claim in text_lower]
        
        passed = len(found_claims) == 0
        score = max(0.0, 1.0 - (len(found_claims) * 0.3))
        
        return ComplianceCheck(
            rule_id="R003",
            rule_name="No False Claims",
            passed=passed,
            score=score,
            details=f"Found unsubstantiated claims: {found_claims}" if not passed else "No false claims detected"
        )
    
    def check_brand_voice(self, text: str, tone: str) -> ComplianceCheck:
        """Check brand voice consistency"""
        # Simplified brand voice check
        # Check for appropriate formality level
        
        formal_indicators = ['dear', 'sincerely', 'regards', 'please']
        casual_indicators = ['hey', 'hi', 'cheers', 'awesome', 'cool']
        
        text_lower = text.lower()
        
        formal_count = sum(1 for word in formal_indicators if word in text_lower)
        casual_count = sum(1 for word in casual_indicators if word in text_lower)
        
        # Check if tone matches content
        tone_match = True
        if tone in ['professional', 'formal'] and casual_count > formal_count:
            tone_match = False
        elif tone in ['casual', 'friendly'] and formal_count > casual_count:
            tone_match = False
        
        score = 1.0 if tone_match else 0.6
        
        return ComplianceCheck(
            rule_id="R004",
            rule_name="Brand Voice Consistency",
            passed=tone_match,
            score=score,
            details="Tone matches brand voice" if tone_match else "Tone may not match intended voice"
        )
    
    def check_spam_indicators(self, text: str) -> ComplianceCheck:
        """Check for spam indicators"""
        spam_patterns = [
            r'!!+',  # Multiple exclamation marks
            r'\$\$+',  # Multiple dollar signs
            r'[A-Z]{5,}',  # Excessive caps
            r'click here',
            r'buy now',
            r'limited time',
            r'act now',
        ]
        
        found_patterns = []
        for pattern in spam_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                found_patterns.append(pattern)
        
        score = max(0.0, 1.0 - (len(found_patterns) * 0.2))
        passed = score > 0.7
        
        return ComplianceCheck(
            rule_id="R007",
            rule_name="No Spam Indicators",
            passed=passed,
            score=score,
            details=f"Found {len(found_patterns)} spam indicators" if not passed else "No spam indicators detected"
        )
    
    def check_character_limits(self, text: str, channel: str) -> ComplianceCheck:
        """Check character limits for channel"""
        limits = {
            'sms': 160,
            'push_notification': 100,
            'email': 10000,
            'whatsapp': 4096
        }
        
        limit = limits.get(channel, 10000)
        text_length = len(text)
        
        passed = text_length <= limit
        score = min(1.0, limit / max(text_length, 1))
        
        return ComplianceCheck(
            rule_id="R006",
            rule_name="Character Limits",
            passed=passed,
            score=score,
            details=f"Length: {text_length}/{limit} characters"
        )
    
    def validate_message(self, variant, segment_type: str) -> ComplianceReport:
        """Validate a single message variant"""
        checks = []
        
        # Run all compliance checks
        checks.append(self.check_profanity(variant.message_text))
        checks.append(self.check_discriminatory_language(variant.message_text))
        checks.append(self.check_false_claims(variant.message_text))
        checks.append(self.check_brand_voice(variant.message_text, variant.tone.value))
        checks.append(self.check_spam_indicators(variant.message_text))
        checks.append(self.check_character_limits(variant.message_text, variant.channel.value))
        
        # Calculate overall risk score
        scores = [check.score for check in checks if check.score is not None]
        risk_score = 1.0 - (sum(scores) / len(scores)) if scores else 1.0
        
        # Determine if all checks passed
        critical_checks = [c for c in checks if c.rule_id in ['R001', 'R002', 'R003', 'R007']]
        overall_passed = all(c.passed for c in critical_checks)
        
        # Generate recommendations
        recommendations = []
        for check in checks:
            if not check.passed:
                recommendations.append(f"Fix: {check.rule_name} - {check.details}")
        
        if not recommendations:
            recommendations.append("Content meets all compliance requirements")
        
        return ComplianceReport(
            variant_id=variant.variant_id,
            overall_passed=overall_passed,
            checks=checks,
            risk_score=risk_score,
            recommendations=recommendations
        )


# Initialize service
service = ComplianceService()


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Starting Compliance Agent...")
    logger.info(f"Loaded {len(service.rules)} compliance rules")
    logger.info("Compliance Agent ready!")


@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint"""
    return HealthCheck(
        service_name="compliance-agent",
        status="healthy",
        version="1.0.0",
        dependencies={
            "rules_loaded": str(len(service.rules)),
            "banned_words": str(len(service.banned_words))
        }
    )


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        service_name="compliance-agent",
        status="healthy",
        version="1.0.0"
    )


@app.post("/validate", response_model=ComplianceValidationResponse)
@timing_decorator
async def validate_messages(request: ComplianceValidationRequest):
    """Validate message variants for compliance"""
    try:
        logger.info(f"Validating {len(request.messages.variants)} message variants")
        
        reports = []
        approved_variants = []
        rejected_variants = []
        
        for variant in request.messages.variants:
            report = service.validate_message(
                variant,
                request.messages.segment_id
            )
            reports.append(report)
            
            if report.overall_passed:
                approved_variants.append(variant.variant_id)
            else:
                rejected_variants.append(variant.variant_id)
        
        response = ComplianceValidationResponse(
            segment_id=request.messages.segment_id,
            reports=reports,
            all_passed=len(rejected_variants) == 0,
            approved_variants=approved_variants,
            rejected_variants=rejected_variants,
            timestamp=datetime.utcnow()
        )
        
        logger.info(f"Validation complete: {len(approved_variants)} approved, {len(rejected_variants)} rejected")
        return response
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/rules")
async def get_rules():
    """Get all compliance rules"""
    return {
        "rules": service.rules,
        "total": len(service.rules)
    }


@app.get("/banned-words")
async def get_banned_words():
    """Get list of banned words"""
    return {
        "banned_words": list(service.banned_words),
        "total": len(service.banned_words)
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5004)
