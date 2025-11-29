import sqlite3
import os

DB_NAME = "atm.db"

def get_connection():
    """Returns a connection to the database."""
    return sqlite3.connect(DB_NAME)

def init_db():
    """Initializes the database and creates the table with initial data."""
    conn = get_connection()
    cur = conn.cursor()
    
    # Create the table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            pin TEXT NOT NULL,
            balance INTEGER NOT NULL
        )
    """)
    conn.commit()

    # Populate with initial data if the table is empty
    cur.execute("SELECT COUNT(*) FROM customers")
    count = cur.fetchone()[0]
    if count == 0:
        initial_customers = [
            ("Avi Cohen", "1234", 1000),
            ("Yossi Cohen", "6543", 500),
            ("Yuri Levi", "5852", 800),
        ]
        cur.executemany(
            "INSERT INTO customers (name, pin, balance) VALUES (?, ?, ?)",
            initial_customers
        )
        conn.commit()
    
    conn.close()

def get_customer_by_name(name):
    """Finds a customer by name (case insensitive)."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, pin, balance FROM customers WHERE LOWER(name) = LOWER(?)",
        (name,)
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"id": row[0], "name": row[1], "pin": row[2], "balance": row[3]}
    return None

def update_balance(customer_id, new_balance):
    """Updates the customer's balance."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE customers SET balance = ? WHERE id = ?",
        (new_balance, customer_id)
    )
    conn.commit()
    conn.close()

def update_pin(customer_id, new_pin):
    """Updates the customer's PIN."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "UPDATE customers SET pin = ? WHERE id = ?",
        (new_pin, customer_id)
    )
    conn.commit()
    conn.close()

def get_customer_balance(customer_id):
    """Gets the current balance of the customer."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT balance FROM customers WHERE id = ?", (customer_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
