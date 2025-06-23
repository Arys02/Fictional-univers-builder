import json
from ollama import ChatResponse, Client
import sqlite3
import os 
from datetime import datetime
from db_path import get_db_path

# Configuration du client Ollama avec l'hôte du conteneur Docker
OLLAMA_HOST = os.environ.get('OLLAMA_HOST', 'http://localhost:11434')
ollama_client = Client(host=OLLAMA_HOST)
DB_PATH = os.environ.get('DB_PATH', 'database.db')

# Redéfinition de la fonction chat pour utiliser notre client configuré
def chat(*args, **kwargs):
    return ollama_client.chat(*args, **kwargs)


def insert_univers(univers, conn=None):
    """
    Insère une liste de factions dans la base de données SQLite.

    :param univers: liste de dictionnaires au format :
        [
            {"name": "Nom de l'univers", "description": "Texte..."},
            ...
        ]
    :param db_path: chemin vers le fichier .db
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(get_db_path())
        close_conn = True

    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO univers (name, description, created_at) VALUES (?, ?, datetime('now'))",
            (univers.get("name", ""), univers.get("description", ""))
        )
        
        if close_conn:
            conn.commit()
    finally:
        if close_conn:
            conn.close()

def insert_factions(factions, univers_id=None, conn=None):
    """
    Insère une liste de factions dans la base de données SQLite.

    :param factions: liste de dictionnaires au format :
        [
            {"name": "Nom de la faction", "description": "Texte..."},
            ...
        ]
    :param univers_id: ID de l'univers auquel ces factions appartiennent
    :param conn: connexion SQLite existante (optionnel)
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(get_db_path())
        close_conn = True
    
    try:
        cursor = conn.cursor()

        for faction in factions:
            name = faction.get("name", "").strip()
            description = faction.get("description", "").strip()

            if name:  # On ignore les entrées sans nom
                cursor.execute(
                    """
                    INSERT INTO faction (name, description, univers_id, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                    """,
                    (name, description, univers_id),
                )
        
        if close_conn:
            conn.commit()
    finally:
        if close_conn:
            conn.close()


