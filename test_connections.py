import asyncio
import os
import boto3
import aiohttp

async def test_digital_ocean():
    """Test Digital Ocean Spaces connection"""
    try:
        s3_client = boto3.client(
            's3',
            endpoint_url=f"https://{os.getenv('DO_SPACES_REGION')}.digitaloceanspaces.com",
            aws_access_key_id=os.getenv('DO_SPACES_ACCESS_KEY'),
            aws_secret_access_key=os.getenv('DO_SPACES_SECRET_KEY')
        )
        
        # List files in contracts bucket
        response = s3_client.list_objects_v2(Bucket=os.getenv('DO_SPACES_BUCKET_NAME'), MaxKeys=5)
        files = [obj['Key'] for obj in response.get('Contents', [])]
        
        print("✅ Digital Ocean connection working!")
        print(f"Sample files: {files[:3]}")
        return True
        
    except Exception as e:
        print(f"❌ Digital Ocean error: {e}")
        return False

async def test_ollama():
    """Test RunPod Ollama connection"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": "llama3.1:8b",
                "prompt": "Quick test: What is 2+2?",
                "stream": False
            }
            
            async with session.post(f"{os.getenv('OLLAMA_BASE_URL')}/api/generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    print("✅ RunPod Ollama connection working!")
                    return True
                else:
                    print(f"❌ Ollama error: {response.status}")
                    return False
                    
    except Exception as e:
        print(f"❌ Ollama error: {e}")
        return False

async def main():
    print("Testing connections...")
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    do_works = await test_digital_ocean()
    ollama_works = await test_ollama()
    
    if do_works and ollama_works:
        print("\n🎉 Both connections working! Ready to analyze contracts!")
    else:
        print("\n❌ Fix connection issues before proceeding")

if __name__ == "__main__":
    asyncio.run(main())
