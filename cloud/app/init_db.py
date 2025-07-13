import sqlite3
from db_path import get_db_path

def init_db():
    db_path = get_db_path()
    
    # deux chemins possibles (conteneur et direct)
    paths_to_try = [
        db_path,  # Chemin relatif
        f"/project_root/{db_path}",  # Chemin monté dans Docker
    ]
    
    for path in paths_to_try:
        try:
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            cursor.execute('CREATE TABLE IF NOT EXISTS univers (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, created_at TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS faction (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, univers_id INTEGER, created_at TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS location (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, univers_id INTEGER, created_at TIMESTAMP)')
            cursor.execute('CREATE TABLE IF NOT EXISTS culture (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, description TEXT, univers_id INTEGER, created_at TIMESTAMP)')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS prompt_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    prompt TEXT NOT NULL,
                    response TEXT NOT NULL,
                    univers_id INTEGER,
                    created_at TIMESTAMP,
                    FOREIGN KEY (univers_id) REFERENCES univers (id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS objets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    univers_id INTEGER,
                    created_at TIMESTAMP,
                    FOREIGN KEY (univers_id) REFERENCES univers (id)
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS personnages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    univers_id INTEGER,
                    created_at TIMESTAMP,
                    FOREIGN KEY (univers_id) REFERENCES univers (id)
                )
            ''')

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Échec de l'initialisation à {path}: {e}")
    
    return False

if __name__ == "__main__":
    init_db()