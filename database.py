import sqlite3
from datetime import datetime

# Define the database schema
SCHEMA = {
    "items": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("item_name", "TEXT NOT NULL"),
        ("bought_price", "REAL NOT NULL"),
        ("sold_price", "REAL"),
        ("sold_date", "TEXT"),
        ("bought_date", "TEXT"),
        ("profit", "REAL")
    ]
}

def create_db():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    for table, columns in SCHEMA.items():
        columns_def = ", ".join(f"{name} {type}" for name, type in columns)
        c.execute(f"CREATE TABLE IF NOT EXISTS {table} ({columns_def})")
    conn.commit()
    conn.close()

def add_item(item_name, bought_price, sold_price=None, bought_date=None):
    if bought_date is None:
        bought_date = datetime.now().strftime('%Y-%m-%d')
    profit = None
    sold_date = None
    if sold_price is not None:
        profit = sold_price - bought_price
        sold_date = datetime.now().strftime('%Y-%m-%d')
    
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('INSERT INTO items (item_name, bought_price, sold_price, sold_date, bought_date, profit) VALUES (?, ?, ?, ?, ?, ?)', 
              (item_name, bought_price, sold_price, sold_date, bought_date, profit))
    conn.commit()
    conn.close()

def view_data():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT * FROM items')
    rows = c.fetchall()
    conn.close()
    return rows

def check_duplicate_item(item_name):
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT * FROM items WHERE item_name = ?', (item_name,))
    result = c.fetchone()
    conn.close()
    return result is not None

def delete_item(item_id):
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('DELETE FROM items WHERE id = ?', (item_id,))
    conn.commit()
    conn.close()

def update_item(item_id, column, new_value):
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    
    # Update the value based on the column being edited
    if column in ["bought_price", "sold_price"]:
        new_value = float(new_value)
        c.execute(f'UPDATE items SET {column} = ? WHERE id = ?', (new_value, item_id))
        
        # Recalculate profit if bought_price or sold_price is updated
        c.execute('SELECT bought_price, sold_price FROM items WHERE id = ?', (item_id,))
        bought_price, sold_price = c.fetchone()
        if sold_price is not None:
            profit = sold_price - bought_price
            c.execute('UPDATE items SET profit = ? WHERE id = ?', (profit, item_id))
            
        # Update sold_date only if it is currently None
        if column == "sold_price" and sold_price is not None:
            c.execute('SELECT sold_date FROM items WHERE id = ?', (item_id,))
            current_sold_date = c.fetchone()[0]
            if current_sold_date is None:
                sold_date = datetime.now().strftime('%Y-%m-%d')
                c.execute('UPDATE items SET sold_date = ? WHERE id = ?', (sold_date, item_id))
    else:
        c.execute(f'UPDATE items SET {column} = ? WHERE id = ?', (new_value, item_id))
    
    conn.commit()
    conn.close()

def get_item_id_from_db(item_name):
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT id FROM items WHERE item_name = ?', (item_name,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def calculate_total_profit():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT profit FROM items WHERE profit IS NOT NULL')
    profits = c.fetchall()
    total_profit = sum(profit[0] for profit in profits if profit[0] is not None)
    conn.close()
    return total_profit

def calculate_total_debt():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT bought_price FROM items WHERE sold_price IS NULL')
    bought_prices = c.fetchall()
    total_debt = sum(bought_price[0] for bought_price in bought_prices)
    conn.close()
    return total_debt
