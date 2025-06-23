#!/usr/bin/env python3
"""
Script pour afficher les statistiques de la base de données
et générer des rapports sur les données stockées.
"""

import sqlite3
import os
from datetime import datetime
from db_path import get_db_path

def get_db_stats(db_path):
    """Récupère les statistiques générales de la base de données."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {}
    
    # Récupérer toutes les tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [table[0] for table in cursor.fetchall()]
    
    stats['tables'] = {}
    total_records = 0
    
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        stats['tables'][table] = count
        total_records += count
    
    stats['total_records'] = total_records
    stats['total_tables'] = len(tables)
    
    # Taille du fichier de base de données
    if os.path.exists(db_path):
        stats['file_size_mb'] = round(os.path.getsize(db_path) / (1024 * 1024), 2)
    else:
        stats['file_size_mb'] = 0
    
    conn.close()
    return stats

def get_universe_details(db_path):
    """Récupère les détails de chaque univers avec le nombre d'éléments."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Requête pour obtenir les détails de chaque univers
    query = """
    SELECT 
        u.id,
        u.name,
        u.description,
        u.created_at,
        COUNT(DISTINCT f.id) as faction_count,
        COUNT(DISTINCT l.id) as location_count,
        COUNT(DISTINCT c.id) as culture_count,
        COUNT(DISTINCT p.id) as character_count,
        COUNT(DISTINCT o.id) as object_count
    FROM univers u
    LEFT JOIN faction f ON u.id = f.univers_id
    LEFT JOIN location l ON u.id = l.univers_id
    LEFT JOIN culture c ON u.id = c.univers_id
    LEFT JOIN personnages p ON u.id = p.univers_id
    LEFT JOIN objets o ON u.id = o.univers_id
    GROUP BY u.id, u.name, u.description, u.created_at
    ORDER BY u.created_at DESC
    """
    
    cursor.execute(query)
    universes = cursor.fetchall()
    
    conn.close()
    return universes

def get_recent_activity(db_path, limit=10):
    """Récupère les activités récentes dans la base de données."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    activities = []
    
    # Récupérer les interactions récentes
    cursor.execute("""
        SELECT 'prompt_answers' as table_name, created_at, 
               SUBSTR(prompt, 1, 50) || '...' as content
        FROM prompt_answers 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (limit,))
    
    activities.extend(cursor.fetchall())
    
    # Récupérer les univers récents
    cursor.execute("""
        SELECT 'univers' as table_name, created_at, 
               SUBSTR(name, 1, 50) as content
        FROM univers 
        ORDER BY created_at DESC 
        LIMIT ?
    """, (limit,))
    
    activities.extend(cursor.fetchall())
    
    # Trier par date de création
    activities.sort(key=lambda x: x[1], reverse=True)
    
    conn.close()
    return activities[:limit]

def generate_markdown_report(stats, universes, activities):
    """Génère un rapport au format Markdown."""
    report = "# Rapport de la Base de Données\n\n"
    report += f"*Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}*\n\n"
    
    # Statistiques générales
    report += "## 📊 Statistiques Générales\n\n"
    report += f"- **Taille du fichier:** {stats['file_size_mb']} MB\n"
    report += f"- **Nombre total d'enregistrements:** {stats['total_records']}\n"
    report += f"- **Nombre de tables:** {stats['total_tables']}\n\n"
    
    # Statistiques par table
    report += "### Répartition par Table\n\n"
    report += "| Table | Nombre d'enregistrements |\n"
    report += "|-------|-------------------------|\n"
    
    for table, count in stats['tables'].items():
        report += f"| `{table}` | {count} |\n"
    
    report += "\n"
    
    # Détails des univers
    if universes:
        report += "## 🌌 Univers Créés\n\n"
        report += "| ID | Nom | Créé le | Factions | Lieux | Cultures | Personnages | Objets |\n"
        report += "|----|-----|---------|----------|-------|----------|-------------|--------|\n"
        
        for universe in universes:
            id, name, desc, created_at, f_count, l_count, c_count, p_count, o_count = universe
            created_date = datetime.fromisoformat(created_at).strftime('%d/%m/%Y') if created_at else 'N/A'
            report += f"| {id} | {name} | {created_date} | {f_count} | {l_count} | {c_count} | {p_count} | {o_count} |\n"
        
        report += "\n"
    
    # Activités récentes
    if activities:
        report += "## 📝 Activités Récentes\n\n"
        report += "| Table | Date | Contenu |\n"
        report += "|-------|------|---------|\n"
        
        for activity in activities:
            table_name, created_at, content = activity
            created_date = datetime.fromisoformat(created_at).strftime('%d/%m/%Y %H:%M') if created_at else 'N/A'
            report += f"| `{table_name}` | {created_date} | {content} |\n"
    
    return report

def print_stats_to_console(stats, universes, activities):
    """Affiche les statistiques dans la console."""
    print("="*60)
    print("📊 RAPPORT DE LA BASE DE DONNÉES")
    print("="*60)
    print(f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}")
    print()
    
    # Statistiques générales
    print("📈 STATISTIQUES GÉNÉRALES")
    print("-" * 30)
    print(f"Taille du fichier: {stats['file_size_mb']} MB")
    print(f"Nombre total d'enregistrements: {stats['total_records']}")
    print(f"Nombre de tables: {stats['total_tables']}")
    print()
    
    # Statistiques par table
    print("📋 RÉPARTITION PAR TABLE")
    print("-" * 30)
    for table, count in stats['tables'].items():
        print(f"{table:15} : {count:3d} enregistrements")
    print()
    
    # Univers créés
    if universes:
        print("🌌 UNIVERS CRÉÉS")
        print("-" * 30)
        for universe in universes:
            id, name, desc, created_at, f_count, l_count, c_count, p_count, o_count = universe
            created_date = datetime.fromisoformat(created_at).strftime('%d/%m/%Y') if created_at else 'N/A'
            print(f"ID {id}: {name}")
            print(f"  Créé le: {created_date}")
            print(f"  Éléments: {f_count} factions, {l_count} lieux, {c_count} cultures, {p_count} personnages, {o_count} objets")
            print()
    
    # Activités récentes
    if activities:
        print("📝 ACTIVITÉS RÉCENTES")
        print("-" * 30)
        for activity in activities[:5]:  # Afficher seulement les 5 plus récentes
            table_name, created_at, content = activity
            created_date = datetime.fromisoformat(created_at).strftime('%d/%m/%Y %H:%M') if created_at else 'N/A'
            print(f"[{created_date}] {table_name}: {content}")

def main():
    """Fonction principale."""
    db_path = get_db_path()
    
    print(f"Analyse de la base de données: {db_path}")
    
    if not os.path.exists(db_path):
        print(f"Erreur: La base de données n'existe pas à {db_path}")
        return
    
    # Récupérer les statistiques
    stats = get_db_stats(db_path)
    universes = get_universe_details(db_path)
    activities = get_recent_activity(db_path)
    
    # Afficher dans la console
    print_stats_to_console(stats, universes, activities)
    
    # Générer le rapport Markdown
    report = generate_markdown_report(stats, universes, activities)
    
    # Sauvegarder le rapport
    report_file = "database_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Rapport sauvegardé dans: {report_file}")

if __name__ == "__main__":
    main() 