def insert_location(locations, univers_id=None, conn=None):
    """
    Insère une liste de lieux dans la base de données SQLite.

    :param locations: liste de dictionnaires au format :
        [
            {"name": "Nom du lieu", "description": "Texte..."},
            ...
        ]
    :param univers_id: ID de l'univers auquel ces lieux appartiennent
    :param conn: connexion SQLite existante (optionnel)
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(get_db_path())
        close_conn = True
    
    try:
        cursor = conn.cursor()

        for location in locations:
            name = location.get("name", "").strip()
            description = location.get("description", "").strip()

            if name:  # On ignore les entrées sans nom
                cursor.execute(
                    """
                    INSERT INTO location (name, description, univers_id, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                    """,
                    (name, description, univers_id),
                )
        
        if close_conn:
            conn.commit()
    finally:
        if close_conn:
            conn.close()


def insert_cultures(cultures, univers_id=None, conn=None):
    """
    Insère une liste de cultures dans la base de données SQLite.

    :param cultures: liste de dictionnaires au format :
        [
            {"name": "Nom de la culture", "description": "Texte..."},
            ...
        ]
    :param univers_id: ID de l'univers auquel ces cultures appartiennent
    :param conn: connexion SQLite existante (optionnel)
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(get_db_path())
        close_conn = True
    
    try:
        cursor = conn.cursor()

        for culture in cultures:
            name = culture.get("name", "").strip()
            description = culture.get("description", "").strip()

            if name:  # On ignore les entrées sans nom
                cursor.execute(
                    """
                    INSERT INTO culture (name, description, univers_id, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                    """,
                    (name, description, univers_id),
                )
        
        if close_conn:
            conn.commit()
    finally:
        if close_conn:
            conn.close()


def get_univers_id(conn=None):
    """
    Récupère l'ID du dernier univers inséré dans la base de données SQLite.

    :param conn: connexion SQLite existante (optionnel)
    :return: ID du dernier univers inséré
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(get_db_path())
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM univers ORDER BY id DESC LIMIT 1")
        result = cursor.fetchone()
        
        if result:
            return result[0]
        return None
    finally:
        if close_conn:
            conn.close()


def is_valid_json(text):
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return True
        return False
    except json.JSONDecodeError:
        return False


def ask_faction_extraction(response_content):
    system_prompt = """Tu es un expert en extraction de données structurées à partir de réponses de modèles de langage.
        Tu dois extraire les factions d'un univers fictif. 
        Tu dois fournir le nom des factions, et pour chacune une brève description, à partir des informations fournies dans le texte.
        Le format de sortie doit être strictement un tableau JSON :
        [
          {
            "name": "Nom de la faction",
            "description": "Description"
          }
        ]
        Si tu n’en trouves pas, retourne simplement []. Pas d'explication, pas de texte, seulement du JSON."""

    user_prompt = f"Extrait les factions de la réponse suivante :\n\n{response_content}"

    response: ChatResponse = chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
        "num_thread": 8,       # Plus de threads
        "num_gpu": 1,          # Utiliser le GPU si disponible
        "num_batch": 512,      # Augmenter taille du batch
        "temperature": 0.7,    # Réduire pour des réponses plus rapides
        "top_p": 0.9           # Réduire pour des réponses plus rapides
        }
    )

    content = response.message.content.strip()

    # Validation du JSON
    if is_valid_json(content):
        return json.loads(content)
    else:
        counter = 0
        while not is_valid_json(content) or counter < 20:
            counter += 1
            # Relance une deuxième fois avec un prompt explicite
            retry_prompt = f"""
                Tu n'as pas respecté le format JSON strict. Voici un rappel :
                [
                  {{
                    "name": "Nom de la faction",
                    "description": "Description"
                  }}
                ]
                Pas de texte, pas de commentaire. Corrige la réponse suivante :
                
                {content}
                """

            retry_response: ChatResponse = chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu corriges des réponses LLM pour les rendre au bon format JSON.",
                    },
                    {"role": "user", "content": retry_prompt},
                ],
                options={
                    "num_thread": 8,       # Plus de threads
                    "num_gpu": 1,          # Utiliser le GPU si disponible
                    "num_batch": 512,      # Augmenter taille du batch
                    "temperature": 0.7,    # Réduire pour des réponses plus rapides
                    "top_p": 0.9           # Réduire pour des réponses plus rapides
                }
            )
            retry_content = retry_response.message.content.strip()
            if is_valid_json(retry_content):
                return json.loads(retry_content)


def ask_location_extraction(response_content):
    system_prompt = """
        Tu es un expert en extraction de lieux géographiques à partir de textes de fiction. 
        Ton objectif est d'extraire UNIQUEMENT les lieux physiques ou géographiques (régions, villes, forêts, montagnes, déserts, marais, péninsules, etc.).
        Tu dois fournir la nom du lieu, et une brève description de celui-ci, à partir des informations fournies dans le texte.
        Ignore les personnages, dieux, factions, ou autres entités non géographiques.
    
        Le format de sortie doit être STRICTEMENT un tableau JSON :
    
        [
          {
            "name": "Nom du lieu",
            "description": "Brève description du lieu"
          }
        ]
    
        Si aucun lieu n’est trouvé, retourne simplement []. Aucune explication. Seulement du JSON.
        """

    user_prompt = f"Extrait les lieux géographiques de la réponse suivante :\n\n{response_content}"

    response: ChatResponse = chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "num_thread": 8,       # Plus de threads
            "num_gpu": 1,          # Utiliser le GPU si disponible
            "num_batch": 512,      # Augmenter taille du batch
            "temperature": 0.7,    # Réduire pour des réponses plus rapides
            "top_p": 0.9           # Réduire pour des réponses plus rapides
        }
    )

    content = response.message.content.strip()
    # print("Réponse brute de l'LLM pour les lieux :", content)
    # Validation du JSON
    if is_valid_json(content):
        return json.loads(content)
    else:
        counter = 0
        while not is_valid_json(content) or counter < 10:
            counter += 1
            # Relance une deuxième fois avec un prompt explicite
            retry_prompt = f"""
                Tu n'as pas respecté le format JSON strict. Voici un rappel :
                [
                  {{
                    "name": "Nom de l'endroit",
                    "description": "Description"
                  }}
                ]
                Pas de texte, pas de commentaire. Corrige la réponse suivante :

                {content}
                """

            retry_response: ChatResponse = chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu corriges des réponses LLM pour les rendre au bon format JSON.",
                    },
                    {"role": "user", "content": retry_prompt},
                ],
                options={
                    "num_thread": 8,       # Plus de threads
                    "num_gpu": 1,          # Utiliser le GPU si disponible
                    "num_batch": 512,      # Augmenter taille du batch
                    "temperature": 0.7,    # Réduire pour des réponses plus rapides
                    "top_p": 0.9           # Réduire pour des réponses plus rapides
                }
            )
            retry_content = retry_response.message.content.strip()
            if is_valid_json(retry_content):
                return json.loads(retry_content)


