import os
import subprocess

from tqdm import tqdm

from llm_core.config import PROCESSED_DATA_DIR
from llm_core.config import RAW_DATA_DIR

SPLIT_DIR = RAW_DATA_DIR / "split_xml"
OUTPUT_DIR = RAW_DATA_DIR / "extracted_json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

xml_files = sorted(f for f in os.listdir(SPLIT_DIR) if f.endswith(".xml"))
print(xml_files)

for xml_file in tqdm(xml_files):
    input_path = os.path.join(SPLIT_DIR, xml_file)
    batch_name = os.path.splitext(xml_file)[0]
    output_path = os.path.join(OUTPUT_DIR, batch_name)

    print(f"➡️ Extraction de : {input_path}")

    # Commande WikiExtractor
    cmd = [
        "python3", "-m", "wikiextractor.WikiExtractor",
        "--json",
        "-o", output_path,
        input_path
    ]

    print("Running subprocess")
    subprocess.run(cmd)

