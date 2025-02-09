from transformers import AutoTokenizer, AutoModelForCausalLM

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-1B")
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-1B")

# Define a prompt
prompt = "Once upon a time in a distant galaxy,"

# Tokenize input
inputs = tokenizer(prompt, return_tensors="pt")

# Generate output
output = model.generate(**inputs, max_length=50)

# Decode and print result
generated_text = tokenizer.decode(output[0], skip_special_tokens=True)
print(generated_text)