def ask_univers_extraction(response_content):
    system_prompt = """Tu es un expert en extraction de données structurées à partir de réponses de modèles de langage.
        Tu dois extraire le nom de l'univers dont il est question dans le texte. 
        Récoltes des informations globales sur cet univers et fait un résumé court et synthétique le concernant.
        Ici dans notre contexte, on cherche le nom global de l'univers, il ne doit y avoir qu'un seul nom, pas de sous-univers ou de mondes.
        Le format de sortie doit être strictement un tableau JSON :
        [
          {
            "name": "Nom de l'univers",
            "description": "court résumé de l'univers"
          }
        ]
        Si tu n’en trouves pas, retourne simplement []. Pas d'explication, pas de texte, seulement du JSON."""

    user_prompt = f"Extrait les factions de la réponse suivante :\n\n{response_content}"

    response: ChatResponse = chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "num_thread": 8,       # Plus de threads
            "num_gpu": 1,          # Utiliser le GPU si disponible
            "num_batch": 512,      # Augmenter taille du batch
            "temperature": 0.7,    # Réduire pour des réponses plus rapides
            "top_p": 0.9           # Réduire pour des réponses plus rapides
        }
    )

    content = response.message.content.strip()
    # print("Réponse brute de l'LLM pour l'univers :", content)
    # Validation du JSON
    if is_valid_json(content):
        return json.loads(content)
    else:
        counter = 0
        while not is_valid_json(content) or counter < 100:
            counter += 1
            # Relance une deuxième fois avec un prompt explicite
            retry_prompt = f"""
                Tu n'as pas respecté le format JSON strict. Voici un rappel :
                [
                  {{
                    "name": "Nom de l'univers",
                    "description": "court résumé de l'univers"
                  }}
                ]
                Pas de texte, pas de commentaire. Corrige la réponse suivante :

                {content}
                """

            retry_response: ChatResponse = chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu corriges des réponses LLM pour les rendre au bon format JSON.",
                    },
                    {"role": "user", "content": retry_prompt},
                ],
                options={
                    "num_thread": 8,       # Plus de threads
                    "num_gpu": 1,          # Utiliser le GPU si disponible
                    "num_batch": 512,      # Augmenter taille du batch
                    "temperature": 0.7,    # Réduire pour des réponses plus rapides
                    "top_p": 0.9           # Réduire pour des réponses plus rapides
                }
            )
            retry_content = retry_response.message.content.strip()
            if is_valid_json(retry_content):
                return json.loads(retry_content)


def ask_culture_extraction(response_content):
    system_prompt = """Tu es un expert en extraction de données structurées à partir de réponses de modèles de langage.
        Tu dois extraire les cultures d'un univers fictif. 
        Des exemples de cultures seraient les religions, les philosophies, les modes de vie, les traditions, etc.
        Par exemple la culture Orc, la culture Elfique, la culture des Nains, etc.
        Attention, les cultures que tu trouves doivent correspondrent à celles présentes dans l'univers donné en input et de manière explicite, n'invente pas de cultures.
        Le format de sortie doit être strictement un tableau JSON :
        [
          {
            "name": "Nom de la culture",
            "description": "Description"
          }
        ]
        Si tu n’en trouves pas, retourne simplement []. Pas d'explication, pas de texte, seulement du JSON."""

    user_prompt = f"Extrait les cultures de la réponse suivante :\n\n{response_content}"

    response: ChatResponse = chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "num_thread": 8,       # Plus de threads
            "num_gpu": 1,          # Utiliser le GPU si disponible
            "num_batch": 512,      # Augmenter taille du batch
            "temperature": 0.7,    # Réduire pour des réponses plus rapides
            "top_p": 0.9           # Réduire pour des réponses plus rapides
        }
    )

    content = response.message.content.strip()

    # Validation du JSON
    if is_valid_json(content):
        return json.loads(content)
    else:
        counter = 0
        while not is_valid_json(content) or counter < 100:
            counter += 1
            # Relance une deuxième fois avec un prompt explicite
            retry_prompt = f"""
                Tu n'as pas respecté le format JSON strict. Voici un rappel :
                [
                  {{
                    "name": "Nom de la culture",
                    "description": "Description"
                  }}
                ]
                Pas de texte, pas de commentaire. Corrige la réponse suivante :

                {content}
                """

            retry_response: ChatResponse = chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu corriges des réponses LLM pour les rendre au bon format JSON.",
                    },
                    {"role": "user", "content": retry_prompt},
                ],
                options={
                    "num_thread": 8,       # Plus de threads
                    "num_gpu": 1,          # Utiliser le GPU si disponible
                    "num_batch": 512,      # Augmenter taille du batch
                    "temperature": 0.7,    # Réduire pour des réponses plus rapides
                    "top_p": 0.9           # Réduire pour des réponses plus rapides
                }
            )
            retry_content = retry_response.message.content.strip()
            if is_valid_json(retry_content):
                return json.loads(retry_content)

