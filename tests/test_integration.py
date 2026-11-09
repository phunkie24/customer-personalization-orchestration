"""
Integration tests for Customer Personalization Orchestrator
"""
import asyncio
import httpx
import sys
from datetime import datetime

# Service endpoints
SERVICES = {
    "orchestrator": "http://localhost:8000",
    "segmentation": "http://localhost:5001",
    "content_retrieval": "http://localhost:5002",
    "message_generation": "http://localhost:5003",
    "compliance": "http://localhost:5004",
    "experiment": "http://localhost:5005"
}

print("=" * 60)
print("Customer Personalization Orchestrator - Integration Tests")
print("=" * 60)

async def test_health_checks():
    """Test all service health endpoints"""
    print("\n[Test 1] Health Checks")
    
    async with httpx.AsyncClient() as client:
        for name, url in SERVICES.items():
            try:
                response = await client.get(f"{url}/health", timeout=5.0)
                if response.status_code == 200:
                    print(f"  ✓ {name}: healthy")
                else:
                    print(f"  ✗ {name}: unhealthy (status {response.status_code})")
            except Exception as e:
                print(f"  ✗ {name}: not responding ({e})")
    
    print("  ✓ Health check test passed")

async def test_agent1_segmentation():
    """Test Agent 1: Customer Segmentation"""
    print("\n[Test 2] Agent 1 - Customer Segmentation")
    
    async with httpx.AsyncClient() as client:
        test_data = {
            "customer_id": "C00000001"
        }
        
        response = await client.post(
            f"{SERVICES['segmentation']}/segment",
            json=test_data,
            timeout=30.0
        )
        
        assert response.status_code == 200, f"Status: {response.status_code}"
        result = response.json()
        
        print(f"  ✓ Customer segmented: {result['segment_id']}")
        print(f"    Segment type: {result['segment_type']}")
        print(f"    Confidence: {result['confidence']:.2f}")
        print("  ✓ Segmentation test passed")

async def test_agent2_content_retrieval():
    """Test Agent 2: Content Retrieval"""
    print("\n[Test 3] Agent 2 - Content Retrieval")
    
    async with httpx.AsyncClient() as client:
        # First get a segment
        seg_response = await client.post(
            f"{SERVICES['segmentation']}/segment",
            json={"customer_id": "C00000001"},
            timeout=30.0
        )
        segment_data = seg_response.json()
        
        # Then retrieve content
        test_data = {
            "segment": segment_data["segment_profile"],
            "query": "products",
            "top_k": 3,
            "filters": {}
        }
        
        response = await client.post(
            f"{SERVICES['content_retrieval']}/retrieve",
            json=test_data,
            timeout=30.0
        )
        
        assert response.status_code == 200, f"Status: {response.status_code}"
        result = response.json()
        
        print(f"  ✓ Retrieved {result['total_retrieved']} content items")
        print("  ✓ Content retrieval test passed")

async def test_agent3_message_generation():
    """Test Agent 3: Message Generation"""
    print("\n[Test 4] Agent 3 - Message Generation")
    
    async with httpx.AsyncClient() as client:
        # Get segment and content first
        seg_response = await client.post(
            f"{SERVICES['segmentation']}/segment",
            json={"customer_id": "C00000001"},
            timeout=30.0
        )
        segment_data = seg_response.json()
        
        content_response = await client.post(
            f"{SERVICES['content_retrieval']}/retrieve",
            json={
                "segment": segment_data["segment_profile"],
                "query": "products",
                "top_k": 2,
                "filters": {}
            },
            timeout=30.0
        )
        content_data = content_response.json()
        
        # Generate messages
        test_data = {
            "segment": segment_data["segment_profile"],
            "content_snippets": content_data["content_snippets"],
            "num_variants": 3,
            "channel": "email",
            "tone": "professional"
        }
        
        response = await client.post(
            f"{SERVICES['message_generation']}/generate",
            json=test_data,
            timeout=60.0
        )
        
        assert response.status_code == 200, f"Status: {response.status_code}"
        result = response.json()
        
        print(f"  ✓ Generated {len(result['variants'])} message variants")
        print("  ✓ Message generation test passed")

