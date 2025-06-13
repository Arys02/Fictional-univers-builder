from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
import mlflow

load_dotenv()

# Paths
PROJ_ROOT = Path(__file__).resolve().parents[1] / 'llm_core'
logger.info(f"PROJ_ROOT path is: {PROJ_ROOT}")

# data
DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# src
SRC_DIR = PROJ_ROOT / "src"

MODEL_DIR = SRC_DIR / "models"
TOKEN_DIR = SRC_DIR / "tokenizer"

# experiment config
EXPERIMENTS_CONFIG_DIR = PROJ_ROOT / "src" / "training" / "config"

#ML Flow
MLFLOW_DIR = PROJ_ROOT / "mlflow_root" / 'mlruns'
MLFLOW_PATH = f'file://{MLFLOW_DIR}'

mlflow.set_tracking_uri(MLFLOW_PATH)

logger.info(f"MLFLOW URI path is: {mlflow.get_tracking_uri()}")

# saved_tokenizer
SAVED_TOKENIZER_DIR = PROJ_ROOT / 'saved_tokenizers'

# saved_tokenizer
SAVED_MODEL_DIR = PROJ_ROOT / 'saved_models'




