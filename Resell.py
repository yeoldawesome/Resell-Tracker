import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
from datetime import datetime

import sqlite3

# Function to create a database and a table
def create_db():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute(''' 
        CREATE TABLE IF NOT EXISTS items (  
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT NOT NULL,
            bought_price REAL NOT NULL,
            sold_price REAL,
            sold_date TEXT,
            profit REAL
        )
    ''')
    conn.commit()
    conn.close()

# Function to retrieve all data from the database
def view_data():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT * FROM items')
    rows = c.fetchall()
    conn.close()
    return rows

# Function to add data to the database
def add_data():

    item_name = entry_item_name.get()
    bought_price = entry_bought_price.get()
    sold_price = entry_sold_price.get()

    try:
        bought_price = float(bought_price)
        if sold_price:
            sold_price = float(sold_price)
        else:
            sold_price = None
    except ValueError:
        messagebox.showwarning("Input Error", "Please enter valid prices.")
        return

    if item_name and bought_price >= 0:
        profit = None
        sold_date = None
        if sold_price is not None:
            profit = sold_price - bought_price  # Calculate profit when sold price is provided
            sold_date = datetime.now().strftime('%Y-%m-%d')  # Get today's date
        
        conn = sqlite3.connect('resell_tracker.db')
        c = conn.cursor()
        c.execute('INSERT INTO items (item_name, bought_price, sold_price, sold_date, profit) VALUES (?, ?, ?, ?, ?)', 
                  (item_name, bought_price, sold_price, sold_date, profit))
        conn.commit()
        conn.close()
        
        entry_item_name.delete(0, tk.END)  # Clear the item name input field
        entry_bought_price.delete(0, tk.END)  # Clear the bought price field
        entry_sold_price.delete(0, tk.END)  # Clear the sold price field
        load_data()  # Reload the data in the Treeview
    else:
        messagebox.showwarning("Input Error", "Please enter a valid item and bought price.")
        
def calculate_total_profit():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT profit FROM items WHERE sold_price IS NOT NULL')
    profits = c.fetchall()
    
    total_profit = sum(profit[0] for profit in profits if profit[0] is not None)  # Sum all non-None profits
    conn.close()
    
    # Update the label to show the total profit
    label_total_profit.config(text=f"Total Profit: ${total_profit:.2f}")

def calculate_total_debt():
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT bought_price FROM items WHERE sold_price IS NULL')
    bought_prices = c.fetchall()
    
    total_debt = sum(bought_price[0] for bought_price in bought_prices)  # Sum the bought prices for unsold items
    conn.close()
    
    # Update the label to show the total debt
    label_total_debt.config(text=f"Total Debt: ${total_debt:.2f}")

# Function to load data into the Treeview
def load_data():
    # Clear the existing rows in the Treeview
    for row in treeview.get_children():
        treeview.delete(row)

    data = view_data()
    for row in data:
        # Determine the row color based on the sold status and profit
        if row[3] is not None:  # sold_price is not None means the item is sold
            if row[3] > row[2]:  # Sold at a profit
                row_color = "lightgreen"
            else:  # Sold at a loss
                row_color = "lightcoral"
        else:  # Not sold
            row_color = "lightyellow"

        # Insert the row into the Treeview with the color tag applied
        treeview.insert("", "end", values=(row[1], f"${row[2]:.2f}", 
                                          f"${row[3] if row[3] is not None else 'Not Sold'}", 
                                          f"${row[3] - row[2]:.2f}" if row[3] is not None else "Not Sold", 
                                          row[4] if row[4] is not None else 'Not Sold'),
                        tags=(row_color,))  # Apply the color tag based on the status
    
    calculate_total_profit()
    calculate_total_debt()