def insert_prompt_answer(prompt, response, univers_id=None, conn=None):
    """
    Insère un prompt et sa réponse dans la base de données.
    
    :param prompt: Le prompt envoyé à l'LLM
    :param response: La réponse complète de l'LLM
    :param univers_id: ID de l'univers associé (peut être None)
    :param conn: connexion SQLite existante (optionnel)
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(get_db_path())
        close_conn = True
    
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO prompt_answers (prompt, response, univers_id, created_at)
            VALUES (?, ?, ?, datetime('now'))
            """,
            (prompt, response, univers_id)
        )
        
        if close_conn:
            conn.commit()
    finally:
        if close_conn:
            conn.close()


def ask_objets_extraction(response_content):
    system_prompt = """Tu es un expert en extraction de données structurées à partir de réponses de modèles de langage.
        Tu dois extraire les objets importants d'un univers fictif. 
        Des exemples d'objets seraient par exemple des armes, des artefacts, des objets magiques, des reliques, etc.
        Attention, les objets que tu trouves doivent correspondrent à ceux présentes dans l'univers donné en input et de manière explicite, n'invente pas d'objets.
        Le format de sortie doit être strictement un tableau JSON :
        [
          {
            "name": "Nom de l'objet",
            "description": "Description"
          }
        ]
        Si tu n’en trouves pas, retourne simplement []. Pas d'explication, pas de texte, seulement du JSON."""

    user_prompt = f"Extrait les objets de la réponse suivante :\n\n{response_content}"

    response: ChatResponse = chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "num_thread": 8,       # Plus de threads
            "num_gpu": 1,          # Utiliser le GPU si disponible
            "num_batch": 512,      # Augmenter taille du batch
            "temperature": 0.7,    # Réduire pour des réponses plus rapides
            "top_p": 0.9           # Réduire pour des réponses plus rapides
        }
    )

    content = response.message.content.strip()

    # Validation du JSON
    if is_valid_json(content):
        return json.loads(content)
    else:
        counter = 0
        while not is_valid_json(content) or counter < 100:
            counter += 1
            # Relance une deuxième fois avec un prompt explicite
            retry_prompt = f"""
                Tu n'as pas respecté le format JSON strict. Voici un rappel :
                [
                  {{
                    "name": "Nom de l'objet",
                    "description": "Description"
                  }}
                ]
                Pas de texte, pas de commentaire. Corrige la réponse suivante :

                {content}
                """

            retry_response: ChatResponse = chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu corriges des réponses LLM pour les rendre au bon format JSON.",
                    },
                    {"role": "user", "content": retry_prompt},
                ],
                options={
                    "num_thread": 8,       # Plus de threads
                    "num_gpu": 1,          # Utiliser le GPU si disponible
                    "num_batch": 512,      # Augmenter taille du batch
                    "temperature": 0.7,    # Réduire pour des réponses plus rapides
                    "top_p": 0.9           # Réduire pour des réponses plus rapides
                }
            )
            retry_content = retry_response.message.content.strip()
            if is_valid_json(retry_content):
                return json.loads(retry_content)
            

