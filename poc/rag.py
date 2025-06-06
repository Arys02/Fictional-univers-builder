import numpy as np
import pandas as pd

import sqlite3

from sentence_transformers import SentenceTransformer
import faiss

from ollama import chat, ChatResponse


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
def get_text_chunks_from_db(db_path, univers_id):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Liste des tables
    ## ATTENTION: j'ai précisé des noms de tables en dur
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name in ('univers', 'faction', 'location', 'culture');")
    table_names = [row[0] for row in cursor.fetchall()]

    all_chunks = []

    for table in table_names:
        try:

            if table == "univers":
                df = pd.read_sql_query(f"SELECT * FROM {table} WHERE id = {univers_id}", conn)
                if df.empty:
                    continue
     
                df["uid"] = df["id"]
            else:
                df = pd.read_sql_query(f"SELECT * FROM {table} WHERE univers_id = {univers_id}", conn)
                if df.empty:
                    continue
                df["uid"] = df["univers_id"]

            df["text"] = extract_textual_columns(df)
            df["source_table"] = table

            all_chunks.append(df[["id", "text", "source_table", "uid"]])
        except Exception as e:
            print(f"Erreur sur la table {table} : {e}")

    # Fusion de tous les documents
    full_df = pd.concat(all_chunks, ignore_index=True)
    return full_df

def create_faiss_index(df, model):
    # Simple chunking : on encode tout le contenu tel quel ici
    df["embedding"] = df["text"].apply(lambda x: model.encode(x))

    # Préparer pour FAISS
    embeddings = np.vstack(df["embedding"].values)
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index

# Elle sert à retrouver les k documents les plus pertinents par similarité vectorielle à une question posée
def search(question, df, model, index, k=3):
    query_embedding = model.encode(question)
    D, I = index.search(np.array([query_embedding]), k)
    results = df.iloc[I[0]]
    return results

def rag_answer(question, df, model, index):
    search_result = search(question, df, model, index)
    context = "\n\n".join(f"[{row['source_table'].upper()}] {row['text']}" for _, row in search_result.iterrows())

    prompt = f"""Voici des extraits de documentation :

    {context}

    Question : {question}
    Réponds de manière précise à la question en t'appuyant sur les extraits fournis uniquement."""

    response: ChatResponse = chat(
        model="llama3.2",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.message.content


if __name__ == "__main__":
    model = SentenceTransformer("all-MiniLM-L6-v2")
    db_path = 'database.db'
    concat_df = get_text_chunks_from_db(db_path, 2)

    index = create_faiss_index(concat_df, model)

    question = "Quelle sont les factions présentes dans l'univers ?"
    # results = search(question, concat_df, model, index)

    print(rag_answer(question, concat_df, model, index))
