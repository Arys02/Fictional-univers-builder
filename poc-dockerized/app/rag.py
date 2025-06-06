import numpy as np
import pandas as pd
import json

import sqlite3
from db_path import get_db_path

from sentence_transformers import SentenceTransformer
import faiss

from ollama import chat, ChatResponse


def get_all_table_schemas(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
    tables = [row[0] for row in cursor.fetchall()]

    schemas = {}

    for table in tables:
        cursor.execute(f"PRAGMA table_info({table});")
        schema = cursor.fetchall()
        schemas[table] = [
            {"name": col[1], "type": col[2], "notnull": bool(col[3]), "default": col[4], "primary_key": bool(col[5])}
            for col in schema
        ]

    conn.close()
    return schemas

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

def rag_answer(question, univers_id):
    model = SentenceTransformer("all-MiniLM-L6-v2")
    df = get_text_chunks_from_db(get_db_path(), univers_id)
    index = create_faiss_index(df, model)

    search_result = search(question, df, model, index, 20)
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

def rag_update_db(request, univers_id):
    context = get_all_table_schemas(get_db_path())

    formatted_schema = json.dumps(context, indent=2)

    prompt = f"""Tu es un assistant qui génère du SQL pour mettre à jour une base SQLite.

    Voici les schémas des tables de la base de données, les ID sont en AutoIncrement :

    {formatted_schema}

    Voici la requête utilisateur :
    "{request}"

    Écris uniquement le script SQL nécessaire pour mettre à jour la base en fonction de la requête.
    - N'écris **aucun commentaire**, **aucune explication**.
    - Si une jointure ou une vérification est nécessaire, fais-le.
    - Utilise l'univers_id suivant pour lier les données : {univers_id}

    Exemple :
    Si la requête est "Ajoute moi la faction Le Clan de l'Eau avec une description", alors le SQL généré doit être :

    INSERT INTO faction (name, description, univers_id) VALUES ('Le Clan de l'Eau', 'Les elfes démoniaques du Clan de L'Eau sont connus pour leur agressivité et leur passion pour le thrash metal. Ils sont réputés pour leurs concerts de plus de 2 heures d'heureux vacarme.', 2);
    """

    response: ChatResponse = chat(
        model="llama3.2",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.message.content.strip()


if __name__ == "__main__":
    # model = SentenceTransformer("all-MiniLM-L6-v2")
    # db_path = 'database.db'
    # concat_df = get_text_chunks_from_db(db_path, 2)

    # index = create_faiss_index(concat_df, model)

    # question = "Quelles sont les factions présentes dans l'univers ?"
    question = "Rajoute moi la faction des Singes Géants, rajoute y une description"
    # results = search(question, concat_df, model, index)

    # print(rag_answer(question, 2))
    script = rag_update_db(question, 3)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute(script)
    conn.commit()
    conn.close()

