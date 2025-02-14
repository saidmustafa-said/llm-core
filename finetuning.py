"""
Fine-Tuning Meta‑Llama/Llama‑3.2‑3B for a Query-to-JSON Retrieval Task

This script fine-tunes a causal language model (Meta‑Llama) on a custom task:
when provided with a query (e.g., "I'm in Esenyurt and I'm looking for the closest mall"),
the model will generate a JSON-formatted answer (including fields such as name, description,
coordinates, etc.) from your dataset.

Each training example should be a JSON object with:
    "input_text": The query prompt.
    "target_text": The JSON-formatted answer.
    
The script covers:
    - Dataset loading and preprocessing.
    - A custom preprocessing function that concatenates prompt and answer.
    - Data collator for dynamic padding.
    - Advanced training arguments (mixed precision, gradient accumulation, gradient clipping).
    - A gradient test to ensure gradients are flowing.
    - A custom Trainer callback that logs gradient norms every step.
    - An evaluation function (using ROUGE) to compare generated outputs.
    - A testing/inference loop that uses beam search to generate answers from the test set.
"""

import os
import json
import numpy as np
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    Trainer,
    TrainingArguments,
    DataCollatorForLanguageModeling,
    TrainerCallback,
)
import torch
import evaluate
from tqdm.auto import tqdm

print(
    f"Using device: {torch.device('cuda' if torch.cuda.is_available() else 'cpu')}")
print(
    f"Using device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")


# =============================================================================
# 1. MODEL AND DEVICE SETUP
# =============================================================================
# We fine-tune the Meta‑Llama model available on Hugging Face.
model_checkpoint = "meta-llama/Llama-3.2-1B"  # Model name on Hugging Face Hub
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load the tokenizer and model.
# (Note: Depending on your installation and the model repo, you might need to pass
#  additional arguments such as `trust_remote_code=True`.)
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint, use_fast=False)
model = AutoModelForCausalLM.from_pretrained(model_checkpoint)
model.to(device)

# =============================================================================
# 2. DATA LOADING
# =============================================================================
# We assume your data is stored in JSON files with the following keys:
#    "input_text"  : user query
#    "target_text" : JSON answer
# Provide paths to your training, evaluation, and test files.
data_files = {
    "train": "data2/train_data.json",         # Path to your training data
    "validation": "data2/eval_data.json",       # Path to your validation data
    # Path to your test data (for inference)
    "test": "data2/test_data.json",
}
raw_datasets = load_dataset("json", data_files=data_files)

# =============================================================================
# 3. PREPROCESSING FUNCTION
# =============================================================================
# For causal LM fine-tuning, we combine the input query and its corresponding answer
# into one text. A delimiter ("\nAnswer: ") is used to signal the beginning of the answer.


def preprocess_function(examples):
    texts = []
    for inp, tgt in zip(examples["input_text"], examples["target_text"]):
        full_text = inp.strip() + "\nAnswer: " + tgt.strip() + tokenizer.eos_token
        texts.append(full_text)
    # Tokenize the full text. We use truncation and a max_length; adjust as needed.
    tokenized = tokenizer(texts, truncation=True, max_length=1024)
    # For causal LM, our labels are the same as the input IDs.
    tokenized["labels"] = tokenized["input_ids"].copy()
    return tokenized


# Apply the preprocessing function to all splits (train/validation).
# We remove the original columns as they are no longer needed for training.
tokenized_datasets = raw_datasets.map(
    preprocess_function,
    batched=True,
    remove_columns=raw_datasets["train"].column_names,
)

# =============================================================================
# 4. DATA COLLATOR
# =============================================================================
# The data collator dynamically pads each batch to the longest sequence.
data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

# =============================================================================
# 5. TRAINING ARGUMENTS (ADVANCED)
# =============================================================================
# Here we set various advanced training options:
#   - Mixed precision (fp16) for faster training.
#   - Gradient accumulation to simulate a larger batch size.
#   - Gradient clipping via max_grad_norm.
# training_args = TrainingArguments(
#     # Directory to store checkpoints and logs.
#     output_dir="./llama_finetuned",
#     evaluation_strategy="epoch",          # Evaluate at the end of each epoch.
#     learning_rate=3e-5,
#     per_device_train_batch_size=2,        # Adjust based on your GPU memory.
#     per_device_eval_batch_size=2,
#     gradient_accumulation_steps=8,        # Effective batch size = 2*8 = 16.
#     num_train_epochs=3,
#     weight_decay=0.01,
#     logging_steps=10,
#     save_total_limit=3,
#     fp16=True,                          # Enable mixed precision training.
#     max_grad_norm=1.0,                  # Clip gradients to this norm.
#     # Use model.generate() during evaluation.
#     # predict_with_generate=True,
#     # Change to "tensorboard"/"wandb" for advanced logging.
#     report_to="none",
# )

training_args = TrainingArguments(
    # Directory to store checkpoints and logs.
    output_dir="./llama_finetuned",
    evaluation_strategy="epoch",          # Evaluate at the end of each epoch.
    learning_rate=3e-5,
    per_device_train_batch_size=2,        # Adjust based on your GPU memory.
    per_device_eval_batch_size=2,
    gradient_accumulation_steps=8,        # Effective batch size = 2*8 = 16.
    num_train_epochs=3,
    weight_decay=0.01,
    logging_steps=10,
    save_total_limit=3,
    fp16=True,                          # Enable mixed precision training.
    max_grad_norm=1.0,                  # Clip gradients to this norm.
    # Change to "tensorboard"/"wandb" for advanced logging.
    report_to="none",
)


