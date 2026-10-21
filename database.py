import sqlite3
import json
import uuid
from datetime import datetime
from config import DB_PATH, DEFAULT_STORE_NAME, DEFAULT_TAX_RATE, DEFAULT_CURRENCY

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Wallet Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wallet (
            id INTEGER PRIMARY KEY,
            balance REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            updated_at TEXT NOT NULL
        )
    """)

    # Products Table for POS & E-commerce
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sku TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0,
            icon TEXT NOT NULL DEFAULT 'shopping_bag',
            description TEXT
        )
    """)

    # Transactions Table (POS sales, P2P Transfers, PayPal orders, Top-ups)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL DEFAULT 'USD',
            fee REAL NOT NULL DEFAULT 0.0,
            net REAL NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL,
            counterparty TEXT,
            paypal_order_id TEXT,
            reference_note TEXT,
            timestamp TEXT NOT NULL,
            items_json TEXT
        )
    """)

    # Settings Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)

    conn.commit()

    # Seed initial data if empty
    cursor.execute("SELECT COUNT(*) as count FROM wallet")
    if cursor.fetchone()["count"] == 0:
        cursor.execute(
            "INSERT INTO wallet (id, balance, currency, updated_at) VALUES (1, ?, ?, ?)",
            (2450.00, DEFAULT_CURRENCY, datetime.now().isoformat())
        )

    # Seed settings if empty
    default_settings = {
        "store_name": DEFAULT_STORE_NAME,
        "tax_rate": str(DEFAULT_TAX_RATE),
        "currency": DEFAULT_CURRENCY,
        "paypal_mode": "sandbox",
        "paypal_client_id": "",
        "paypal_client_secret": "",
        "simulation_mode": "true"
    }
    for k, v in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))

    # Seed products if empty
    cursor.execute("SELECT COUNT(*) as count FROM products")
    if cursor.fetchone()["count"] == 0:
        seed_products = [
            ("Wireless Noise-Canceling Headphones", "TECH-001", "Electronics", 149.99, 25, "headphones", "Premium over-ear Bluetooth headphones with 30hr battery."),
            ("Ultra-Slim Mechanical Keyboard", "TECH-002", "Electronics", 89.50, 40, "keyboard", "RGB tactile mechanical keyboard with wireless dongle."),
            ("Ergonomic Wireless Mouse", "TECH-003", "Electronics", 49.99, 60, "mouse", "Precision laser sensor with multi-device fast pairing."),
            ("Organic Cold Brew Blend (1kg)", "BEV-001", "Beverages", 24.00, 100, "local_cafe", "Single-origin Arabica dark roast, steeped to perfection."),
            ("Artisan Matcha Green Tea", "BEV-002", "Beverages", 18.50, 80, "emoji_food_beverage", "Ceremonial grade pure stone-ground matcha powder."),
            ("Minimalist Leather Cardholder", "ACC-001", "Accessories", 35.00, 45, "credit_card", "Hand-stitched genuine calfskin with RFID blocking."),
            ("Smart Water Bottle with LED Temp", "ACC-002", "Accessories", 29.99, 50, "water_drop", "Vacuum insulated stainless steel with temperature display."),
            ("Cloud Storage Subscription (1 Year)", "SRV-001", "Services", 79.99, 999, "cloud_queue", "1TB encrypted cloud storage with automatic sync.")
        ]
        cursor.executemany("""
            INSERT INTO products (name, sku, category, price, stock, icon, description)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, seed_products)

    # Seed sample transactions if empty
    cursor.execute("SELECT COUNT(*) as count FROM transactions")
    if cursor.fetchone()["count"] == 0:
        sample_transactions = [
            (
                "TX-1001",
                "pos_sale",
                149.99,
                "USD",
                4.65,
                145.34,
                "completed",
                "Customer: alex.jones@example.com",
                "PAYID-MOCK89211A",
                "POS Order #1001 - Wireless Headphones",
                datetime.now().strftime("%Y-%m-%d 09:15"),
                json.dumps([{"name": "Wireless Noise-Canceling Headphones", "qty": 1, "price": 149.99}])
            ),
            (
                "TX-1002",
                "transfer_received",
                120.00,
                "USD",
                0.0,
                120.00,
                "completed",
                "sarah.designer@gmail.com",
                "PAYID-P2P33912",
                "Payment for UI consultation",
                datetime.now().strftime("%Y-%m-%d 10:45"),
                "[]"
            ),
            (
                "TX-1003",
                "transfer_sent",
                65.00,
                "USD",
                0.0,
                -65.00,
                "completed",
                "hosting-provider@domain.com",
                "PAYID-P2P88219",
                "Monthly dedicated cloud server",
                datetime.now().strftime("%Y-%m-%d 11:30"),
                "[]"
            ),
            (
                "TX-1004",
                "wallet_deposit",
                500.00,
                "USD",
                0.0,
                500.00,
                "completed",
                "Bank Account (Chase ****4129)",
                "PAYID-DEP55102",
                "Direct wallet deposit via PayPal Bank Link",
                datetime.now().strftime("%Y-%m-%d 08:00"),
                "[]"
            )
        ]
        cursor.executemany("""
            INSERT INTO transactions (id, type, amount, currency, fee, net, status, counterparty, paypal_order_id, reference_note, timestamp, items_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, sample_transactions)

    conn.commit()
    conn.close()

# Wallet operations
def get_wallet():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM wallet WHERE id = 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"id": 1, "balance": 0.0, "currency": "USD", "updated_at": datetime.now().isoformat()}

def update_wallet_balance(delta: float):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM wallet WHERE id = 1")
    current = cursor.fetchone()["balance"]
    new_balance = max(0.0, current + delta)
    cursor.execute(
        "UPDATE wallet SET balance = ?, updated_at = ? WHERE id = 1",
        (new_balance, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()
    return new_balance

# Products operations
def get_products(category=None, search=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    if category and category != "All":
        query += " AND category = ?"
        params.append(category)
    if search:
        query += " AND (name LIKE ? OR sku LIKE ? OR description LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term])
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def get_product(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def add_product(name, sku, category, price, stock, icon="shopping_bag", description=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products (name, sku, category, price, stock, icon, description)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (name, sku, category, float(price), int(stock), icon, description))
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def update_product(product_id, name, sku, category, price, stock, icon, description):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE products
        SET name = ?, sku = ?, category = ?, price = ?, stock = ?, icon = ?, description = ?
        WHERE id = ?
    """, (name, sku, category, float(price), int(stock), icon, description, product_id))
    conn.commit()
    conn.close()

