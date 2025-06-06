# Use a pipeline as a high-level helper
from transformers import pipeline

pipe = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.2")
messages = [
    {"role": "user", "content": "Who are you?"},
]

print("hello")
pipe(messages)
print()