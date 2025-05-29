import os

db_path = '../database.db'

if os.path.exists(db_path):
    os.remove(db_path)
    print(f"{db_path} has been deleted successfully!")
else:
    print(f"{db_path} does not exist.")