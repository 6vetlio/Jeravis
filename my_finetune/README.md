# Simple LLM Fine-Tuning for LM Studio

Fine-tune an existing LLM with QLoRA on your custom data and use it in LM Studio.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Your Training Data

Edit `train.jsonl` with your conversations:

```jsonl
{"user": "your input", "assistant": "desired response"}
{"user": "another input", "assistant": "another response"}
```

You can also use existing conversations from Jarvis history or other sources.

### 3. Fine-Tune with QLoRA

```bash
python finetune.py \
  --base_model Qwen/Qwen2.5-7B-Instruct \
  --data_file train.jsonl \
  --output_dir ./my_model \
  --epochs 3 \
  --batch_size 1 \
  --gradient_accumulation 8
```

**Parameters:**
- `--base_model`: Hugging Face model to fine-tune (7B-20B range recommended for RTX 4070 8GB)
- `--data_file`: Your training data file (jsonl format)
- `--output_dir`: Where to save the fine-tuned model
- `--epochs`: Number of training epochs (default: 3)
- `--batch_size`: Batch size (default: 1, keep low for 8GB VRAM)
- `--gradient_accumulation`: Gradient accumulation steps (default: 8)

### 4. Load in LM Studio

LM Studio can load Hugging Face models directly:

1. Open LM Studio
2. Add model → Select local model
3. Browse to `./my_model` directory
4. Start chatting with your fine-tuned model

**Optional GGUF Conversion:**
If you prefer GGUF format, use llama.cpp:
```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
python convert.py ../my_model --outfile ../my_model.gguf --outtype q4_k_m
```

## Recommended Base Models

For RTX 4070 8GB VRAM:
- **7B models**: Qwen2.5-7B-Instruct, Mistral-7B-Instruct, Phi-3-mini
- **14B models**: Qwen2.5-14B-Instruct (may need lower batch size)
- **20B models**: Qwen2.5-20B-Instruct (use QLoRA, may be slow)

## Training Tips

- Start with a small dataset (100-1000 examples) to test
- Use more epochs (5-10) for small datasets
- Use fewer epochs (1-3) for large datasets
- Monitor training loss - should decrease steadily
- Adjust learning rate if training is unstable (try 5e-5 or 1e-4)

## Hardware Requirements

- GPU: RTX 4070 8GB VRAM (or similar)
- RAM: 32GB recommended
- Storage: 20GB+ for model weights

## Estimated Time

- Setup: 30 minutes
- Data prep: 1-2 hours
- Training: 6-24 hours (depends on data size and model)
- Total: 1-2 days

## Files

- `finetune.py` - QLoRA training script
- `convert_to_gguf.py` - GGUF conversion helper
- `train.jsonl` - Training data template
- `requirements.txt` - Python dependencies
