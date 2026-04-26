#!/bin/bash
echo "Removing old qwen2.5 models and adding DeepSeek-R1 on Vast.ai..."
echo ""
echo "Removing old models..."
ollama rm qwen2.5:7b
ollama rm qwen2.5:14b
ollama rm qwen2.5:32b
echo ""
echo "Pulling DeepSeek-R1 models..."
echo "Pulling deepseek-r1:8b (~6GB)..."
ollama pull deepseek-r1:8b
echo "Pulling deepseek-r1:32b (~20GB)..."
ollama pull deepseek-r1:32b
echo ""
echo "Done! Verifying models..."
ollama list
