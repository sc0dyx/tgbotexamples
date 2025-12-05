from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "deepseek-ai/deepseek-vl2-tiny"
tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True)

inputs = tokenizer(
    "Привет! Напиши короткий рассказ про программиста.", return_tensors="pt"
)
outputs = model.generate(**inputs, max_length=100)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
