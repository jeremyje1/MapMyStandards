import sqlite3

conn = sqlite3.connect('a3e_production.db')
cursor = conn.cursor()

try:
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    print(f'Users in database: {len(users)}')
    for user in users:
        print(f'  - {user}')
except Exception as e:
    print(f'Error: {e}')
finally:
    conn.close()
