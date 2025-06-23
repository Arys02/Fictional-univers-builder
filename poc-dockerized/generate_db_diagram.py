#!/usr/bin/env python3
"""
Script pour générer automatiquement un diagramme de la base de données
au format Mermaid à partir du schéma SQLite.
"""

import sqlite3
import os
from db_path import get_db_path

def get_table_schema(db_path):
    """Récupère le schéma de toutes les tables de la base de données."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Récupérer toutes les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [table[0] for table in cursor.fetchall()]
    
    schema = {}
    for table in tables:
        # Récupérer les colonnes de chaque table
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        schema[table] = []
        for col in columns:
            col_id, name, type_name, not_null, default_value, pk = col
            schema[table].append({
                'name': name,
                'type': type_name,
                'notnull': bool(not_null),
                'default': default_value,
                'primary_key': bool(pk)
            })
    
    conn.close()
    return schema

def generate_mermaid_er_diagram(schema):
    """Génère un diagramme ER au format Mermaid."""
    mermaid = "```mermaid\nerDiagram\n"
    
    # Définir les tables
    for table_name, columns in schema.items():
        mermaid += f"    {table_name} {{\n"
        for col in columns:
            pk_suffix = " PK" if col['primary_key'] else ""
            fk_suffix = " FK" if col['name'].endswith('_id') and not col['primary_key'] else ""
            not_null_suffix = " NOT NULL" if col['notnull'] else ""
            mermaid += f"        {col['type']} {col['name']}{pk_suffix}{fk_suffix}{not_null_suffix}\n"
        mermaid += "    }\n\n"
    
    # Définir les relations (basées sur les clés étrangères)
    relations = []
    for table_name, columns in schema.items():
        for col in columns:
            if col['name'].endswith('_id') and not col['primary_key']:
                # Extraire le nom de la table référencée
                referenced_table = col['name'].replace('_id', '')
                if referenced_table in schema:
                    relations.append(f"    {referenced_table} ||--o{{ {table_name} : \"contient\"")
    
    # Ajouter les relations uniques
    unique_relations = list(set(relations))
    for relation in unique_relations:
        mermaid += relation + "\n"
    
    mermaid += "```"
    return mermaid

def generate_mermaid_flow_diagram(schema):
    """Génère un diagramme de flux au format Mermaid."""
    mermaid = "```mermaid\ngraph TD\n"
    
    # Créer les nœuds pour chaque table
    for table_name in schema.keys():
        mermaid += f"    A_{table_name}[{table_name}]\n"
    
    # Créer les relations
    for table_name, columns in schema.items():
        for col in columns:
            if col['name'].endswith('_id') and not col['primary_key']:
                referenced_table = col['name'].replace('_id', '')
                if referenced_table in schema:
                    mermaid += f"    A_{referenced_table} --> A_{table_name}\n"
    
    mermaid += "```"
    return mermaid

def generate_table_documentation(schema):
    """Génère la documentation des tables au format Markdown."""
    doc = "## Documentation des Tables\n\n"
    
    for table_name, columns in schema.items():
        doc += f"### Table `{table_name}`\n\n"
        
        # Tableau des colonnes
        doc += "| Champ | Type | Contrainte | Description |\n"
        doc += "|-------|------|------------|-------------|\n"
        
        for col in columns:
            constraints = []
            if col['primary_key']:
                constraints.append("PRIMARY KEY")
            if col['notnull']:
                constraints.append("NOT NULL")
            if col['name'].endswith('_id') and not col['primary_key']:
                constraints.append("FOREIGN KEY")
            
            constraint_str = ", ".join(constraints) if constraints else "-"
            description = get_column_description(col['name'], table_name)
            
            doc += f"| `{col['name']}` | {col['type']} | {constraint_str} | {description} |\n"
        
        doc += "\n"
    
    return doc

def get_column_description(column_name, table_name):
    """Retourne une description pour une colonne donnée."""
    descriptions = {
        'id': 'Identifiant unique',
        'name': 'Nom de l\'élément',
        'description': 'Description détaillée',
        'created_at': 'Date et heure de création',
        'univers_id': 'Référence vers l\'univers parent',
        'prompt': 'Le prompt original de l\'utilisateur',
        'response': 'La réponse générée par l\'IA'
    }
    
    return descriptions.get(column_name, 'Champ de données')

def generate_schema_json(schema):
    """Génère le schéma au format JSON pour référence."""
    import json
    return json.dumps(schema, indent=2, ensure_ascii=False)

def main():
    """Fonction principale."""
    db_path = get_db_path()
    
    print(f"Génération du diagramme pour la base de données: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Erreur: La base de données n'existe pas à {db_path}")
        return
    
    # Récupérer le schéma
    schema = get_table_schema(db_path)
    
    # Générer les diagrammes
    er_diagram = generate_mermaid_er_diagram(schema)
    flow_diagram = generate_mermaid_flow_diagram(schema)
    table_doc = generate_table_documentation(schema)
    schema_json = generate_schema_json(schema)
    
    # Créer le fichier de sortie
    output_file = "database_diagram.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Diagramme de la Base de Données\n\n")
        f.write("## Schéma JSON de la Base de Données\n\n")
        f.write("```json\n")
        f.write(schema_json)
        f.write("\n```\n\n")
        f.write("## Diagramme Entité-Relation\n\n")
        f.write(er_diagram)
        f.write("\n\n")
        f.write("## Diagramme de Flux\n\n")
        f.write(flow_diagram)
        f.write("\n\n")
        f.write(table_doc)
    
    print(f"Diagramme généré dans: {output_file}")
    
    # Afficher le schéma JSON dans la console
    print("\n" + "="*50)
    print("SCHÉMA JSON DE LA BASE DE DONNÉES")
    print("="*50)
    print(schema_json)
    
    # Afficher le diagramme ER dans la console
    print("\n" + "="*50)
    print("DIAGRAMME ENTITÉ-RELATION")
    print("="*50)
    print(er_diagram)

if __name__ == "__main__":
    main() 