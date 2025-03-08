import tkinter as tk
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import matplotlib
from datetime import datetime
import matplotlib.dates as mdates  # Import matplotlib.dates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def get_days_and_price():
    conn = sqlite3.connect('resell_tracker.db')
    cursor = conn.execute("SELECT days_between, bought_price FROM items ORDER BY bought_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1]) for row in rows]

def get_date():
    conn = sqlite3.connect('resell_tracker.db')
    cursor = conn.execute("SELECT bought_date FROM items ORDER BY bought_date ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_profit():
    conn = sqlite3.connect('resell_tracker.db')
    cursor = conn.execute("SELECT profit FROM items ORDER BY bought_date ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row[0] for row in rows]

def get_profit_and_price():
    conn = sqlite3.connect('resell_tracker.db')
    cursor = conn.execute("SELECT bought_price, profit FROM items ORDER BY bought_date ASC")
    rows = cursor.fetchall()
    conn.close()
    return [(row[0], row[1]) for row in rows]

dates = get_date()
profit = get_profit()
days = get_days_and_price()
dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]  
price_vs_profit = get_profit_and_price()

def running_sum(nums):
    result = []
    current_sum = 0
    for num in nums:
        current_sum += num
        result.append(current_sum)
    return result

def debug():
    for date in dates:
        print(date)

    for prof in profit:
        print(prof)
    
    running_profit = running_sum(profit)

    for prof in running_profit:
        print(prof)

    for prof in days:
        print(prof)
    
    for date in dates:
        print(date)
    
    for price in price_vs_profit:
        print(price)

# This plots the relation of time to profit
def graph_profit_time(parent_frame):
    dates = get_date()
    profit = get_profit()
    # this prob needs to be fixed at some point so that they are 
    dates = [datetime.strptime(date, '%Y-%m-%d') for date in dates]  

    running_profit = running_sum(profit)

    figure = plt.Figure(figsize=(10, 5), dpi=100)

    scatter = FigureCanvasTkAgg(figure, parent_frame)
    scatter.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    ax1 = figure.add_subplot(111)
    ax1.plot(dates, running_profit, marker='o', linestyle='-')

    txt="This shows your total profit over time."
    figure.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2)  # Add padding around the graph
    ax1.text(0.5, -0.2, txt, wrap=True, ha='center', fontsize=10, transform=ax1.transAxes)


    ax1.set_xlabel('Date')
    ax1.set_ylabel('Profit')

    ax1.set_title('Total Profit Over Time')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))

def graph_time_vs_price(parent_frame):
    TimeVsProfit = get_days_and_price()

    figure = plt.Figure(figsize=(10, 5), dpi=100)

    scatter = FigureCanvasTkAgg(figure, parent_frame)
    scatter.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    ax1 = figure.add_subplot(111)
    ax1.plot([x[0] for x in TimeVsProfit], [x[1] for x in TimeVsProfit], marker='o', linestyle='-')

    txt="This shows the relation between the how much the item cost and how long it took to sell."
    figure.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2)  # Add padding around the graph
    ax1.text(0.5, -0.2, txt, wrap=True, ha='center', fontsize=10, transform=ax1.transAxes)


    ax1.set_xlabel('Days Unsold')
    ax1.set_ylabel('Price')

    ax1.set_title('Price vs Days Unsold')

def graph_price_profit(parent_frame):
    

    price_profit = get_profit_and_price()

    figure = plt.Figure(figsize=(10, 5), dpi=100)

    scatter = FigureCanvasTkAgg(figure, parent_frame)
    scatter.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    ax1 = figure.add_subplot()
    ax1.scatter([x[0] for x in price_profit], [x[1] for x in price_profit], marker='o', linestyle='-')

    txt="This shows the relation between the bought price and the profit."
    figure.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.2)  # Add padding around the graph
    ax1.text(0.5, -0.2, txt, wrap=True, ha='center', fontsize=10, transform=ax1.transAxes)

    ax1.set_xlabel('Bought Price')
    ax1.set_ylabel('Profit')

    ax1.set_title('Bought Price vs Profit')


# Create a simple Tkinter window to test the graph
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Graph Test")

    frame = tk.Frame(root)
    frame.pack(fill=tk.BOTH, expand=True)
    debug()
    graph_price_profit(frame)
    # Uncomment the line below to test the other graph
    # graph_time_vs_price(frame)

    root.mainloop()