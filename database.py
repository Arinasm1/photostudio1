import sqlite3

DB_NAME = "photostudio.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            login TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price_per_hour REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS photographers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            specialization TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            photographer_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            is_busy INTEGER DEFAULT 0,
            FOREIGN KEY (photographer_id) REFERENCES photographers(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            photographer_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            hours INTEGER NOT NULL,
            total REAL NOT NULL,
            status TEXT NOT NULL,
            payment_method TEXT,
            FOREIGN KEY (client_id) REFERENCES clients(id),
            FOREIGN KEY (service_id) REFERENCES services(id),
            FOREIGN KEY (photographer_id) REFERENCES photographers(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            recipient TEXT NOT NULL,
            text TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    """)

    conn.commit()
    conn.close()


def seed_data():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM services")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO services (name, price_per_hour) VALUES (?, ?)",
            [
                ("Портретная съёмка", 5000.00),
                ("Семейная съёмка", 7000.00),
                ("Коммерческая съёмка", 12000.00),
            ]
        )

    cur.execute("SELECT COUNT(*) FROM photographers")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO photographers (full_name, specialization) VALUES (?, ?)",
            [
                ("Анна Смирнова", "Портретная"),
                ("Иван Петров", "Семейная"),
                ("Мария Иванова", "Коммерческая"),
            ]
        )

    cur.execute("SELECT COUNT(*) FROM clients")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO clients (full_name, phone, email, login, password_hash) VALUES (?, ?, ?, ?, ?)",
            ("Анна Смирнова", "+7 (999) 123-45-67", "anna@mail.ru", "client", "12345")
        )

    cur.execute("SELECT COUNT(*) FROM slots")
    if cur.fetchone()[0] == 0:
        slots = []
        for ph_id in (1, 2, 3):
            for date in ("2026-11-18", "2026-11-19", "2026-11-20"):
                for time in ("10:00", "14:00", "16:00"):
                    slots.append((ph_id, date, time, 0))
        cur.executemany(
            "INSERT INTO slots (photographer_id, date, time, is_busy) VALUES (?, ?, ?, ?)",
            slots
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    seed_data()
    print("База данных инициализирована и заполнена.")