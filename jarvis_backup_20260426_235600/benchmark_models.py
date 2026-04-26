"""
Model Benchmarking Script for Jarvis
Tests different models and quantization levels on RTX 4070 (12GB VRAM)
"""
import ollama
import time
import subprocess
import json
import os

# Models to test (using actual installed models)
MODELS_TO_TEST = [
    {"name": "qwen2.5:7b", "description": "Fast model, baseline"},
    {"name": "qwen2.5:14b", "description": "General purpose, sweet spot"},
    {"name": "qwen2.5-coder:32b-instruct-q4_K_M", "description": "Large coding model, max capability"},
]

# Test queries (simplified for faster testing)
TEST_QUERIES = [
    {"type": "simple", "query": "Hi"},
    {"type": "medium", "query": "What is AI?"},
]

def get_vram_usage():
    """Get current VRAM usage using nvidia-smi"""
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            used, total = result.stdout.strip().split(",")
            return int(used), int(total)
    except Exception as e:
        print(f"Error getting VRAM: {e}")
    return 0, 0

def benchmark_model(model_name):
    """Benchmark a specific model"""
    print(f"\n{'='*60}")
    print(f"Benchmarking: {model_name}")
    print(f"{'='*60}")
    
    results = {
        "model": model_name,
        "tests": []
    }
    
    # Check if model exists - if not, skip
    try:
        models = ollama.list()
        model_names = []
        if "models" in models:
            model_names = [m.model for m in models["models"]]
        
        if model_name not in model_names:
            print(f"Model {model_name} not found, skipping...")
            return None
        else:
            print(f"Model {model_name} found!")
    except Exception as e:
        print(f"Error checking model: {e}")
        return None
    
    for test in TEST_QUERIES:
        print(f"\nTest: {test['type']} - {test['query'][:50]}...")
        
        # Get VRAM before
        vram_before, vram_total = get_vram_usage()
        
        # Run inference with timeout
        start_time = time.time()
        try:
            response = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": test['query']}],
                stream=True,
                options={"num_predict": 200}  # Limit response length for benchmarking
            )
            
            full_response = ""
            chunk_count = 0
            for chunk in response:
                chunk_count += 1
                if chunk_count % 10 == 0:
                    print(f"  Progress: {chunk_count} chunks...")
                if 'message' in chunk and 'content' in chunk['message']:
                    full_response += chunk['message']['content']
                
                # Safety timeout
                if time.time() - start_time > 30:  # 30 second timeout
                    print(f"  Timeout after 30s")
                    break
            
            inference_time = time.time() - start_time
            response_length = len(full_response)
            
            # Get VRAM after
            vram_after, _ = get_vram_usage()
            vram_used = vram_after - vram_before
            
            result = {
                "type": test['type'],
                "query": test['query'],
                "inference_time": round(inference_time, 2),
                "response_length": response_length,
                "vram_used_mb": vram_used,
                "vram_total_mb": vram_total,
                "tokens_per_second": round(response_length / inference_time, 2) if inference_time > 0 else 0
            }
            results["tests"].append(result)
            
            print(f"  Time: {inference_time:.2f}s")
            print(f"  VRAM used: {vram_used}MB")
            print(f"  Tokens/sec: {result['tokens_per_second']}")
            print(f"  Response preview: {full_response[:100]}...")
            
        except Exception as e:
            print(f"  Error: {e}")
            results["tests"].append({
                "type": test['type'],
                "error": str(e)
            })
    
    return results

def main():
    """Run all benchmarks"""
    print("Jarvis Model Benchmarking Script")
    print(f"Testing on RTX 4070 (12GB VRAM)")
    print("="*60)
    
    all_results = []
    
    for model_info in MODELS_TO_TEST:
        result = benchmark_model(model_info["name"])
        if result:
            result["description"] = model_info["description"]
            all_results.append(result)
    
    # Save results
    output_file = "benchmark_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    
    print(f"\n{'='*60}")
    print("Benchmark complete!")
    print(f"Results saved to: {output_file}")
    print("="*60)
    
    # Print summary
    print("\nSummary:")
    for result in all_results:
        model = result["model"]
        desc = result["description"]
        avg_time = sum([t.get("inference_time", 0) for t in result["tests"] if "error" not in t]) / len([t for t in result["tests"] if "error" not in t])
        max_vram = max([t.get("vram_used_mb", 0) for t in result["tests"]])
        print(f"  {model} ({desc}):")
        print(f"    Avg time: {avg_time:.2f}s")
        print(f"    Max VRAM: {max_vram}MB")

if __name__ == "__main__":
    main()
