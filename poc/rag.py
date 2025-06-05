import numpy as np
import pandas as pd

import sqlite3

# conn = sqlite3.connect('database.db')
# cursor = conn.cursor()

# table_name = 'univers'


#%%
def extract_textual_columns(df):
    textual_cols = df.select_dtypes(include=["object"]).columns

    def row_to_labeled_text(row):
        parts = []
        for col in textual_cols:
            val = row[col]
            if pd.notnull(val) and str(val).strip():
                parts.append(f"{col}: {val}")
        return "\n".join(parts)

    return df.apply(row_to_labeled_text, axis=1)

# Loop sur chaque table pour concat chaque colonnes textuelles et n'avoir qu'une colonne text
def get_text_chunks_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Liste des tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = [row[0] for row in cursor.fetchall()]

    print(table_names)

    all_chunks = []

    for table in table_names:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
            if df.empty:
                continue

            df["text"] = extract_textual_columns(df)
            df["source_table"] = table

            all_chunks.append(df[["id", "text", "source_table"]])
        except Exception as e:
            print(f"Erreur sur la table {table} : {e}")

    # Fusion de tous les documents
    full_df = pd.concat(all_chunks, ignore_index=True)
    return full_df



if __name__ == "__main__":
    db_path = 'database.db'
    concat_df = get_text_chunks_from_db(db_path)
    print(concat_df)