def insert_objets(objets, univers_id=None, conn=None):
    """
    Insère une liste d'objets' dans la base de données SQLite.

    :param cultures: liste de dictionnaires au format :
        [
            {"name": "Nom de l'objet", "description": "Texte..."},
            ...
        ]
    :param univers_id: ID de l'univers auquel ces cultures appartiennent
    :param conn: connexion SQLite existante (optionnel)
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(get_db_path())
        close_conn = True
    
    try:
        cursor = conn.cursor()

        for object in objets:
            name = object.get("name", "").strip()
            description = object.get("description", "").strip()

            if name:  # On ignore les entrées sans nom
                cursor.execute(
                    """
                    INSERT INTO objets (name, description, univers_id, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                    """,
                    (name, description, univers_id),
                )
        
        if close_conn:
            conn.commit()
    finally:
        if close_conn:
            conn.close()


def ask_personnages_extraction(response_content):
    system_prompt = """Tu es un expert en extraction de données structurées à partir de réponses de modèles de langage.
        Tu dois extraire les personnages importants d'un univers fictif. 
        Des exemples de personnages seraient par exemple des héros, des méchants, des figures historiques, etc.
        Attention, les personnages que tu trouves doivent correspondrent à ceux présents dans l'univers donné en input et de manière explicite, n'invente pas de personnages.
        Le format de sortie doit être strictement un tableau JSON :
        [
          {
            "name": "Nom du personnage",
            "description": "Description"
          }
        ]
        Si tu n’en trouves pas, retourne simplement []. Pas d'explication, pas de texte, seulement du JSON."""

    user_prompt = f"Extrait les objets de la réponse suivante :\n\n{response_content}"

    response: ChatResponse = chat(
        model="llama3.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        options={
            "num_thread": 8,       # Plus de threads
            "num_gpu": 1,          # Utiliser le GPU si disponible
            "num_batch": 512,      # Augmenter taille du batch
            "temperature": 0.7,    # Réduire pour des réponses plus rapides
            "top_p": 0.9           # Réduire pour des réponses plus rapides
        }
    )

    content = response.message.content.strip()

    # Validation du JSON
    if is_valid_json(content):
        return json.loads(content)
    else:
        counter = 0
        while not is_valid_json(content) or counter < 100:
            counter += 1
            # Relance une deuxième fois avec un prompt explicite
            retry_prompt = f"""
                Tu n'as pas respecté le format JSON strict. Voici un rappel :
                [
                  {{
                    "name": "Nom du personnages",
                    "description": "Description"
                  }}
                ]
                Pas de texte, pas de commentaire. Corrige la réponse suivante :

                {content}
                """

            retry_response: ChatResponse = chat(
                model="llama3.2",
                messages=[
                    {
                        "role": "system",
                        "content": "Tu corriges des réponses LLM pour les rendre au bon format JSON.",
                    },
                    {"role": "user", "content": retry_prompt},
                ],
                options={
                    "num_thread": 8,       # Plus de threads
                    "num_gpu": 1,          # Utiliser le GPU si disponible
                    "num_batch": 512,      # Augmenter taille du batch
                    "temperature": 0.7,    # Réduire pour des réponses plus rapides
                    "top_p": 0.9           # Réduire pour des réponses plus rapides
                }
            )
            retry_content = retry_response.message.content.strip()
            if is_valid_json(retry_content):
                return json.loads(retry_content)
            

def insert_personnages(personnages, univers_id=None, conn=None):
    """
    Insère une liste de personnages dans la base de données SQLite.

    :param cultures: liste de dictionnaires au format :
        [
            {"name": "Nom du personnage", "description": "Texte..."},
            ...
        ]
    :param univers_id: ID de l'univers auquel ces personnages appartiennent
    :param conn: connexion SQLite existante (optionnel)
    """
    close_conn = False
    if conn is None:
        conn = sqlite3.connect(get_db_path())
        close_conn = True
    
    try:
        cursor = conn.cursor()

        for personnage in personnages:
            name = personnage.get("name", "").strip()
            description = personnage.get("description", "").strip()

            if name:  # On ignore les entrées sans nom
                cursor.execute(
                    """
                    INSERT INTO personnages (name, description, univers_id, created_at)
                    VALUES (?, ?, ?, datetime('now'))
                    """,
                    (name, description, univers_id),
                )
        
        if close_conn:
            conn.commit()
    finally:
        if close_conn:
            conn.close()