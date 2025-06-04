import json
from ollama import chat, ChatResponse
import sqlite3


def insert_factions(factions, db_path="../database.db", univers_id=None):
    """
    Insère une liste de factions dans la base de données SQLite.

    :param factions: liste de dictionnaires au format :
        [
            {"name": "Nom de la faction", "description": "Texte..."},
            ...
        ]
    :param db_path: chemin vers le fichier .db
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for faction in factions:
        name = faction.get("name", "").strip()
        description = faction.get("description", "").strip()

        if name:  # On ignore les entrées sans nom
            cursor.execute(
                """
                INSERT INTO faction (name, description, univers_id)
                VALUES (?, ?, ?)
            """,
                (name, description, univers_id),
            )

    conn.commit()
    conn.close()


def insert_location(locations, db_path="../database.db", univers_id=None):
    """
    Insère une liste de factions dans la base de données SQLite.

    :param locations: liste de dictionnaires au format :
        [
            {"name": "Nom de la location", "description": "Texte..."},
            ...
        ]
    :param db_path: chemin vers le fichier .db
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for location in locations:
        name = location.get("name", "").strip()
        description = location.get("description", "").strip()

        if name:  # On ignore les entrées sans nom
            cursor.execute(
                """
                INSERT INTO location (name, description, univers_id)
                VALUES (?, ?, ?)
            """,
                (name, description, univers_id),
            )

    conn.commit()
    conn.close()


def insert_univers(univers, db_path="../database.db"):
    """
    Insère une liste de factions dans la base de données SQLite.

    :param univers: liste de dictionnaires au format :
        [
            {"name": "Nom de la faction", "description": "Texte..."},
            ...
        ]
    :param db_path: chemin vers le fichier .db
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    name = univers[0].get("name", "").strip()
    description = univers[0].get("description", "").strip()

    if name:  # On ignore les entrées sans nom
        cursor.execute(
            """
            INSERT INTO univers (name, description)
            VALUES (?, ?)
        """,
            (name, description),
        )
    else:
        cursor.execute(
            """
        INSERT INTO univers (name, description)
        VALUES (?, ?)
        """,
            ("?", description),
        )

    conn.commit()
    conn.close()


def insert_cultures(cultures, db_path="../database.db", univers_id=None):
    """
    Insère une liste de factions dans la base de données SQLite.

    :param cultures: liste de dictionnaires au format :
        [
            {"name": "Nom de la culture", "description": "Texte..."},
            ...
        ]
    :param db_path: chemin vers le fichier .db
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for culture in cultures:
        name = culture.get("name", "").strip()
        description = culture.get("description", "").strip()

        if name:  # On ignore les entrées sans nom
            cursor.execute(
                """
                INSERT INTO culture (name, description, univers_id)
                VALUES (?, ?, ?)
            """,
                (name, description, univers_id),
            )

    conn.commit()
    conn.close()


def get_univers_id(db_path="../database.db"):
    """
    Récupère l'ID du dernier univers inséré dans la base de données SQLite.

    :param db_path: chemin vers le fichier .db
    :return: ID du dernier univers inséré
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM univers ORDER BY id DESC LIMIT 1")
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]
    return None


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
            )
            retry_content = retry_response.message.content.strip()
            if is_valid_json(retry_content):
                return json.loads(retry_content)
