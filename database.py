import sqlite3
from datetime import datetime

# Define the database schema
# when adding a new column, add it to the SCHEMA dictionary and edit the on_item_edit column count
SCHEMA = {
    "items": [
        ("id", "INTEGER PRIMARY KEY AUTOINCREMENT"),
        ("item_name", "TEXT NOT NULL"),
        ("description", "TEXT"),
        ("bought_price", "REAL NOT NULL"),
        ("expenses", "REAL"),  # Change type to REAL for calculations
        ("sold_price", "REAL"),
        ("bought_date", "TEXT"),
        ("sold_date", "TEXT"),
        ("profit", "REAL")
    ]
}

def create_db():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    for table, columns in SCHEMA.items():
        columns_def = ", ".join(f"{name} {type}" for name, type in columns)
        c.execute(f"CREATE TABLE IF NOT EXISTS {table} ({columns_def})")
        
        # Check for missing columns and add them
        c.execute(f"PRAGMA table_info({table})")
        existing_columns = [column[1] for column in c.fetchall()]
        for column, column_type in columns:
            if column not in existing_columns:
                c.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
                
    conn.commit()
    conn.close()

def add_item(item_name, bought_price, sold_price=None, bought_date=None, expenses=None, **kwargs):
    if bought_date is None:
        bought_date = datetime.now().strftime('%Y-%m-%d')
    profit = None
    sold_date = None
    if sold_price is not None:
        expenses = float(expenses) if expenses is not None else 0
        profit = sold_price - bought_price - expenses
        sold_date = datetime.now().strftime('%Y-%m-%d')
    
    # Prepare the columns and values for insertion
    columns = ["item_name", "bought_price", "sold_price", "sold_date", "bought_date", "expenses", "profit"]
    values = [item_name, bought_price, sold_price, sold_date, bought_date, expenses, profit]
    
    # Add additional columns from kwargs
    for column, _ in SCHEMA["items"]:
        if column not in columns:
            columns.append(column)
            values.append(kwargs.get(column, None))
    
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute(f'INSERT INTO items ({", ".join(columns)}) VALUES ({", ".join("?" for _ in values)})', values)
    conn.commit()
    conn.close()

def view_data():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT * FROM items')
    rows = c.fetchall()
    conn.close()
    return rows

def get_column_names():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('PRAGMA table_info(items)')
    columns = [column[1] for column in c.fetchall()]
    conn.close()
    return columns

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
    
    try:
        # Update the value based on the column being edited
        if column in ["bought_price", "sold_price", "expenses"]:
            new_value = float(new_value)
            c.execute(f'UPDATE items SET {column} = ? WHERE id = ?', (new_value, item_id))
            
            # Recalculate profit if bought_price, sold_price, or expenses is updated
            c.execute('SELECT bought_price, sold_price, expenses FROM items WHERE id = ?', (item_id,))
            result = c.fetchone()
            if result is None:
                raise ValueError(f"No item found with id {item_id}")
            bought_price, sold_price, expenses = result
            if sold_price is not None:
                expenses = float(expenses) if expenses is not None else 0
                profit = sold_price - bought_price - expenses
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
    except sqlite3.OperationalError as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

def get_item_id_from_db(item_name):
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT id FROM items WHERE item_name = ?', (item_name,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    print(f"Error: No item found with name {item_name}")  # Debugging information
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
