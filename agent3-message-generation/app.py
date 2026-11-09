"""
Agent 3: Message Generation Service
Uses LLM to generate personalized messages
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import os
import sys
from datetime import datetime
from typing import List
import random

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.models import (
    MessageGenerationRequest, MessageGenerationResponse,
    MessageVariant, MessageTone, Channel, HealthCheck
)
from shared.utils import setup_logging, timing_decorator, Config

# Initialize FastAPI app
app = FastAPI(
    title="Message Generation Agent",
    description="LLM-based personalized message generation",
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
logger = setup_logging("message-generation-agent")


class MessageGenerationService:
    """LLM-based message generation service"""
    
    def __init__(self):
        self.ollama_url = Config.OLLAMA_HOST
        self.model_name = Config.LLM_MODEL
        self.use_ollama = True
        
    def check_ollama_availability(self):
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info("Ollama is available")
                return True
        except:
            logger.warning("Ollama not available, using template-based generation")
            self.use_ollama = False
            return False
    
    def generate_with_ollama(self, prompt: str) -> str:
        """Generate text using Ollama"""
        try:
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['response']
            else:
                raise Exception(f"Ollama API error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ollama generation error: {e}")
            raise
    
    def generate_with_template(self, segment_type: str, content: str, tone: str, channel: str) -> str:
        """Fallback template-based generation"""
        templates = {
            'email': {
                'professional': "Dear valued customer,\n\n{content}\n\nBest regards,\nThe Team",
                'casual': "Hi there!\n\n{content}\n\nCheers!",
                'friendly': "Hello!\n\n{content}\n\nWarm regards,\nYour friends at our company",
                'urgent': "IMPORTANT UPDATE:\n\n{content}\n\nAct now!",
            },
            'sms': {
                'professional': "{content}",
                'casual': "Hey! {content}",
                'friendly': "Hi friend! {content}",
                'urgent': "⚡ URGENT: {content}",
            }
        }
        
        channel_key = channel if channel in templates else 'email'
        tone_key = tone if tone in templates[channel_key] else 'professional'
        
        template = templates[channel_key][tone_key]
        return template.format(content=content[:200])
    
    def build_generation_prompt(
        self,
        segment_profile,
        content_snippets,
        channel: Channel,
        tone: MessageTone
    ) -> str:
        """Build prompt for LLM"""
        
        # Extract key info from segment
        segment_type = segment_profile.segment_type.value
        segment_desc = segment_profile.description
        avg_value = segment_profile.average_value
        
        # Get content texts
        content_texts = [snippet.text for snippet in content_snippets]
        combined_content = "\n".join(content_texts[:2])  # Use top 2 snippets
        
        prompt = f"""You are a professional marketing copywriter. Generate a personalized {channel.value} message.

SEGMENT PROFILE:
- Type: {segment_type}
- Description: {segment_desc}
- Average Customer Value: ${avg_value:.2f}

CONTENT TO PROMOTE:
{combined_content}

REQUIREMENTS:
- Tone: {tone.value}
- Channel: {channel.value}
- Length: {"50-100 words" if channel == Channel.SMS else "100-200 words"}
- Include clear call-to-action
- Be authentic and engaging
- Match the tone to the segment

Generate the message now (just the message text, no explanations):"""
        
        return prompt
    
    def generate_messages(
        self,
        request: MessageGenerationRequest
    ) -> List[MessageVariant]:
        """Generate multiple message variants"""
        
        variants = []
        
        # Determine tones to use
        if request.tone:
            tones = [request.tone]
        else:
            # Select appropriate tones based on segment
            segment_type = request.segment.segment_type.value
            if 'high_value' in segment_type or 'luxury' in segment_type:
                tones = [MessageTone.PROFESSIONAL, MessageTone.FRIENDLY]
            elif 'tech' in segment_type:
                tones = [MessageTone.CASUAL, MessageTone.PROFESSIONAL]
            else:
                tones = [MessageTone.FRIENDLY, MessageTone.CASUAL]
        
        # Ensure we generate the requested number of variants
        while len(tones) < request.num_variants:
            tones.append(random.choice(list(MessageTone)))
        
        # Generate variants
        for i, tone in enumerate(tones[:request.num_variants]):
            try:
                # Build prompt
                prompt = self.build_generation_prompt(
                    request.segment,
                    request.content.content_snippets,
                    request.channel,
                    tone
                )
                
                # Generate message
                if self.use_ollama:
                    try:
                        message_text = self.generate_with_ollama(prompt)
                    except:
                        # Fallback to template
                        content = request.content.content_snippets[0].text if request.content.content_snippets else ""
                        message_text = self.generate_with_template(
                            request.segment.segment_type.value,
                            content,
                            tone.value,
                            request.channel.value
                        )
                else:
                    content = request.content.content_snippets[0].text if request.content.content_snippets else ""
                    message_text = self.generate_with_template(
                        request.segment.segment_type.value,
                        content,
                        tone.value,
                        request.channel.value
                    )
                
                # Generate subject line for email
                subject = None
                if request.channel == Channel.EMAIL:
                    subject = f"Exclusive offer for our {request.segment.segment_type.value.replace('_', ' ')} customers"
                
                # Create variant
                variant = MessageVariant(
                    variant_id=chr(65 + i),  # A, B, C, etc.
                    message_text=message_text.strip(),
                    subject=subject,
                    tone=tone,
                    channel=request.channel,
                    personalization_tokens={
                        "segment": request.segment.segment_type.value,
                        "avg_value": str(request.segment.average_value)
                    },
                    metadata={
                        "generation_method": "ollama" if self.use_ollama else "template",
                        "content_sources": [s.content_id for s in request.content.content_snippets]
                    }
                )
                
                variants.append(variant)
                
            except Exception as e:
                logger.error(f"Error generating variant {i}: {e}")
                continue
        
        return variants


# Initialize service
service = MessageGenerationService()


@app.on_event("startup")
async def startup_event():
    """Initialize service on startup"""
    logger.info("Starting Message Generation Agent...")
    service.check_ollama_availability()
    logger.info("Message Generation Agent ready!")


@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint"""
    return HealthCheck(
        service_name="message-generation-agent",
        status="healthy",
        version="1.0.0",
        dependencies={
            "llm_available": str(service.use_ollama),
            "model": service.model_name
        }
    )


@app.get("/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    return HealthCheck(
        service_name="message-generation-agent",
        status="healthy",
        version="1.0.0"
    )


@app.post("/generate", response_model=MessageGenerationResponse)
@timing_decorator
async def generate_messages(request: MessageGenerationRequest):
    """Generate personalized message variants"""
    try:
        logger.info(f"Generating {request.num_variants} messages for segment {request.segment.segment_id}")
        
        variants = service.generate_messages(request)
        
        if not variants:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate any message variants"
            )
        
        response = MessageGenerationResponse(
            segment_id=request.segment.segment_id,
            variants=variants,
            generated_at=datetime.utcnow()
        )
        
        logger.info(f"Generated {len(variants)} message variants")
        return response
        
    except Exception as e:
        logger.error(f"Message generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/regenerate")
async def regenerate_variant(
    segment_id: str,
    variant_id: str,
    tone: MessageTone
):
    """Regenerate a specific variant"""
    try:
        # This would regenerate a specific variant
        # Implementation simplified for demo
        return {
            "status": "success",
            "message": f"Variant {variant_id} regenerated with {tone.value} tone"
        }
    except Exception as e:
        logger.error(f"Regeneration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5003)
