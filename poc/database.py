import sqlite3
import os

def create_database():
    conn = sqlite3.connect('../database.db')
    cursor = conn.cursor()

    # Univers
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS univers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT
            )
        ''')

    # Faction
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS faction (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            univers_id INTEGER,
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Culture
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS culture (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            univers_id INTEGER,
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Technology_Magic
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS technology_magic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            culture_id INTEGER,
            univers_id INTEGER,
            FOREIGN KEY (culture_id) REFERENCES culture(id),
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Character
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS character (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            location_id INTEGER,
            culture_id INTEGER,
            faction_id INTEGER,
            univers_id INTEGER,
            FOREIGN KEY (location_id) REFERENCES location(id),
            FOREIGN KEY (culture_id) REFERENCES culture(id),
            FOREIGN KEY (faction_id) REFERENCES faction(id),
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Quest
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quest (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            univers_id INTEGER,
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Item
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS item (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            owner_character_id INTEGER,
            location_id INTEGER,
            univers_id INTEGER,
            FOREIGN KEY (owner_character_id) REFERENCES character(id),
            FOREIGN KEY (location_id) REFERENCES location(id),
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Creature
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS creature (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            location_id INTEGER,
            univers_id INTEGER,
            FOREIGN KEY (location_id) REFERENCES location(id),
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Location
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS location (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            parent_location_id INTEGER,
            univers_id INTEGER,
            FOREIGN KEY (parent_location_id) REFERENCES location(id),
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Event
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS event (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            location_id INTEGER,
            univers_id INTEGER,
            FOREIGN KEY (location_id) REFERENCES location(id),
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Table de liaison: character_quest (many-to-many)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS character_quest (
            character_id INTEGER,
            quest_id INTEGER,
            univers_id INTEGER,
            PRIMARY KEY (character_id, quest_id),
            FOREIGN KEY (character_id) REFERENCES character(id),
            FOREIGN KEY (quest_id) REFERENCES quest(id),
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Table de liaison: quest_item (many-to-many)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quest_item (
            quest_id INTEGER,
            item_id INTEGER,
            univers_id INTEGER,
            PRIMARY KEY (quest_id, item_id),
            FOREIGN KEY (quest_id) REFERENCES quest(id),
            FOREIGN KEY (item_id) REFERENCES item(id),
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Table de liaison: quest_creature (many-to-many)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quest_creature (
            quest_id INTEGER,
            creature_id INTEGER,
            univers_id INTEGER,
            PRIMARY KEY (quest_id, creature_id),
            FOREIGN KEY (quest_id) REFERENCES quest(id),
            FOREIGN KEY (creature_id) REFERENCES creature(id),
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')

    # Table de liaison: character_faction (many-to-many, groups)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS character_faction (
            character_id INTEGER,
            faction_id INTEGER,
            univers_id INTEGER,
            PRIMARY KEY (character_id, faction_id),
            FOREIGN KEY (character_id) REFERENCES character(id),
            FOREIGN KEY (faction_id) REFERENCES faction(id),
            FOREIGN KEY (univers_id) REFERENCES univers(id)
        )
    ''')


    conn.commit()
    conn.close()
    print("Base de données et tables créées avec succès !")

if __name__ == "__main__":
    # Create the database and insert sample data
    create_database()
    print("Database created successfully!")
    