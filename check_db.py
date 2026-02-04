import sqlite3

def check_database():
    conn = sqlite3.connect('data/semantic_engine.db')
    cursor = conn.cursor()
    
    # Check existing tables
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    print('Existing tables:', [t[0] for t in tables])
    
    # Check predatory_list table structure
    cursor.execute('PRAGMA table_info(predatory_list)')
    predatory_info = cursor.fetchall()
    print('\nPredatory_list table structure:')
    for col in predatory_info:
        print(f'  {col[1]} {col[2]}')
    
    conn.close()

if __name__ == '__main__':
    check_database()