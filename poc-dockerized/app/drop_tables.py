import sqlite3
import os

def drop_tables(table_names, db_path):
    """
    Supprime les tables spécifiées de la base de données.
    
    :param table_names: Liste des noms de tables à supprimer
    :param db_path: Chemin vers le fichier de base de données
    """
    print(f"Tentative de connexion à la base de données : {db_path}")
    print(f"Le fichier existe : {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        print(f"Erreur: La base de données n'existe pas à l'emplacement {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Afficher les tables existantes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        print(f"Tables existantes : {existing_tables}")
        
        for table_name in table_names:
            if table_name in existing_tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                print(f"Table '{table_name}' supprimée avec succès.")
            else:
                print(f"Table '{table_name}' n'existe pas dans la base de données.")
        
        conn.commit()
        conn.close()
        print("Opération terminée.")
    except sqlite3.Error as e:
        print(f"Erreur de connexion à la base de données : {e}")

if __name__ == "__main__":
    # Chemin vers la racine de poc-dockerized
    current_dir = os.path.dirname(os.path.abspath(__file__))  # app directory
    root_dir = os.path.dirname(current_dir)  # poc-dockerized directory
    db_path = os.path.join(root_dir, "database.db")
    
    print(f"Utilisation de la base de données à : {db_path}")
    
    # Spécifiez ici les tables que vous souhaitez supprimer
    tables_to_drop = []
    
    if not tables_to_drop:
        print("ATTENTION: Aucune table n'est spécifiée pour la suppression.")
        tables = input("Entrez les noms des tables à supprimer (séparés par des virgules) ou 'ALL' pour toutes : ")
        
        if tables.strip().upper() == 'ALL':
            # Obtenir toutes les tables de la base de données
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                tables_to_drop = [table[0] for table in cursor.fetchall()]
                conn.close()
            else:
                print(f"La base de données n'existe pas à l'emplacement {db_path}")
                exit(1)
        else:
            tables_to_drop = [t.strip() for t in tables.split(',')]
    
    if tables_to_drop:
        confirm = input(f"Êtes-vous sûr de vouloir supprimer ces tables ? {tables_to_drop} (y/n): ")
        if confirm.lower() == 'y':
            drop_tables(tables_to_drop, db_path)
        else:
            print("Opération annulée.")
    else:
        print("Aucune table à supprimer.")