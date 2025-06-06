import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

#%%
# Faction
# cursor.execute('''
#     CREATE TABLE IF NOT EXISTS faction (
#         id INTEGER PRIMARY KEY AUTOINCREMENT,
#         name TEXT NOT NULL,
#         description TEXT
#     )
# ''')

# Faction
cursor.execute('''
    INSERT INTO faction (name, description)
    VALUES ('Faction A', 'Description of Faction A')
''')

#%%
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()

print("Tables existantes 😊")
for table in tables:
    print(table[0])

#%%
a = cursor.execute("""
SELECT *
FROM culture
""").fetchall()

print(a)

print(type(a))