import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'splitwise.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create members table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            upi_id TEXT
        )
    ''')
    
    # Create expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            payer_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (payer_id) REFERENCES members (id) ON DELETE CASCADE
        )
    ''')
    
    # Create splits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS splits (
            expense_id INTEGER NOT NULL,
            member_id INTEGER NOT NULL,
            PRIMARY KEY (expense_id, member_id),
            FOREIGN KEY (expense_id) REFERENCES expenses (id) ON DELETE CASCADE,
            FOREIGN KEY (member_id) REFERENCES members (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def add_member(name, upi_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Normalize UPI ID to empty string if not provided
    upi_val = upi_id.strip() if upi_id and upi_id.strip() else None
    cursor.execute('INSERT INTO members (name, upi_id) VALUES (?, ?)', (name.strip(), upi_val))
    conn.commit()
    member_id = cursor.lastrowid
    conn.close()
    return member_id

def get_members():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM members ORDER BY name ASC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def delete_member(member_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM members WHERE id = ?', (member_id,))
    conn.commit()
    conn.close()

def add_expense(description, amount, payer_id, split_member_ids):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('BEGIN TRANSACTION')
        cursor.execute(
            'INSERT INTO expenses (description, amount, payer_id, created_at) VALUES (?, ?, ?, ?)',
            (description.strip(), float(amount), int(payer_id), datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        expense_id = cursor.lastrowid
        
        for m_id in split_member_ids:
            cursor.execute('INSERT INTO splits (expense_id, member_id) VALUES (?, ?)', (expense_id, int(m_id)))
            
        conn.commit()
        return expense_id
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_expense(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()

def get_expenses_with_payer():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.*, m.name as payer_name 
        FROM expenses e
        JOIN members m ON e.payer_id = m.id
        ORDER BY e.created_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_splits_for_expense(expense_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.member_id, m.name 
        FROM splits s
        JOIN members m ON s.member_id = m.id
        WHERE s.expense_id = ?
    ''', (expense_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_all_splits():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM splits')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]
