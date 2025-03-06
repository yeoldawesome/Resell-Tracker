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

# Function to check if an item already exists in the database
def check_duplicate_item(item_name):
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT * FROM items WHERE item_name = ?', (item_name,))
    result = c.fetchone()  # Fetch the first matching result
    conn.close()
    return result is not None  # If a result is found, it means the item already exists

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
        # Check if the item already exists
        if check_duplicate_item(item_name):
            messagebox.showwarning("Duplicate Item", f"The item '{item_name}' already exists in the database.")
            return
        
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
    c.execute('SELECT profit FROM items WHERE profit IS NOT NULL')
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
    if total_debt < 0:
        label_total_debt.config(text=f"Total Debt: ${total_debt:.2f}", fg="green")
    elif total_debt > 0:
        label_total_debt.config(text=f"Total Debt: ${total_debt:.2f}", fg="red")
    else:
        label_total_debt.config(text="Total Debt: $0.00", fg="green")

# Function to load data into the Treeview
def load_data():
    # Clear the existing rows in the Treeview
    for row in treeview.get_children():
        treeview.delete(row)

    data = view_data()
    for row in data:
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

# Function to delete selected item from the Treeview and the database
def delete_item():
    selected_item = treeview.selection()
    if not selected_item:
        messagebox.showwarning("No Item Selected", "Please select an item to delete.")
        return

    item_name = treeview.item(selected_item, "values")[0]  # Get the item name from the selected row
    
    confirm = messagebox.askyesno("Delete Item", f"Are you sure you want to delete the item: {item_name}?")
    if confirm:
        # Get the item ID from the database
        item_id = get_item_id_from_db(item_name)
        if item_id:
            conn = sqlite3.connect('resell_tracker.db')
            c = conn.cursor()
            c.execute('DELETE FROM items WHERE id = ?', (item_id,))
            conn.commit()
            conn.close()
            load_data()  # Reload the data in the Treeview
        else:
            messagebox.showwarning("Error", "Item not found in the database.")

# Function to get the item ID from the database based on the item name
def get_item_id_from_db(item_name):
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()
    c.execute('SELECT id FROM items WHERE item_name = ?', (item_name,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]  # Return the item_id
    return None  # Return None if no item is found

# Function to handle the cell editing
def on_item_edit(event):
    item = treeview.focus()  # Get the selected row
    column = treeview.identify_column(event.x)  # Get the column of the clicked cell
    
    if column in ['#1', '#2', '#3', '#4', '#5']:  # Check if the clicked column is editable
        col_index = int(column[1:]) - 1
        old_value = treeview.item(item, "values")[col_index]

        # Use a simple dialog to get the new value
        new_value = simpledialog.askstring("Edit Value", f"Enter new value for {treeview.heading(column)['text']}:", initialvalue=old_value)

        if new_value is not None and new_value != old_value:  # If the value has changed
            # Update the database with the new value
            update_item(item, col_index, new_value)
            load_data()  # Reload data to show updated values

# Function to update the database with the edited value
def update_item(item, col_index, new_value):
    item_name = treeview.item(item, "values")[0]
    conn = sqlite3.connect('resell_tracker.db')
    c = conn.cursor()

    # Update the value based on the column being edited
    if col_index == 0:  # Item name
        c.execute('UPDATE items SET item_name = ? WHERE item_name = ?', (new_value, item_name))
    elif col_index == 1:  # Bought price
        new_value = float(new_value)
        c.execute('UPDATE items SET bought_price = ? WHERE item_name = ?', (new_value, item_name))
    elif col_index == 2:  # Sold price
        new_value = float(new_value)
        c.execute('UPDATE items SET sold_price = ? WHERE item_name = ?', (new_value, item_name))
        # Update profit and sold_date when sold price is updated
        c.execute('UPDATE items SET profit = sold_price - bought_price, sold_date = ? WHERE item_name = ?', 
                  (datetime.now().strftime('%Y-%m-%d'), item_name))
    elif col_index == 3:  # Profit
        new_value = float(new_value)
        c.execute('UPDATE items SET profit = ? WHERE item_name = ?', (new_value, item_name))
    elif col_index == 4:  # Show Date
        c.execute('UPDATE items SET sold_date = ? WHERE item_name = ?', (new_value, item_name))
    
    conn.commit()
    conn.close()
    calculate_total_profit()
    calculate_total_debt()

def sort_treeview_column(treeview, col, reverse):
    data = [(treeview.set(child, col), child) for child in treeview.get_children('')]
    
    # Convert data to appropriate types for sorting
    if col in ["Bought Price", "Sold Price", "Profit"]:
        data = [(float(value.strip('$').replace('Not Sold', '0')), child) for value, child in data]
    elif col == "Show Date":
        data = [(datetime.strptime(value, '%Y-%m-%d') if value != 'Not Sold' else datetime.min, child) for value, child in data]
    
    # Sort data
    data.sort(reverse=reverse)
    
    # Rearrange items in sorted positions
    for index, (val, child) in enumerate(data):
        treeview.move(child, '', index)
    
    # Reverse sort next time
    treeview.heading(col, command=lambda: sort_treeview_column(treeview, col, not reverse))

# Creating the main window
root = tk.Tk()
root.title("Resell Tracker")
root.geometry("800x600")  # Change the size as needed

# Create the database if not already created
create_db()

# Create a frame for the add item and profit/debt labels
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

# Delete Item button
button_delete = tk.Button(frame_buttons, text="Delete Item", command=delete_item)
button_delete.pack(side=tk.LEFT, padx=10)

frame_profit_debt = tk.Frame(root)
frame_profit_debt.pack(pady=10)

# Total Profit label
label_total_profit = tk.Label(frame_profit_debt, text="Total Profit: $0.00", font=("Arial", 14))
label_total_profit.pack(side=tk.LEFT, padx=10)

# Total Debt label
label_total_debt = tk.Label(frame_profit_debt, text="Total Debt: $0.00", font=("Arial", 14))
label_total_debt.pack(side=tk.LEFT, padx=10)

# Create the Treeview below
treeview = ttk.Treeview(root, columns=("Item Name", "Bought Price", "Sold Price", "Profit", "Show Date"), show="headings")
treeview.pack(padx=10, pady=10, fill="both", expand=False)
treeview.column("Item Name", width=150)
treeview.column("Bought Price", width=100)
treeview.column("Sold Price", width=100)
treeview.column("Profit", width=100)
treeview.column("Show Date", width=80)

# Create headings for the Treeview and bind the sorting function
for col in treeview["columns"]:
    treeview.heading(col, text=col, command=lambda _col=col: sort_treeview_column(treeview, _col, False))

# Add some colors for specific tags
treeview.tag_configure("not_sold", background="yellow2")  
treeview.tag_configure("profit", background="springgreen2")
treeview.tag_configure("loss", background="brown1")

# Bind double click to trigger editing functionality
treeview.bind('<Double-1>', on_item_edit)
load_data()
# Start the application
root.mainloop()