# Function to handle double-click event on a cell
def on_double_click(event):
    # Get the item clicked in the Treeview
    item = treeview.selection()
    if not item:
        return  # If no item is selected, do nothing

    # Get the item_id (from first column which should hold the item name, or store item_id)
    item_id = treeview.item(item, "values")[0]  # Get the item name or id from the first column
    item_id = get_item_id_from_db(item_id)  # Fetch the actual ID from the database based on item name or description

    if not item_id:
        messagebox.showwarning("Error", "Item ID not found in the database.")
        return

    # Get the column clicked
    col_id = treeview.identify_column(event.x)
    column = int(col_id.split('#')[1]) - 1  # Convert column number to zero-based index

    if column == 0:  # Item Name column
        current_value = treeview.item(item, "values")[0]
        new_value = simple_input(f"Edit Item Name (Current: {current_value})")
        if new_value:
            treeview.item(item, values=(new_value, ) + treeview.item(item, "values")[1:])
            update_database(item_id, "item_name", new_value)

    elif column == 1:  # Bought Price column
        current_value = treeview.item(item, "values")[1]
        new_value = simple_input(f"Edit Bought Price (Current: {current_value})", float)
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], f"${new_value:.2f}") + treeview.item(item, "values")[2:])
            update_database(item_id, "bought_price", new_value)
            update_profit(item_id)  # Recalculate profit after bought price update

    elif column == 2:  # Sold Price column
        current_value = treeview.item(item, "values")[2]
        new_value = simple_input(f"Edit Sold Price (Current: {current_value})", float)
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], treeview.item(item, "values")[1], f"${new_value:.2f}") + treeview.item(item, "values")[3:])
            update_database(item_id, "sold_price", new_value)
            update_profit(item_id)  # Recalculate profit after sold price update

    elif column == 3:  # Profit column
        current_value = treeview.item(item, "values")[3]
        new_value = simple_input(f"Edit Profit (Current: {current_value})", float)
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], treeview.item(item, "values")[1], treeview.item(item, "values")[2], f"${new_value:.2f}") + treeview.item(item, "values")[4:])
            update_database(item_id, "profit", new_value)

    elif column == 4:  # Sold Date column
        current_value = treeview.item(item, "values")[4]
        new_value = simple_input(f"Edit Sold Date (Current: {current_value})")
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], treeview.item(item, "values")[1], treeview.item(item, "values")[2], treeview.item(item, "values")[3], new_value))
            update_database(item_id, "sold_date", new_value)
    # Get the item clicked in the Treeview
    item = treeview.selection()
    if not item:
        return  # If no item is selected, do nothing

    # Get the item_id (from first column which should hold the item name, or store item_id)
    item_id = treeview.item(item, "values")[0]  # Get the item name or id from the first column
    item_id = get_item_id_from_db(item_id)  # Fetch the actual ID from the database based on item name or description

    if not item_id:
        messagebox.showwarning("Error", "Item ID not found in the database.")
        return

    # Get the column clicked
    col_id = treeview.identify_column(event.x)
    column = int(col_id.split('#')[1]) - 1  # Convert column number to zero-based index

    if column == 0:  # Item Name column
        current_value = treeview.item(item, "values")[0]
        new_value = simple_input(f"Edit Item Name (Current: {current_value})")
        if new_value:
            treeview.item(item, values=(new_value, ) + treeview.item(item, "values")[1:])
            update_database(item_id, "item_name", new_value)

    elif column == 1:  # Bought Price column
        current_value = treeview.item(item, "values")[1]
        new_value = simple_input(f"Edit Bought Price (Current: {current_value})", float)
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], f"${new_value:.2f}") + treeview.item(item, "values")[2:])
            update_database(item_id, "bought_price", new_value)
            update_profit(item_id)  # Recalculate profit

    elif column == 2:  # Sold Price column
        current_value = treeview.item(item, "values")[2]
        new_value = simple_input(f"Edit Sold Price (Current: {current_value})", float)
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], treeview.item(item, "values")[1], f"${new_value:.2f}") + treeview.item(item, "values")[3:])
            update_database(item_id, "sold_price", new_value)
            update_profit(item_id)  # Recalculate profit

    elif column == 3:  # Profit column
        current_value = treeview.item(item, "values")[3]
        new_value = simple_input(f"Edit Profit (Current: {current_value})", float)
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], treeview.item(item, "values")[1], treeview.item(item, "values")[2], f"${new_value:.2f}") + treeview.item(item, "values")[4:])
            update_database(item_id, "profit", new_value)

    elif column == 4:  # Sold Date column
        current_value = treeview.item(item, "values")[4]
        new_value = simple_input(f"Edit Sold Date (Current: {current_value})")
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], treeview.item(item, "values")[1], treeview.item(item, "values")[2], treeview.item(item, "values")[3], new_value))
            update_database(item_id, "sold_date", new_value)

    # Get the item clicked in the Treeview
    item = treeview.selection()
    if not item:
        return  # If no item is selected, do nothing

    item_id = treeview.item(item, "values")[0]  # The item name (assuming it's in the first column)

    # Get the column clicked
    col_id = treeview.identify_column(event.x)
    column = int(col_id.split('#')[1]) - 1  # Convert column number to zero-based index

    if column == 0:  # Item Name column
        current_value = treeview.item(item, "values")[0]
        new_value = simple_input(f"Edit Item Name (Current: {current_value})")
        if new_value:
            treeview.item(item, values=(new_value, ) + treeview.item(item, "values")[1:])
            update_database(item_id, "item_name", new_value)

    elif column == 1:  # Bought Price column
        current_value = treeview.item(item, "values")[1]
        new_value = simple_input(f"Edit Bought Price (Current: {current_value})", float)
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], f"${new_value:.2f}") + treeview.item(item, "values")[2:])
            update_database(item_id, "bought_price", new_value)
            update_profit(item_id)  # Recalculate profit after bought price update

    elif column == 2:  # Sold Price column
        current_value = treeview.item(item, "values")[2]
        new_value = simple_input(f"Edit Sold Price (Current: {current_value})", float)
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], treeview.item(item, "values")[1], f"${new_value:.2f}") + treeview.item(item, "values")[3:])
            update_database(item_id, "sold_price", new_value)
            update_profit(item_id)  # Recalculate profit after sold price update

    elif column == 3:  # Profit column
        current_value = treeview.item(item, "values")[3]
        new_value = simple_input(f"Edit Profit (Current: {current_value})", float)
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], treeview.item(item, "values")[1], treeview.item(item, "values")[2], f"${new_value:.2f}") + treeview.item(item, "values")[4:])
            update_database(item_id, "profit", new_value)

    elif column == 4:  # Sold Date column
        current_value = treeview.item(item, "values")[4]
        new_value = simple_input(f"Edit Sold Date (Current: {current_value})")
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], treeview.item(item, "values")[1], treeview.item(item, "values")[2], treeview.item(item, "values")[3], new_value))
            update_database(item_id, "sold_date", new_value)

