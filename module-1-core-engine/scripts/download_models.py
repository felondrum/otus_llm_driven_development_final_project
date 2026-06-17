# Скачивание моделей

import asyncio
import aiohttp
import json


async def download_model(model_name: str, base_url: str = "http://localhost:11434"):
    """Download a model from Ollama."""
    url = f"{base_url}/api/pull"
    
    async with aiohttp.ClientSession() as session:
        payload = {"name": model_name}
        
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                result = await response.json()
                print(f"Model {model_name} downloaded successfully")
                return result
            else:
                error_text = await response.text()
                print(f"Failed to download model {model_name}: {error_text}")
                return None


async def list_models(base_url: str = "http://localhost:11434"):
    """List available models in Ollama."""
    url = f"{base_url}/api/tags"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                result = await response.json()
                models = result.get('models', [])
                print("Available models:")
                for model in models:
                    print(f"  - {model.get('name')}")
                return models
            else:
                error_text = await response.text()
                print(f"Failed to list models: {error_text}")
                return []


async def main():
    """Main function."""
    print("Checking Ollama models...")
    
    models = await list_models()
    
    if models is None:
        print("Ollama is not running. Please start Ollama first.")
        return
    
    # Models to download
    models_to_download = [
        "qwen2.5:1.5b",
        "nomic-embed-text"
    ]
    
    for model in models_to_download:
        if model not in [m.get('name') for m in models]:
            print(f"Downloading {model}...")
            await download_model(model)
        else:
            print(f"{model} already downloaded")


if __name__ == "__main__":
    asyncio.run(main())
