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
        
        # Set bought_price to None if it is 0
        if bought_price == 0:
            bought_price = None
        
        database.add_item(item_name, bought_price, sold_price)
        
        entry_item_name.delete(0, tk.END)
        entry_bought_price.delete(0, tk.END)
        entry_sold_price.delete(0, tk.END)
        load_data()
    else:
        messagebox.showwarning("Input Error", "Please enter a valid item and bought price.")

def add_expenditure():
    item_name = entry_item_name.get()
    expenses = entry_bought_price.get()  # Use the bought price field for expenses
    sold_price = entry_sold_price.get()

    try:
        expenses = float(expenses)
        if sold_price:
            sold_price = float(sold_price)
        else:
            sold_price = None
    except ValueError:
        messagebox.showwarning("Input Error", "Please enter valid prices.")
        return

    if item_name and expenses >= 0:
        if database.check_duplicate_item(item_name):
            messagebox.showwarning("Duplicate Item", f"The item '{item_name}' already exists in the database.")
            return
        
        # Calculate profit for expenditure
        profit = -expenses  # Set profit as negative value of expenses
        if sold_price is not None:
            profit = sold_price - expenses
        
        database.add_item(item_name, 0, sold_price, expenses=expenses, profit=profit)  # Set bought_price to 0 and add expenses
        
        entry_item_name.delete(0, tk.END)
        entry_bought_price.delete(0, tk.END)
        entry_sold_price.delete(0, tk.END)
        load_data()
    else:
        messagebox.showwarning("Input Error", "Please enter a valid item and expenses.")

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

    # Hide the 'id' column by default
    if "id" in columns:
        treeview.column("id", width=0, stretch=tk.NO)
        treeview.heading("id", text="", anchor=tk.W)

    data = database.view_data()
    for row in data:
        # Replace None values with empty strings
        row = ["" if value is None else value for value in row]
        
        # Set bought_price to empty string if it is 0
        bought_price_index = columns.index("bought_price")
        if row[bought_price_index] == 0:
            row[bought_price_index] = ""
        
        # Determine the tag based on the sold_price and bought_price
        sold_price = row[columns.index("sold_price")]
        expenses = row[columns.index("expenses")]

        profit = row[columns.index("profit")]
        tag = ""
        if sold_price == "":
            tag = "not_sold"
        elif profit > 0:
            tag = "profit"
        elif profit < 0:
            tag = "loss"

        if (expenses != "") & (sold_price == ""):
            tag = "loss"
        treeview.insert("", "end", values=row, tags=(tag,))


    calculate_days()
    color_total_profit()
    color_total_debt()

def delete_item():
    selected_item = treeview.selection()
    if not selected_item:
        messagebox.showwarning("No Item Selected", "Please select an item to delete.")
        return

    item_values = treeview.item(selected_item, "values")
    item_name = item_values[treeview["columns"].index("item_name")]  # Dynamically get the item_name column index
    print(f"Deleting item: {item_name}")  # Debugging information
    confirm = messagebox.askyesno("Delete Item", f"Are you sure you want to delete the item: {item_name}?")
    if confirm:
        item_id = database.get_item_id_from_db(item_name)
        print(f"Item ID: {item_id}")  # Debugging information
        if item_id:
            database.delete_item(item_id)
            load_data()
        else:
            messagebox.showwarning("Error", "Item not found in the database.")

def on_item_edit(event):
    item = treeview.focus()
    column = treeview.identify_column(event.x)
    
    if column in [f'#{i+1}' for i in range(len(treeview["columns"]))]:
        col_index = int(column[1:]) - 1
        old_value = treeview.item(item, "values")[col_index]
        new_value = simpledialog.askstring("Edit Value", f"Enter new value for {treeview.heading(column)['text']}:", initialvalue=old_value)

        if new_value is not None and new_value != old_value:
            item_values = treeview.item(item, "values")
            item_name = item_values[treeview["columns"].index("item_name")]  # Dynamically get the item_name column index
            print(f"Item values: {item_values}")  # Debugging information
            print(f"Editing item: {item_name}")  # Debugging information
            item_id = database.get_item_id_from_db(item_name)
            print(f"Item ID: {item_id}")  # Debugging information
            if item_id is not None:
                column_name = treeview.heading(column)['text'].lower().replace(" ", "_")
                database.update_item(item_id, column_name, new_value)
                load_data()
            else:
                print(f"Error: No item found with name {item_name}")

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

def calculate_days():
    data = database.view_data()
    for row in data:
        # Replace None values with empty strings
        row = ["" if value is None else value for value in row]
        
        # Check if the sold date is empty
        sold_date = row[database.get_column_names().index("sold_date")]
        bought_date = row[database.get_column_names().index("bought_date")]
        today = datetime.now().strftime('%Y-%m-%d')

        if sold_date == "":
            todays = datetime.now().strptime(today,'%Y-%m-%d')
            bought_date_obj = datetime.strptime(bought_date, '%Y-%m-%d')
            days_between = (todays - bought_date_obj).days
            
            # Update the cell with the calculated days
            row[database.get_column_names().index("days_between")] = days_between
            database.update_item(row[0], "days_between", days_between) 
        else:
            # Calculate the days between bought date and sold date
            bought_date_obj = datetime.strptime(bought_date, '%Y-%m-%d')
            sold_date_obj = datetime.strptime(sold_date, '%Y-%m-%d')
            days_between = (sold_date_obj - bought_date_obj).days
            
            # Update the cell with the calculated days
            row[database.get_column_names().index("days_between")] = days_between
            database.update_item(row[0], "days_between", days_between)  # Assuming the first column is the item ID


root = tk.Tk()
root.title("Resell Tracker")
root.geometry("800x600")

# Create a menu bar
menu_bar = tk.Menu(root)

# Create a "File" menu
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="Load Data", command=load_data)
file_menu.add_separator()
file_menu.add_command(label="Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

# Create a "Tools" menu
tools_menu = tk.Menu(menu_bar, tearoff=0)
tools_menu.add_command(label="Add Item", command=add_data)
tools_menu.add_command(label="Delete Item", command=delete_item)
tools_menu.add_command(label="Add Expenditure", command=add_expenditure)  # Add Expenditure option
menu_bar.add_cascade(label="Tools", menu=tools_menu)

# Add the menu bar to the root window
root.config(menu=menu_bar)




database.create_db()

frame_item_name = tk.Frame(root)
frame_item_name.pack(pady=5)

label_item_name = tk.Label(frame_item_name, text="Enter Item Name:")
label_item_name.pack(side=tk.LEFT, padx=5)

entry_item_name = tk.Entry(frame_item_name, width=50)
entry_item_name.pack(side=tk.LEFT, padx=5)

frame_bought_price = tk.Frame(root)
frame_bought_price.pack(pady=5)

label_bought_price = tk.Label(frame_bought_price, text="Enter Bought Price / Expenses:")
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

button_add_expenditure = tk.Button(frame_buttons, text="Add Expenditure", command=add_expenditure)  # Add Expenditure button
button_add_expenditure.pack(side=tk.LEFT, padx=10)

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
