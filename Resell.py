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
        
        messagebox.showinfo("Success", "Item added successfully!")
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
    if total_profit > 0:
        label_total_profit.config(text=f"Total Profit: ${total_profit:.2f}", fg="green")
    elif total_profit < 0:
        label_total_profit.config(text=f"Total Profit: ${total_profit:.2f}", fg="red")
    else:
        label_total_profit.config(text="Total Profit: $0.00", fg="yellow")


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
        # Insert the row into the Treeview without color tags
        item_name = row[1]
        bought_price = f"${row[2]:.2f}"
        sold_price = f"${row[3] if row[3] is not None else 'Not Sold'}"
        profit = f"${row[3] - row[2]:.2f}" if row[3] is not None else "Not Sold"
        sold_date = row[4] if row[4] is not None else 'Not Sold'

        # Add the item to the treeview, applying color based on conditions
        tag = ""
        if row[3] is None:  # Not Sold items
            tag = "not_sold"
        elif row[3] and row[3] > row[2]:  # Profit made
            tag = "profit"
        elif row[3] and row[3] < row[2]:  # Loss made
            tag = "loss"

        treeview.insert("", "end", values=(item_name, bought_price, sold_price, profit, sold_date), tags=(tag,))

    calculate_total_profit()
    calculate_total_debt()

# Function to handle double-click event on a cell
def on_double_click(event):
    item = treeview.selection()
    if not item:
        return  # If no item is selected, do nothing

    item_id = treeview.item(item, "values")[0]  # Get the item name or id from the first column
    item_id = get_item_id_from_db(item_id)  # Fetch the actual ID from the database based on item name

    if not item_id:
        messagebox.showwarning("Error", "Item ID not found in the database.")
        return

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
            update_profit(item_id)

    elif column == 2:  # Sold Price column
        current_value = treeview.item(item, "values")[2]
        new_value = simple_input(f"Edit Sold Price (Current: {current_value})", float)
        if new_value:
            treeview.item(item, values=(treeview.item(item, "values")[0], treeview.item(item, "values")[1], f"${new_value:.2f}") + treeview.item(item, "values")[3:])
            update_database(item_id, "sold_price", new_value)
            update_profit(item_id)

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

    if result is None:
        messagebox.showwarning("Error", "Item not found.")
        return

    bought_price, sold_price = result
    profit = sold_price - bought_price if sold_price is not None else None

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


# Creating the main window
root = tk.Tk()
root.title("Resell Tracker")
root.geometry("800x600")  # Change the size as needed

# Create the database if not already created
create_db()

# Create a frame for the add item and profit/debt labels
# Frame for Item Name entry
frame_item_name = tk.Frame(root)
frame_item_name.pack(pady=5)

label_item_name = tk.Label(frame_item_name, text="Enter Item Name:")
label_item_name.pack(side=tk.LEFT, padx=5)

entry_item_name = tk.Entry(frame_item_name, width=50)
entry_item_name.pack(side=tk.LEFT, padx=5)

# Frame for Bought Price entry
frame_bought_price = tk.Frame(root)
frame_bought_price.pack(pady=5)

label_bought_price = tk.Label(frame_bought_price, text="Enter Bought Price:")
label_bought_price.pack(side=tk.LEFT, padx=5)

entry_bought_price = tk.Entry(frame_bought_price, width=50)
entry_bought_price.pack(side=tk.LEFT, padx=5)

# Frame for Sold Price entry
frame_sold_price = tk.Frame(root)
frame_sold_price.pack(pady=5)

label_sold_price = tk.Label(frame_sold_price, text="Enter Sold Price:")
label_sold_price.pack(side=tk.LEFT, padx=5)

entry_sold_price = tk.Entry(frame_sold_price, width=50)
entry_sold_price.pack(side=tk.LEFT, padx=5)

frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)

# Add Item button
button_add = tk.Button(frame_buttons, text="Add Item", command=add_data)
button_add.pack(side=tk.LEFT, padx=10)

# Load Data button
button_load = tk.Button(frame_buttons, text="Load Data", command=load_data)
button_load.pack(side=tk.LEFT, padx=10)

frame_profit_debt = tk.Frame(root)
frame_profit_debt.pack(pady=10)

# Total Profit label
label_total_profit = tk.Label(frame_profit_debt, text="Total Profit: $0.00", font=("Arial", 14))
label_total_profit.pack(side=tk.LEFT, padx=10)

# Total Debt label
label_total_debt = tk.Label(frame_profit_debt, text="Total Debt: $0.00", font=("Arial", 14))
label_total_debt.pack(side=tk.LEFT, padx=10)

# Create the Treeview below
treeview = ttk.Treeview(root, columns=("Item Name", "Bought Price", "Sold Price", "Profit"), show="headings")
treeview.pack(padx=10, pady=10, fill="both", expand=True)

# Create headings for the Treeview
for col in treeview["columns"]:
    treeview.heading(col, text=col)

# Add some colors for specific tags
treeview.tag_configure("not_sold", background="yellow2")  
treeview.tag_configure("profit", background="springgreen2")
treeview.tag_configure("loss", background="coral")

# Bind double-click event to edit cell
treeview.bind("<Double-1>", on_double_click)

# Load initial data
load_data()

# Start the Tkinter main loop
root.mainloop()
