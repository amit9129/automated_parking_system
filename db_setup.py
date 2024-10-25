# db_setup.py
import sqlite3

def setup_database():
    conn = sqlite3.connect('parking_system.db')
    c = conn.cursor()
    
    # Create table for vehicle details
    c.execute('''CREATE TABLE IF NOT EXISTS vehicles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    vehicle_number TEXT NOT NULL,
                    entry_time TEXT NOT NULL,
                    slot_assigned INTEGER NOT NULL,
                    payment_status TEXT DEFAULT 'Pending'
                )''')

    # Create table for parking slots
    c.execute('''CREATE TABLE IF NOT EXISTS slots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    is_occupied BOOLEAN NOT NULL DEFAULT 0
                )''')

    # Insert default slots (let's say 10)
    for i in range(1, 11):
        c.execute('INSERT INTO slots (is_occupied) VALUES (0)')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