# Function to open a simple input box
def simple_input(prompt, type_func=str):
    value = tk.simpledialog.askstring("Edit Value", prompt)
    if value:
        try:
            return type_func(value)
        except ValueError:
            messagebox.showwarning("Input Error", "Invalid input value.")
    return None

# Function to update the database after editing
def update_database(item_id, column, new_value):
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute(f'''UPDATE items SET {column} = ? WHERE id = ?''', (new_value, item_id))
    conn.commit()
    conn.close()

# Function to update the profit calculation after any price changes
def update_profit(item_id):
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT bought_price, sold_price FROM items WHERE id = ?', (item_id,))
    result = c.fetchone()

    # If no result is returned, handle the situation
    if result is None:
        messagebox.showwarning("Database Error", "Item not found in the database.")
        conn.close()
        return
    
    bought_price, sold_price = result
    
    if sold_price is not None:
        profit = sold_price - bought_price
    else:
        profit = None  # Profit remains None if the item is unsold
    
    c.execute('UPDATE items SET profit = ? WHERE id = ?', (profit, item_id))
    conn.commit()
    conn.close()

    # Reload data to reflect updated profit
    load_data()    
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT bought_price, sold_price FROM items WHERE id = ?', (item_id,))
    result = c.fetchone()

    # If no result is returned, handle the situation
    if result is None:
        messagebox.showwarning("Database Error", "Item not found in the database.")
        conn.close()
        return
    
    bought_price, sold_price = result
    
    if sold_price is not None:
        profit = sold_price - bought_price
    else:
        profit = None  # Profit remains None if the item is unsold
    
    c.execute('UPDATE items SET profit = ? WHERE id = ?', (profit, item_id))
    conn.commit()
    conn.close()

def get_item_id_from_db(item_name):
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT id FROM items WHERE item_name = ?', (item_name,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]  # Return the item_id
    return None  # Return None if no item is found

# Set up the main application window
root = tk.Tk()
root.title("Resell Tracker")

# Create the database and table
create_db()

# Create input fields for adding data
label_item_name = tk.Label(root, text="Enter Item Name:")
label_item_name.pack(pady=5)

entry_item_name = tk.Entry(root, width=50)
entry_item_name.pack(pady=5)

label_bought_price = tk.Label(root, text="Enter Bought Price:")
label_bought_price.pack(pady=5)

entry_bought_price = tk.Entry(root, width=50)
entry_bought_price.pack(pady=5)

label_sold_price = tk.Label(root, text="Enter Sold Price (leave blank if not sold):")
label_sold_price.pack(pady=5)


entry_sold_price = tk.Entry(root, width=50)
entry_sold_price.pack(pady=5)

button_add = tk.Button(root, text="Add Item", command=add_data)
button_add.pack(pady=10)

label_total_profit = tk.Label(root, text="Total Profit: $0.00", font=("Arial", 14))
label_total_profit.pack(pady=10)

label_total_debt = tk.Label(root, text="Total Debt: $0.00", font=("Arial", 14))
label_total_debt.pack(pady=10)

# Create the Treeview widget (Excel-like table)
columns = ("Item Name", "Bought Price", "Sold Price", "Profit")
treeview = ttk.Treeview(root, columns=columns, show="headings", height=10)

# Define the column headers
for col in columns:
    treeview.heading(col, text=col)
    treeview.column(col, anchor="w", width=150)  # Width can be adjusted based on your data

# Define styles for the rows (using tags)
style = ttk.Style()
style.configure("lightgreen", background="green")  # Green for sold items with profit
style.configure("lightcoral", background="red")  # Red for sold items at a loss
style.configure("lightyellow", background="yellow")  # Yellow for unsold items

treeview.pack(pady=10)

# Bind double-click to edit the row
treeview.bind("<Double-1>", on_double_click)

# Button to load data into the Treeview
button_load = tk.Button(root, text="Load Data", command=load_data)
button_load.pack(pady=5)

# Start the app
load_data()  # Load data on startup
root.mainloop()