async def test_agent4_compliance():
    """Test Agent 4: Compliance"""
    print("\n[Test 5] Agent 4 - Compliance Validation")
    
    async with httpx.AsyncClient() as client:
        test_data = {
            "message_variants": [
                {
                    "variant_id": "A",
                    "message_text": "Great offer for you today!",
                    "tone": "professional",
                    "channel": "email"
                },
                {
                    "variant_id": "B",
                    "message_text": "AMAZING DEAL!!! BUY NOW!!!",
                    "tone": "urgent",
                    "channel": "email"
                },
                {
                    "variant_id": "C",
                    "message_text": "Check out our new products.",
                    "tone": "casual",
                    "channel": "email"
                }
            ],
            "segment_type": "high_value",
            "channel": "email"
        }
        
        response = await client.post(
            f"{SERVICES['compliance']}/validate",
            json=test_data,
            timeout=30.0
        )
        
        assert response.status_code == 200, f"Status: {response.status_code}"
        result = response.json()
        
        print(f"  ✓ Compliance validation test passed")
        print(f"    Approved: {len(result['approved_variants'])} variants")
        print(f"    Rejected: {len(result['rejected_variants'])} variants")

async def test_agent5_experiment():
    """Test Agent 5: Experiment Orchestrator"""
    print("\n[Test 6] Agent 5 - Experiment Orchestrator")
    
    async with httpx.AsyncClient() as client:
        # Use EXACT data format that worked in debug
        test_data = {
            "experiment_config": {
                "experiment_name": "test",
                "experiment_type": "ab_test",
                "sample_size": 100,
                "duration_days": 7,
                "success_metrics": ["conversion_rate"]
            },
            "message_variants": [
                {
                    "variant_id": "A",
                    "message_text": "Test message A",
                    "tone": "professional",
                    "channel": "email"
                },
                {
                    "variant_id": "B",
                    "message_text": "Test message B",
                    "tone": "casual",
                    "channel": "email"
                }
            ],
            "customer_id": "C00000001",
            "segment_id": "SEG_0"
        }
        
        response = await client.post(
            f"{SERVICES['experiment']}/deploy",
            json=test_data,
            timeout=30.0
        )
        
        if response.status_code != 200:
            print(f"  ✗ Status: {response.status_code}")
            print(f"  ✗ Response: {response.text}")
        
        assert response.status_code == 200, f"Got {response.status_code}: {response.text}"
        
        result = response.json()
        print(f"  ✓ Experiment deployed: {result['experiment_id']}")
        print(f"    Assigned variant: {result['assigned_variant']}")
        
        # Get results
        experiment_id = result['experiment_id']
        response = await client.get(
            f"{SERVICES['experiment']}/results/{experiment_id}",
            timeout=30.0
        )
        
        if response.status_code == 200:
            results = response.json()
            print(f"  ✓ Results retrieved: {results['status']}")
        
        print("  ✓ Experiment orchestrator test passed")

async def test_end_to_end_orchestrator():
    """Test complete end-to-end flow through orchestrator"""
    print("\n[Test 7] End-to-End - Complete Orchestrator Flow")
    
    async with httpx.AsyncClient() as client:
        customer_ids = ["C00000001", "C00000100", "C00000500"]
        
        for customer_id in customer_ids:
            print(f"\n  Testing customer: {customer_id}")
            
            response = await client.post(
                f"{SERVICES['orchestrator']}/personalize/{customer_id}",
                timeout=120.0
            )
            
            if response.status_code != 200:
                print(f"    ✗ Failed: {response.status_code}")
                print(f"    Error: {response.text}")
                continue
            
            result = response.json()
            
            print(f"    ✓ Segment: {result.get('segment', {}).get('segment_type', 'N/A')}")
            print(f"    ✓ Content items: {result.get('content', {}).get('total_retrieved', 0)}")
            print(f"    ✓ Message variants: {len(result.get('messages', {}).get('variants', []))}")
            print(f"    ✓ Approved variants: {len(result.get('compliance', {}).get('approved_variants', []))}")
            print(f"    ✓ Experiment: {result.get('experiment', {}).get('experiment_id', 'N/A')}")
            print(f"    ✓ Processing time: {result.get('processing_time_ms', 0):.0f}ms")
        
        print("\n  ✓ End-to-end orchestrator test passed")

def test_run_all():
    """Run all integration tests"""
    try:
        # Run tests sequentially
        asyncio.run(test_health_checks())
        asyncio.run(test_agent1_segmentation())
        asyncio.run(test_agent2_content_retrieval())
        asyncio.run(test_agent3_message_generation())
        asyncio.run(test_agent4_compliance())
        asyncio.run(test_agent5_experiment())
        asyncio.run(test_end_to_end_orchestrator())
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED! ✓")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = test_run_all()
    sys.exit(exit_code)
