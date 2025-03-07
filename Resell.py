import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
from datetime import datetime
import database 

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
        if database.check_duplicate_item(item_name):
            messagebox.showwarning("Duplicate Item", f"The item '{item_name}' already exists in the database.")
            return
        
        database.add_item(item_name, bought_price, sold_price)
        
        entry_item_name.delete(0, tk.END)
        entry_bought_price.delete(0, tk.END)
        entry_sold_price.delete(0, tk.END)
        load_data()
    else:
        messagebox.showwarning("Input Error", "Please enter a valid item and bought price.")

def color_total_profit():
    total_profit = database.calculate_total_profit()
    label_total_profit.config(text=f"Total Profit: ${total_profit:.2f}")
    if total_profit > 0:
        label_total_profit.config(text=f"Total Profit: ${total_profit:.2f}", fg="green")
    elif total_profit < 0:
        label_total_profit.config(text=f"Total Profit: ${total_profit:.2f}", fg="red")
    else:
        label_total_profit.config(text="Total Profit: $0.00", fg="yellow")

def color_total_debt():
    total_debt = database.calculate_total_debt()
    label_total_debt.config(text=f"Total Debt: ${total_debt:.2f}")
    if total_debt < 0:
        label_total_debt.config(text=f"Total Debt: ${total_debt:.2f}", fg="green")
    elif total_debt > 0:
        label_total_debt.config(text=f"Total Debt: ${total_debt:.2f}", fg="red")
    else:
        label_total_debt.config(text="Total Debt: $0.00", fg="green")

def load_data():
    for row in treeview.get_children():
        treeview.delete(row)

    # Fetch column names from the database
    columns = database.get_column_names()
    treeview["columns"] = columns

    # Create Treeview columns dynamically
    for col in columns:
        treeview.column(col, width=100)
        treeview.heading(col, text=col, command=lambda _col=col: sort_treeview_column(treeview, _col, False))

    data = database.view_data()
    for row in data:
        # Determine the tag based on the sold_price and bought_price
        sold_price = row[columns.index("sold_price")]
        bought_price = row[columns.index("bought_price")]
        tag = ""
        if sold_price is None:
            tag = "not_sold"
        elif sold_price > bought_price:
            tag = "profit"
        elif sold_price < bought_price:
            tag = "loss"

        treeview.insert("", "end", values=row, tags=(tag,))

    color_total_profit()
    color_total_debt()

def delete_item():
    selected_item = treeview.selection()
    if not selected_item:
        messagebox.showwarning("No Item Selected", "Please select an item to delete.")
        return

    item_name = treeview.item(selected_item, "values")[0]
    confirm = messagebox.askyesno("Delete Item", f"Are you sure you want to delete the item: {item_name}?")
    if confirm:
        item_id = database.get_item_id_from_db(item_name)
        if item_id:
            database.delete_item(item_id)
            load_data()
        else:
            messagebox.showwarning("Error", "Item not found in the database.")

def on_item_edit(event):
    item = treeview.focus()
    column = treeview.identify_column(event.x)
    
    if column in ['#1', '#2', '#3', '#4', '#5', '#6']:
        col_index = int(column[1:]) - 1
        old_value = treeview.item(item, "values")[col_index]
        new_value = simpledialog.askstring("Edit Value", f"Enter new value for {treeview.heading(column)['text']}:", initialvalue=old_value)

        if new_value is not None and new_value != old_value:
            item_id = database.get_item_id_from_db(treeview.item(item, "values")[0])
            column_name = treeview.heading(column)['text'].lower().replace(" ", "_")
            database.update_item(item_id, column_name, new_value)
            load_data()

