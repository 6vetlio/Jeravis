import argparse
import torch
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    BitsAndBytesConfig,
    TrainingArguments,
)
from peft import LoraConfig, PeftModel
from trl import SFTTrainer


def main():
    parser = argparse.ArgumentParser(description="Fine-tune LLM with QLoRA")
    parser.add_argument("--base_model", type=str, required=True, help="Base model from Hugging Face")
    parser.add_argument("--data_file", type=str, required=True, help="Training data file (jsonl)")
    parser.add_argument("--output_dir", type=str, default="./my_model", help="Output directory")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--batch_size", type=int, default=1, help="Batch size")
    parser.add_argument("--gradient_accumulation", type=int, default=8, help="Gradient accumulation steps")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--lora_r", type=int, default=16, help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=32, help="LoRA alpha")
    parser.add_argument("--max_seq_length", type=int, default=2048, help="Maximum sequence length")
    
    args = parser.parse_args()
    
    print(f"Loading model: {args.base_model}")
    print(f"Training data: {args.data_file}")
    print(f"Output directory: {args.output_dir}")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    
    # Load dataset
    print("Loading dataset...")
    dataset = load_dataset("json", data_files=args.data_file, split="train")
    
    # Format dataset for chat
    def format_prompt(example):
        return {"text": f"User: {example['user']}\nAssistant: {example['assistant']}"}
    
    dataset = dataset.map(format_prompt)
    
    # 4-bit quantization config
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.float16,
        bnb_4bit_use_double_quant=True,
    )
    
    # Load base model
    print("Loading base model in 4-bit...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        quantization_config=bnb_config,
        device_map="auto",
        trust_remote_code=True,
    )
    model.config.use_cache = False
    model.config.pretraining_tp = 1
    
    # LoRA config
    peft_config = LoraConfig(
        lora_alpha=args.lora_alpha,
        lora_dropout=0.1,
        r=args.lora_r,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=args.output_dir,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation,
        learning_rate=args.learning_rate,
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        fp16=True,
        optim="paged_adamw_32bit",
        lr_scheduler_type="cosine",
        warmup_ratio=0.03,
        gradient_checkpointing=True,
        report_to="none",
    )
    
    # Trainer
    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        peft_config=peft_config,
        dataset_text_field="text",
        max_seq_length=args.max_seq_length,
        tokenizer=tokenizer,
        args=training_args,
        packing=False,
    )
    
    # Train
    print("Starting training...")
    trainer.train()
    
    # Save model
    print(f"Saving model to {args.output_dir}...")
    trainer.model.save_pretrained(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)
    
    # Merge LoRA weights
    print("Merging LoRA weights...")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16,
        device_map="auto",
        trust_remote_code=True,
    )
    model = PeftModel.from_pretrained(base_model, args.output_dir)
    model = model.merge_and_unload()
    model.save_pretrained(args.output_dir)
    
    print(f"Training complete! Model saved to {args.output_dir}")


if __name__ == "__main__":
    main()
