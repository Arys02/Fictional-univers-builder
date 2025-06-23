import numpy as np
import pandas as pd
import json
import pickle
import os
from pathlib import Path

import sqlite3
from db_path import get_db_path

from sentence_transformers import SentenceTransformer
import faiss

from ollama import chat, ChatResponse

# Cache pour les modèles et index
_model_cache = {}
_index_cache = {}
_data_cache = {}

def get_cached_model(model_name="all-MiniLM-L6-v2"):
    """Récupère ou charge le modèle d'embedding avec cache"""
    if model_name not in _model_cache:
        print(f"Chargement du modèle {model_name}...")
        _model_cache[model_name] = SentenceTransformer(model_name)
    return _model_cache[model_name]

def get_cache_key(univers_id, model_name="all-MiniLM-L6-v2"):
    """Génère une clé de cache unique"""
    return f"{model_name}_{univers_id}"

def get_cached_data(univers_id, model_name="all-MiniLM-L6-v2"):
    """Récupère les données avec cache"""
    cache_key = get_cache_key(univers_id, model_name)
    
    if cache_key not in _data_cache:
        print(f"Chargement des données pour l'univers {univers_id}...")
        _data_cache[cache_key] = get_text_chunks_from_db(get_db_path(), univers_id)
    
    return _data_cache[cache_key]

def get_cached_index(univers_id, model_name="all-MiniLM-L6-v2"):
    """Récupère l'index FAISS avec cache"""
    cache_key = get_cache_key(univers_id, model_name)
    
    if cache_key not in _index_cache:
        print(f"Création de l'index pour l'univers {univers_id}...")
        model = get_cached_model(model_name)
        df = get_cached_data(univers_id, model_name)
        _index_cache[cache_key] = create_faiss_index(df, model)
    
    return _index_cache[cache_key]

