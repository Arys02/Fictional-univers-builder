import sqlite3
import os
from db_path import get_db_path

def update_db(instructions=None):
    # Obtenir le chemin direct à la racine du projet
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(current_dir)
    db_path = os.path.join(root_dir, "database.db")
    
    print(f"Connection DB à: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Exécuter l'instruction fournie
        cursor.execute(instructions)
        print(f"Instruction exécutée: {instructions}")

        conn.commit()
        conn.close()
        print(f"Modification réussie sur {db_path}")
        return True
    except Exception as e:
        print(f"Échec: {e}")
        return False

if __name__ == "__main__":
    # Renommer la colonne "COLUMN" en "created_at" dans chaque table
    tables = ['univers', 'faction', 'location', 'culture']
    
    for table in tables:
        print(f"\nRenommage de colonne dans la table: {table}")
        
        # SQLite ne supporte pas directement ALTER TABLE RENAME COLUMN avant la version 3.25
        # On doit utiliser une approche en plusieurs étapes avec une table temporaire
        
        # 1. Créer une table temporaire avec les colonnes renommées
        create_temp = f"""
        CREATE TABLE temp_{table} AS 
        SELECT 
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            name TEXT, 
            description TEXT, 
            FOREIGN KEY (univers_id) REFERENCES univers (id),
            created_at TIMESTAMP
        FROM {table}
        WHERE id IS NOT NULL
        """
        
        # Pour univers, la structure est différente (pas de univers_id)
        if table == 'univers':
            create_temp = f"""
            CREATE TABLE temp_{table} AS 
            SELECT 
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT, 
                description TEXT, 
                created_at TIMESTAMP
            FROM {table}
            WHERE id IS NOT NULL
            """
        
        # 2. Supprimer la table originale
        drop_original = f"DROP TABLE {table}"
        
        # 3. Renommer la table temporaire
        rename_temp = f"ALTER TABLE temp_{table} RENAME TO {table}"
        
        # Exécuter les 3 étapes
        update_db(create_temp)
        update_db(drop_original)
        update_db(rename_temp)
        
        print(f"Colonne renommée avec succès dans la table {table}")