import sqlite3


def create_database():
    connection = sqlite3.connect("database/pashumitra.db")
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            mobile TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE,
            password TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS animals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            animal_name TEXT NOT NULL,
            animal_type TEXT NOT NULL,
            gender TEXT NOT NULL,
            age_years INTEGER,
            age_months INTEGER,
            source TEXT NOT NULL,
            purchase_date DATE,
            purchase_cost REAL,
            pregnancy TEXT,
            pregnancy_date DATE,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS daily_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            animal_id INTEGER NOT NULL,
            record_date DATE NOT NULL,
            cattle_feed REAL DEFAULT 0,
            regular_grass REAL DEFAULT 0,
            doctor_cost REAL DEFAULT 0,
            morning_milk REAL DEFAULT 0,
            evening_milk REAL DEFAULT 0,
            income REAL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (animal_id) REFERENCES animals(id),
            UNIQUE(animal_id, record_date)
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    create_database()
    print("Database created successfully!")