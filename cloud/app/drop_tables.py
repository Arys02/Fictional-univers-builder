import sqlite3
import os

def drop_tables(table_names, db_path):
    if not os.path.exists(db_path):
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        print(f"Tables existantes : {existing_tables}")
        
        for table_name in table_names:
            if table_name in existing_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            else:
                print(f"Table '{table_name}' n'existe pas dans la base de données.")
        
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"Erreur de connexion à la base de données : {e}")