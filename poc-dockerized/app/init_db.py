import sqlite3
from db_path import get_db_path

def init_db():
    db_path = get_db_path()
    
    # Essayer deux chemins possibles (conteneur et direct)
    paths_to_try = [
        db_path,  # Chemin relatif
        f"/project_root/{db_path}",  # Chemin monté dans Docker
    ]
    
    for path in paths_to_try:
        print(f"Tentative d'initialisation de la DB à: {path}")
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            # Créer les tables
            cursor.execute('CREATE TABLE IF NOT EXISTS univers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT)')
            cursor.execute('CREATE TABLE IF NOT EXISTS faction (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, univers_id INTEGER)')
            cursor.execute('CREATE TABLE IF NOT EXISTS location (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, univers_id INTEGER)')
            cursor.execute('CREATE TABLE IF NOT EXISTS culture (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, univers_id INTEGER)')
            
            conn.commit()
            conn.close()
            print(f"Base de données initialisée avec succès à: {path}")
            return True
        except Exception as e:
            print(f"Échec de l'initialisation à {path}: {e}")
    
    return False

if __name__ == "__main__":
    init_db()