def sort_treeview_column(treeview, col, reverse):
    data = [(treeview.set(child, col), child) for child in treeview.get_children('')]
    
    if col in ["Bought Price", "Sold Price", "Profit"]:
        data = [(float(value.strip('$').replace('Not Sold', '0')), child) for value, child in data]
    elif col == "Show Date":
        data = [(datetime.strptime(value, '%Y-%m-%d') if value != 'Not Sold' else datetime.min, child) for value, child in data]
    
    data.sort(reverse=reverse)
    
    for index, (val, child) in enumerate(data):
        treeview.move(child, '', index)
    
    treeview.heading(col, command=lambda: sort_treeview_column(treeview, col, not reverse))

def show_column_menu(event):
    column_menu.delete(0, tk.END)
    for col in treeview["columns"]:
        column_menu.add_command(label=f"Hide {col}", command=lambda _col=col: hide_column(_col))
    column_menu.add_separator()
    for col in hidden_columns:
        column_menu.add_command(label=f"Show {col}", command=lambda _col=col: show_column(_col))
    column_menu.post(event.x_root, event.y_root)

def hide_column(column):
    treeview.column(column, width=0, stretch=tk.NO)
    hidden_columns[column] = treeview.heading(column)["text"]
    treeview.heading(column, text="", anchor=tk.W)

def show_column(column):
    if column in hidden_columns:
        treeview.column(column, width=100, stretch=tk.YES)
        treeview.heading(column, text=hidden_columns[column], anchor=tk.W)
        del hidden_columns[column]

root = tk.Tk()
root.title("Resell Tracker")
root.geometry("800x600")

database.create_db()

frame_item_name = tk.Frame(root)
frame_item_name.pack(pady=5)

label_item_name = tk.Label(frame_item_name, text="Enter Item Name:")
label_item_name.pack(side=tk.LEFT, padx=5)

entry_item_name = tk.Entry(frame_item_name, width=50)
entry_item_name.pack(side=tk.LEFT, padx=5)

frame_bought_price = tk.Frame(root)
frame_bought_price.pack(pady=5)

label_bought_price = tk.Label(frame_bought_price, text="Enter Bought Price:")
label_bought_price.pack(side=tk.LEFT, padx=5)

entry_bought_price = tk.Entry(frame_bought_price, width=50)
entry_bought_price.pack(side=tk.LEFT, padx=5)

frame_sold_price = tk.Frame(root)
frame_sold_price.pack(pady=5)

label_sold_price = tk.Label(frame_sold_price, text="Enter Sold Price:")
label_sold_price.pack(side=tk.LEFT, padx=5)

entry_sold_price = tk.Entry(frame_sold_price, width=50)
entry_sold_price.pack(side=tk.LEFT, padx=5)

frame_buttons = tk.Frame(root)
frame_buttons.pack(pady=10)

button_add = tk.Button(frame_buttons, text="Add Item", command=add_data)
button_add.pack(side=tk.LEFT, padx=10)

button_load = tk.Button(frame_buttons, text="Load Data", command=load_data)
button_load.pack(side=tk.LEFT, padx=10)

button_delete = tk.Button(frame_buttons, text="Delete Item", command=delete_item)
button_delete.pack(side=tk.LEFT, padx=10)

frame_profit_debt = tk.Frame(root)
frame_profit_debt.pack(pady=10)

label_total_profit = tk.Label(frame_profit_debt, text="Total Profit: $0.00", font=("Arial", 14))
label_total_profit.pack(side=tk.LEFT, padx=10)

label_total_debt = tk.Label(frame_profit_debt, text="Total Debt: $0.00", font=("Arial", 14))
label_total_debt.pack(side=tk.LEFT, padx=10)

treeview = ttk.Treeview(root, show="headings")
treeview.pack(padx=10, pady=10, fill="both", expand=False)

treeview.tag_configure("not_sold", background="yellow2")
treeview.tag_configure("profit", background="springgreen2")
treeview.tag_configure("loss", background="brown1")

treeview.bind('<Double-1>', on_item_edit)

# Create a context menu for columns
column_menu = tk.Menu(root, tearoff=0)
hidden_columns = {}

# Bind right-click to show the column menu
treeview.bind("<Button-3>", show_column_menu)

load_data()
root.mainloop()