def clear_cache(univers_id=None):
    """Nettoie le cache pour un univers spécifique ou tout le cache"""
    global _data_cache, _index_cache
    
    if univers_id is None:
        _data_cache.clear()
        _index_cache.clear()
        print("Cache complètement vidé")
    else:
        # Supprimer les entrées pour cet univers
        keys_to_remove = [k for k in _data_cache.keys() if str(univers_id) in k]
        for key in keys_to_remove:
            del _data_cache[key]
            if key in _index_cache:
                del _index_cache[key]
        print(f"Cache vidé pour l'univers {univers_id}")

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

    # Liste des tables à inclure dans la recherche RAG
    # Ajout de plus de tables pour une recherche plus complète
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN (
            'univers', 'faction', 'location', 'culture', 
            'character', 'quest', 'item', 'creature', 
            'event', 'technology_magic'
        )
    """)
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

            # Amélioration de l'extraction de texte
            df["text"] = extract_textual_columns_improved(df, table)
            df["source_table"] = table

            all_chunks.append(df[["id", "text", "source_table", "uid"]])
        except Exception as e:
            print(f"Erreur sur la table {table} : {e}")

    # Fusion de tous les documents
    if all_chunks:
        full_df = pd.concat(all_chunks, ignore_index=True)
        # Filtrer les chunks vides
        full_df = full_df[full_df["text"].str.strip() != ""]
        return full_df
    else:
        # Retourner un DataFrame vide avec les bonnes colonnes
        return pd.DataFrame(columns=["id", "text", "source_table", "uid"])

def extract_textual_columns_improved(df, table_name):
    """Extraction améliorée des colonnes textuelles avec contexte"""
    textual_cols = df.select_dtypes(include=["object"]).columns

    def row_to_labeled_text(row):
        parts = []
        
        # Ajouter le nom de la table comme contexte
        parts.append(f"Type: {table_name.upper()}")
        
        for col in textual_cols:
            val = row[col]
            if pd.notnull(val) and str(val).strip():
                # Améliorer le formatage selon le type de colonne
                if col == "name":
                    parts.append(f"Nom: {val}")
                elif col == "description":
                    parts.append(f"Description: {val}")
                else:
                    parts.append(f"{col}: {val}")
        
        return "\n".join(parts)

    return df.apply(row_to_labeled_text, axis=1)

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

def rag_answer(question, univers_id, k=5):
    """Répond à une question en utilisant RAG avec cache optimisé"""
    try:
        # Utiliser le cache pour les modèles et données
        model = get_cached_model()
        df = get_cached_data(univers_id)
        index = get_cached_index(univers_id)
        
        # Recherche avec score de similarité
        search_result = search_with_scores(question, df, model, index, k)
        
        # Filtrer les résultats avec un seuil de similarité
        threshold = 0.3  # Seuil de similarité
        filtered_results = search_result[search_result['similarity_score'] > threshold]
        
        if filtered_results.empty:
            return "Je n'ai pas trouvé d'informations pertinentes dans la base de données pour répondre à votre question. Pouvez-vous reformuler ou préciser votre demande ?"
        
        # Construire le contexte avec les sources
        context_parts = []
        for _, row in filtered_results.iterrows():
            source_info = f"[{row['source_table'].upper()}]"
            context_parts.append(f"{source_info}\n{row['text']}")
        
        context = "\n\n---\n\n".join(context_parts)
        
        # Prompt amélioré
        prompt = f"""Tu es un assistant spécialisé dans les univers de fiction et de jeu de rôle (D&D). 
        
        Voici des extraits de documentation sur l'univers :

        {context}

        Question : {question}
        
        Instructions :
        1. Réponds de manière précise en t'appuyant UNIQUEMENT sur les extraits fournis
        2. Si l'information n'est pas dans les extraits, dis-le clairement
        3. Sois immersif et parle comme un Dungeon Master passionné
        4. Cite les sources quand c'est pertinent (ex: "Selon les archives des factions...")
        5. Réponds en français de manière naturelle et engageante
        """

        response: ChatResponse = chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}]
        )
        
        return response.message.content
        
    except Exception as e:
        print(f"Erreur dans rag_answer: {str(e)}")
        return f"Une erreur s'est produite lors de la recherche : {str(e)}"

def search_with_scores(question, df, model, index, k=5):
    """Recherche avec scores de similarité"""
    query_embedding = model.encode(question)
    D, I = index.search(np.array([query_embedding]), k)
    
    results = df.iloc[I[0]].copy()
    results['similarity_score'] = 1 / (1 + D[0])  # Convertir la distance en score de similarité
    
    return results.sort_values('similarity_score', ascending=False)

def rag_update_db(request, univers_id):
    context = get_all_table_schemas(get_db_path())

    formatted_schema = json.dumps(context, indent=2)

    is_syntax_valid = False

    while not is_syntax_valid:
        prompt = f"""Tu es un assistant qui génère du SQL pour mettre à jour une base SQLite.

        Voici les schémas des tables de la base de données, les ID sont en AutoIncrement :

        {formatted_schema}

        Voici la requête utilisateur :
        "{request}"

        Écris uniquement le script SQL nécessaire pour mettre à jour la base en fonction de la requête.
        - N'écris **aucun commentaire**, **aucune explication**.
        - Si une jointure ou une vérification est nécessaire, fais-le.
        - Utilise l'univers_id ou l'id (si tu te trouves dans la table univers) suivant pour lier les données : {univers_id}

        Le script SQL doit **impérativement utiliser l'univers_id ou l'id de la table univers "{univers_id}"** afin de ne modifier que les données de l'univers concerné.

        Attention à modifier uniquement la bonne table !

        Exemple :
        Si la requête est "Ajoute moi la faction Le Clan de l'Eau avec une description", alors le SQL généré doit être :

        INSERT INTO faction (name, description, univers_id) VALUES ('Le Clan de l'Eau', 'Les elfes démoniaques du Clan de L'Eau sont connus pour leur agressivité et leur passion pour le thrash metal. Ils sont réputés pour leurs concerts de plus de 2 heures d'heureux vacarme.', 2);
        
        Second Exemple :
        Si la requête est "Je viens de passer dans la Forêt Trolonne et elle a brûlée", alors c'est du contexte à rajouter à la description de la location, le SQL généré doit être :

        UPDATE location SET description = 'un immense forestier où les trolls vivent dans leurs huttes de pierre et de bois. Elle a aujourd'hui brûlée' WHERE name = 'Forêt Trolonne' AND univers_id = 2;
        
        Troisième exemple :
        Si la requête est "Met à jour le nom de l'univers en "Magika"", alors le SQL généré doit être :

        UPDATE univers SET name = 'Magika' WHERE id = 3;
        """

        response: ChatResponse = chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}]
        )

        clean_response = response.message.content.strip()

        sql_syntax_valid = is_sql_syntax_valid(clean_response, get_db_path())
        sql_content_valid = check_sql_content(clean_response, request)

        
        univers_id_valid = "univers_id" in clean_response.lower() or "id" in clean_response.lower()

        print(clean_response)

        print(sql_syntax_valid, sql_content_valid, univers_id_valid)

        if sql_syntax_valid and sql_content_valid and univers_id_valid:
            is_syntax_valid = True

    return clean_response

def check_sql_content(script_sql, request):

    is_syntax_valid = False

    while not is_syntax_valid:
        prompt = f"""
    Tu es un validateur de syntaxe SQL. Si le script SQL est valide, correspond bien à la requête initiale de l'utilisateur **et ne contient que du SQL**, réponds **exclusivement** par "True" (sans guillemets). Sinon, réponds "False".
    Il est impératif que le script SQL correspond à la demande de l'utilisateur et qu'il ne modifie pas les données non concernées par la requête.
    Ne fournis **aucune explication**, **aucun autre mot**, **aucun caractère en plus**.

    Voici la requête initiale de l'utilisateur :
    {request}

    Voici le script SQL à vérifier :
    {script_sql}
    """
        response: ChatResponse = chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}])
        
        print(response.message.content.strip())
        
        if response.message.content.strip() in ["True", "False"]:
            is_syntax_valid = True

    return response.message.content.strip()

def is_sql_syntax_valid(sql, db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("BEGIN") 
        cursor.execute(sql)
        conn.rollback()
        return True
    except sqlite3.Error:
        return False
    finally:
        conn.close()

def pretty_sql(script_sql):
    prompt = f"""
Tu es un assistant non technique, ton rôle est d'aider un utilisateur à comprendre les changements apportés par une requête SQL. L'application est un outil de création et d'interaction avec un monde de jeu de rôle, du type Dungeons & Dragons.
Fais en sorte de parler comme un Dungeon Master de Dungeons & Dragons et immerse toi dans l'univers.
Donne des réponses courtes, pas besoin de rentrer dans les détails techniques du SQL.

Voici une requête SQL :
{script_sql}
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

