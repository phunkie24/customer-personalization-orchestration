import httpx
import asyncio
import json

async def debug_agent5():
    async with httpx.AsyncClient() as client:
        # Test data
        data = {
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
                    "message_text": "Test message",
                    "tone": "professional",
                    "channel": "email"
                }
            ],
            "customer_id": "C00000001",
            "segment_id": "SEG_0"
        }
        
        print("Sending request to Agent 5...")
        try:
            response = await client.post(
                "http://localhost:5005/deploy",
                json=data,
                timeout=30.0
            )
            
            print(f"\nStatus Code: {response.status_code}")
            print(f"\nResponse Body:")
            print(response.text)
            
            if response.status_code == 200:
                print("\n✓ SUCCESS!")
            else:
                print("\n✗ FAILED!")
                
        except Exception as e:
            print(f"\n✗ ERROR: {e}")

asyncio.run(debug_agent5())
