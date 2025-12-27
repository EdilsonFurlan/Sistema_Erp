import sqlite3
import os

db_path = 'db.sqlite3'

if not os.path.exists(db_path):
    print("Database not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("Cleaning sales_pedidoitem.produto_id...")
try:
    cursor.execute("UPDATE sales_pedidoitem SET produto_id = NULL")
    conn.commit()
    print("Updated rows successfully. produto_id is now NULL.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