def delete_product(product_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def deduct_product_stock(product_id: int, quantity: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE products SET stock = MAX(0, stock - ?) WHERE id = ?", (quantity, product_id))
    conn.commit()
    conn.close()

# Transactions operations
def get_transactions(limit=100, filter_type=None, search=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    if filter_type and filter_type != "All":
        query += " AND type = ?"
        params.append(filter_type)
    if search:
        query += " AND (counterparty LIKE ? OR paypal_order_id LIKE ? OR reference_note LIKE ? OR id LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)
    cursor.execute(query, params)
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def create_transaction(tx_type, amount, currency, fee, net, status, counterparty, paypal_order_id, reference_note, items_list=None):
    conn = get_connection()
    cursor = conn.cursor()
    tx_id = f"TX-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items_json = json.dumps(items_list or [])

    cursor.execute("""
        INSERT INTO transactions (id, type, amount, currency, fee, net, status, counterparty, paypal_order_id, reference_note, timestamp, items_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, tx_type, amount, currency, fee, net, status, counterparty, paypal_order_id, reference_note, timestamp, items_json))

    conn.commit()
    conn.close()
    return tx_id

def get_transaction(tx_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE id = ?", (tx_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

# Settings operations
def get_setting(key: str, default: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row["value"] if row else default

def set_setting(key: str, value: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

def get_all_settings():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    rows = {r["key"]: r["value"] for r in cursor.fetchall()}
    conn.close()
    return rows

# Dashboard Stats Helper
def get_dashboard_summary():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Wallet balance
    cursor.execute("SELECT balance, currency FROM wallet WHERE id = 1")
    w = cursor.fetchone()
    balance = w["balance"] if w else 0.0
    currency = w["currency"] if w else "USD"

    # Total Sales Volume (POS sales + received)
    cursor.execute("SELECT SUM(amount) as total, COUNT(*) as count FROM transactions WHERE type IN ('pos_sale', 'transfer_received') AND status = 'completed'")
    sales = cursor.fetchone()
    total_sales = sales["total"] if sales and sales["total"] else 0.0
    sales_count = sales["count"] if sales else 0

    # Total Spent / Sent
    cursor.execute("SELECT SUM(amount) as total FROM transactions WHERE type IN ('transfer_sent', 'wallet_withdraw') AND status = 'completed'")
    spent_row = cursor.fetchone()
    total_sent = spent_row["total"] if spent_row and spent_row["total"] else 0.0

    # Low Stock Items count (stock < 10)
    cursor.execute("SELECT COUNT(*) as count FROM products WHERE stock < 10")
    low_stock = cursor.fetchone()["count"]

    conn.close()
    return {
        "balance": balance,
        "currency": currency,
        "total_sales": total_sales,
        "sales_count": sales_count,
        "total_sent": total_sent,
        "low_stock_count": low_stock
    }
