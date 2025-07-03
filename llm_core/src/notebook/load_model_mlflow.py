#%%
import mlflow
import torch

from llm_core.src.tokenizer.bpe_tokenizer import BPETokenizer
from llm_core.src.tokenizer.tiktoken_tokenizer import TiktokenTokenizer


#%%
from llm_core.config import MLFLOW_PATH
from llm_core.src.tokenizer.transformers_tokenizer import TransformersTokenizer

print("Tracking URI:", mlflow.get_tracking_uri())
#%%
experiments = mlflow.search_experiments()
for exp in experiments:
    print(f"ID: {exp.experiment_id} - Name: {exp.name}")
#%%
runs = mlflow.search_runs(experiment_ids=["0"])

print("Tous les run_id disponibles dans l'expérience 0 :")
for rid in runs["run_id"]:
    print("-", rid)
#%%
from llm_core.src.models.gpt2 import GPT2
from llm_core.src.models.gpt import GPTModel

experiment_id = "494534413940730003"
run_id = "98f938de200d4310b9ea8d3f0d17c067"
model : GPT2 = mlflow.pytorch.load_model(f"{MLFLOW_PATH}/{experiment_id}/{run_id}/artifacts/gpt2")
#%%
from llm_core.config import RAW_DATA_DIR, SAVED_TOKENIZER_DIR
from llm_core.src.tokenizer.char_tokenizer import CharTokenizer

# with open(RAW_DATA_DIR / 'sheakspear_input.txt', 'r', encoding='utf-8') as f:
#     text = f.read()
# 
# 
# 
# tokenizer = BPETokenizer(SAVED_TOKENIZER_DIR / 'tokenizer_sheakspear.json') 
#tokenizer = TiktokenTokenizer('gpt2')

tokenizer = TransformersTokenizer()

#%%
print(model.generate_text(500, tokenizer))
#%%
