import os

def get_db_path():
    """
    Retourne le chemin absolu vers la base de données, 
    cohérent entre toutes les parties de l'application
    """
    db_name = os.environ.get('DB_PATH', 'database.db')
    
    # Dans Docker, utiliser le chemin monté pour accéder à la racine du projet
    project_root = "/project_root"
    db_path = os.path.join(project_root, db_name)
    
    print(f"Using database at: {db_path}")

    # return 'poc-dockerized/database.db'
    return db_path