# =============================================================================
# 6. CUSTOM CALLBACK: GRADIENT LOGGING
# =============================================================================
# This callback computes and logs the L2 norm of gradients at the end of each step.


class GradientLoggingCallback(TrainerCallback):
    def on_step_end(self, args, state, control, model=None, **kwargs):
        total_norm = 0.0
        for name, param in model.named_parameters():
            if param.grad is not None:
                param_norm = param.grad.detach().data.norm(2)
                total_norm += param_norm.item() ** 2
        total_norm = total_norm ** 0.5
        print(f"[Step {state.global_step}] Gradient Norm: {total_norm:.4f}")


# =============================================================================
# 7. EVALUATION METRIC: COMPUTE ROUGE
# =============================================================================
# We use ROUGE (via the evaluate library) to compare generated outputs to the targets.
rouge_metric = evaluate.load("rouge")


def compute_metrics(eval_pred):
    predictions, labels = eval_pred
    # Replace -100 (masked positions) in the labels with the pad token id.
    labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
    decoded_preds = tokenizer.batch_decode(
        predictions, skip_special_tokens=True)
    decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
    result = rouge_metric.compute(
        predictions=decoded_preds,
        references=decoded_labels,
        use_stemmer=True,
    )
    # Format ROUGE scores: here we report F-measure * 100.
    result = {key: value.mid.fmeasure * 100 for key, value in result.items()}
    return result

# =============================================================================
# 8. GRADIENT TEST FUNCTION
# =============================================================================
# Before training, we perform a gradient test on a single sample to verify that gradients flow.


def gradient_test():
    sample = tokenized_datasets["train"][0]
    # Prepare tensors and add a batch dimension.
    input_ids = torch.tensor(sample["input_ids"]).unsqueeze(0).to(device)
    attention_mask = torch.tensor(
        sample["attention_mask"]).unsqueeze(0).to(device)
    labels = torch.tensor(sample["labels"]).unsqueeze(0).to(device)
    model.train()
    outputs = model(input_ids=input_ids,
                    attention_mask=attention_mask, labels=labels)
    loss = outputs.loss
    loss.backward()
    grad_norm = 0.0
    for param in model.parameters():
        if param.grad is not None:
            grad_norm += param.grad.norm().item() ** 2
    grad_norm = grad_norm ** 0.5
    print(
        f"Gradient Test -> Loss: {loss.item():.4f}, Gradient Norm: {grad_norm:.4f}")


# Run the gradient test.
gradient_test()

# =============================================================================
# 9. INITIALIZE THE TRAINER
# =============================================================================
# trainer = Trainer(
#     model=model,
#     args=training_args,
#     train_dataset=tokenized_datasets["train"],
#     eval_dataset=tokenized_datasets["validation"],
#     tokenizer=tokenizer,
#     data_collator=data_collator,
#     compute_metrics=compute_metrics,
#     callbacks=[GradientLoggingCallback()],
#     predict_with_generate=True,
# )

trainer = Trainer(
    model=model,
    args=training_args,  # Use the training arguments without generation_kwargs
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["validation"],
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
    callbacks=[GradientLoggingCallback()],
)


# =============================================================================
# 10. TRAINING
# =============================================================================
# Start fine-tuning. Checkpoints, logs, and evaluations will be saved per the training_args.
trainer.train()

# Save the fine-tuned model and tokenizer.
trainer.save_model("./llama_finetuned_final")
tokenizer.save_pretrained("./llama_finetuned_final")

# =============================================================================
# 11. TESTING / INFERENCE
# =============================================================================
# Now we use the (raw) test set for generating answers.
# For each test sample, we only feed the "input_text" (the query) to the model,
# and then generate a completion which should ideally be the JSON answer.


def generate_answer(example):
    prompt = example["input_text"].strip() + "\nAnswer: "
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    # Generate output using beam search for higher-quality generations.
    output_ids = model.generate(
        inputs["input_ids"],
        attention_mask=inputs["attention_mask"],
        max_length=512,
        num_beams=5,
        early_stopping=True,
    )
    generated_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    # If the generated text repeats the prompt, remove it.
    if generated_text.startswith(prompt):
        generated_text = generated_text[len(prompt):].strip()
    return generated_text


# Evaluate the model on the test set.
test_dataset = raw_datasets["test"]
references = []
predictions = []
print("\n--- Generating answers on test set ---")
for example in tqdm(test_dataset, desc="Testing"):
    pred = generate_answer(example)
    predictions.append(pred)
    references.append(example["target_text"])

# Compute ROUGE scores on the test set.
test_rouge = rouge_metric.compute(
    predictions=predictions,
    references=references,
    use_stemmer=True,
)
test_rouge = {key: value.mid.fmeasure *
              100 for key, value in test_rouge.items()}
print("\nTest ROUGE Scores:")
for k, v in test_rouge.items():
    print(f"{k}: {v:.2f}")

# Print a few examples for manual inspection.
print("\nSample Generations:")
for i in range(3):
    print(f"\nInput: {test_dataset[i]['input_text']}")
    print(f"Target: {test_dataset[i]['target_text']}")
    print(f"Prediction: {predictions[i]}")
