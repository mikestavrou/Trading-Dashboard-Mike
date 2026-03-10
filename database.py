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
            audio_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies (id) ON DELETE CASCADE
        )
    ''')
    
    # Check if audio_path needs to be added to an existing strategy_examples table
    c.execute("PRAGMA table_info(strategy_examples)")
    columns = [col[1] for col in c.fetchall()]
    if 'audio_path' not in columns:
        c.execute("ALTER TABLE strategy_examples ADD COLUMN audio_path TEXT")

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
            audio_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (strategy_id) REFERENCES strategies (id) ON DELETE CASCADE
        )
    ''')
    
    # Check if audio_path needs to be added to an existing trades table
    c.execute("PRAGMA table_info(trades)")
    columns = [col[1] for col in c.fetchall()]
    if 'audio_path' not in columns:
        c.execute("ALTER TABLE trades ADD COLUMN audio_path TEXT")

    # Table: Daily Loss Limits (one per day, locked once saved)
    c.execute('''
        CREATE TABLE IF NOT EXISTS daily_limits (
            date TEXT PRIMARY KEY,
            loss_limit REAL NOT NULL,
            locked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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

def delete_strategy(strategy_id):
    """Deletes a strategy and lets SQLite handle cascading deletes via foreign keys."""
    conn = get_connection()
    c = conn.cursor()
    # Execute PRAGMA foreign_keys = ON to ensure CASCADE works
    c.execute("PRAGMA foreign_keys = ON")
    
    # Also manually delete trades since older table creations might not have the CASCADE rule
    c.execute("DELETE FROM trades WHERE strategy_id = ?", (strategy_id,))
    c.execute("DELETE FROM strategy_examples WHERE strategy_id = ?", (strategy_id,))
    c.execute("DELETE FROM strategies WHERE id = ?", (strategy_id,))
    
    conn.commit()
    conn.close()

# --- Helper functions for Strategy Examples ---
def add_strategy_example(strategy_id, image_path, comment, audio_path=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO strategy_examples (strategy_id, image_path, comment, audio_path)
        VALUES (?, ?, ?, ?)
    ''', (strategy_id, image_path, comment, audio_path))
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
def add_trade(symbol, entry_date, exit_date, direction, strategy_id, pnl, image_path, notes, audio_path=None):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO trades (symbol, entry_date, exit_date, direction, strategy_id, pnl, image_path, notes, audio_path)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (symbol, entry_date, exit_date, direction, strategy_id, pnl, image_path, notes, audio_path))
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

# --- Daily Loss Limit helpers ---
def get_daily_limit(date_str):
    """Return the locked loss limit for date_str (YYYY-MM-DD), or None if not set."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT loss_limit FROM daily_limits WHERE date = ?", (date_str,))
    row = c.fetchone()
    conn.close()
    return float(row[0]) if row else None

def set_daily_limit(date_str, limit):
    """Save and lock the loss limit for date_str. No-op if already set."""
    conn = get_connection()
    c = conn.cursor()
    # Only insert — never update after lock (IGNORE on conflict)
    c.execute(
        "INSERT OR IGNORE INTO daily_limits (date, loss_limit) VALUES (?, ?)",
        (date_str, float(limit))
    )
    conn.commit()
    conn.close()
