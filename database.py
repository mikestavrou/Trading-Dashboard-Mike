import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_NAME = "trading_dashboard.db"

def get_connection():
    """Establish and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Return dict-like rows
    return conn

def init_db():
    """Initialize the database with necessary tables."""
    conn = get_connection()
    c = conn.cursor()

    # Table: Strategies
    c.execute('''
        CREATE TABLE IF NOT EXISTS strategies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            entry_rules TEXT,
            exit_rules TEXT,
            risk_management TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Table: Strategy Examples (For the 50+ screenshots per strategy)
    c.execute('''
        CREATE TABLE IF NOT EXISTS strategy_examples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            strategy_id INTEGER NOT NULL,
            image_path TEXT NOT NULL,
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies (id) ON DELETE CASCADE
        )
    ''')

    # Table: Trades (The main Journal)
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT NOT NULL,
            entry_date TEXT,
            exit_date TEXT,
            direction TEXT CHECK(direction IN ('Long', 'Short')),
            strategy_id INTEGER,
            pnl REAL,
            image_path TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# --- Helper functions for Strategies ---
def add_strategy(name, description, entry_rules, exit_rules, risk_management):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO strategies (name, description, entry_rules, exit_rules, risk_management)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, description, entry_rules, exit_rules, risk_management))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Strategy name likely exists
    finally:
        conn.close()

def get_all_strategies():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM strategies", conn)
    conn.close()
    return df

# --- Helper functions for Strategy Examples ---
def add_strategy_example(strategy_id, image_path, comment):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO strategy_examples (strategy_id, image_path, comment)
        VALUES (?, ?, ?)
    ''', (strategy_id, image_path, comment))
    conn.commit()
    conn.close()

def get_strategy_examples(strategy_id):
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM strategy_examples WHERE strategy_id = ?", conn, params=(strategy_id,))
    conn.close()
    return df

def delete_strategy_example(example_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM strategy_examples WHERE id = ?", (example_id,))
    conn.commit()
    conn.close()

# --- Helper functions for Trades ---
def add_trade(symbol, entry_date, exit_date, direction, strategy_id, pnl, image_path, notes):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO trades (symbol, entry_date, exit_date, direction, strategy_id, pnl, image_path, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (symbol, entry_date, exit_date, direction, strategy_id, pnl, image_path, notes))
    conn.commit()
    conn.close()

def get_all_trades():
    conn = get_connection()
    query = '''
        SELECT t.*, s.name as strategy_name 
        FROM trades t 
        LEFT JOIN strategies s ON t.strategy_id = s.id
        ORDER BY t.created_at DESC
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def delete_trade(trade_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM trades WHERE id = ?", (trade_id,))
    conn.commit()
    conn.close()
