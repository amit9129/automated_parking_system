import sqlite3

DATABASE = 'vehicles.db'  # Change this if necessary

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_number TEXT NOT NULL,
                entry_time TEXT NOT NULL,
                slot INTEGER NOT NULL,
                amount INTEGER NOT NULL,
                exit_time TEXT,
                is_paid BOOLEAN DEFAULT 0
            )
        ''')
        conn.commit()

if __name__ == '__main__':
    init_db()  # You can run this script to set up your database
