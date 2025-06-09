from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

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




