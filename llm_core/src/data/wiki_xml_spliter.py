import os

from tqdm import tqdm

from llm_core.config import RAW_DATA_DIR

INPUT_FILE = "/mnt/d/Documents/wikipedia/frwiki-latest-pages-articles.xml"
OUTPUT_DIR = RAW_DATA_DIR / "split_xml"
BATCH_SIZE = 500000  # nombre de <page> par fichier

os.makedirs(OUTPUT_DIR, exist_ok=True)

header = '<?xml version="1.0"?>\n<mediawiki>\n'
footer = '</mediawiki>\n'

count = 0
file_index = 0
out = None

with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    inside_page = False
    page_lines = []

    for line in tqdm(f):
        if '<page>' in line:
            inside_page = True
            page_lines = [line]
        elif '</page>' in line:
            page_lines.append(line)
            inside_page = False
            # écrire la page dans le bon fichier batch
            if count % BATCH_SIZE == 0:
                if out:
                    out.write(footer)
                    out.close()
                out_path = os.path.join(OUTPUT_DIR, f'part_{file_index:04d}.xml')
                out = open(out_path, 'w', encoding='utf-8')
                out.write(header)
                file_index += 1
            out.writelines(page_lines)
            count += 1
        elif inside_page:
            page_lines.append(line)

    # fermer le dernier fichier
    if out:
        out.write(footer)
        out.close()

print(f"✅ Fichier découpé en {file_index} batchs de {BATCH_SIZE} articles.")
