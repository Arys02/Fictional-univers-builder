import os
import json
import re
from llm_core.config import PROCESSED_DATA_DIR, RAW_DATA_DIR
from tqdm import tqdm

EXTRACTED_DIR = RAW_DATA_DIR / 'extracted_json'
OUTPUT_FILE = PROCESSED_DATA_DIR / "fantasy_wikipedia.txt"

SPECIAL_TOKENS = {
    "start": "<|startofarticle|>",
    "end": "<|endofarticle|>"
}

KEYWORDS = [
    "fantasy", "fantastique", "science-fiction", "sf", "mythologie", "mythe", "légende",
    "sorcellerie", "magie", "divinité", "dieu", "déesse", "fable", "conte", "folklore",
    "épopée", "héroïque", "créature", "dragon", "elfe", "nain", "magicien", "sorcier",
    "prophétie", "monstre", "univers parallèle", "quête", "royaume", "mythique"
]

pattern = re.compile(r'\b(?:' + '|'.join(KEYWORDS) + r')\b', flags=re.IGNORECASE)

# Compter le nombre de fichiers pour tqdm
all_files = []
for root, dirs, files in os.walk(EXTRACTED_DIR):
    for filename in files:
        if filename.endswith(".json"):
            all_files.append(os.path.join(root, filename))

with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
    for filepath in tqdm(all_files, desc="Filtrage des articles"):
        with open(filepath, "r", encoding="utf-8") as infile:
            for line in infile:
                try:
                    obj = json.loads(line)
                    text = obj.get("text", "")
                    if pattern.search(text):
                        clean_text = text.strip()
                        if clean_text:
                            outfile.write(f"{SPECIAL_TOKENS['start']}\n{clean_text}\n{SPECIAL_TOKENS['end']}\n\n")
                except json.JSONDecodeError:
                    continue
