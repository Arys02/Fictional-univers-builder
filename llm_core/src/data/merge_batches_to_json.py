import os
from tqdm import tqdm


from llm_core.config import PROCESSED_DATA_DIR, RAW_DATA_DIR

BASE_DIR = RAW_DATA_DIR / 'extracted_json'
OUTPUT_DIR = PROCESSED_DATA_DIR / "merge_json"

os.makedirs(output_dir, exist_ok=true)

# on récupère les dossiers part_*
part_dirs = sorted(d for d in os.listdir(base_dir) if d.startswith("part_"))

for part in tqdm(part_dirs, desc="fusion des batches"):
    part_path = os.path.join(base_dir, part)
    output_file = os.path.join(output_dir, f"{part}.json")

    with open(output_file, "w", encoding="utf-8") as out:
        for root, _, files in os.walk(part_path):
            for file in files:
                if file.startswith("wiki_"):
                    file_path = os.path.join(root, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        for line in f:
                            out.write(line)
