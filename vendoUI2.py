import sys
import ctypes
import serial
import time
import wmi
import win32print
import tkinter as tk
import threading
import subprocess
import json
from tkinter import scrolledtext, simpledialog
from sendDataToFirebase2 import update_firebase
from firebase_admin import db  # Import Firebase Realtime Database

# Constants
BW_COST_PER_PAGE = 5  
PRINTER_NAME = "EPSON L4160 Series"
ESP32_PORT = "COM4"
PAPER_FEED_CAPACITY = 40  
LOW_PAPER_THRESHOLD = 5  
INK_CHECK_THRESHOLD = 3  
OWNER_PASSWORD = "admin123" 

# Global Variables
remaining_paper = PAPER_FEED_CAPACITY  
inserted_coins = 0  
total_cost = 0  
pages_printed = 0  
ser = None

# Check if script is running as Admin
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("🔴 Restarting with Admin privileges...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()

# Fetch paper count from Firebase on startup
def fetch_paper_from_firebase():
    global remaining_paper
    try:
        paper_data = db.reference("papers_remaining").get()
        if paper_data is not None:
            remaining_paper = int(paper_data)
            log_message(f"✅ Paper count synced from Firebase: {remaining_paper}")
        else:
            log_message("⚠️ No paper count data found in Firebase. Using default.")
    except Exception as e:
        log_message(f"❌ Error fetching paper count: {e}")

# UI Setup
root = tk.Tk()
root.title("VendoPrint V2.0")
root.geometry("530x270")
root.resizable(True, True)
root.attributes('-topmost', True)

# Log Box (Left Side)
log_box = scrolledtext.ScrolledText(root, width=60, height=6, state=tk.DISABLED)
log_box.grid(row=0, column=0, columnspan=3, padx=10, pady=5, sticky="w")

def log_message(message):
    """Logs messages in the UI and console."""
    log_box.config(state=tk.NORMAL)
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)
    log_box.config(state=tk.DISABLED)
    print(message)

# Function to Open Settings
def open_settings():
    global remaining_paper
    password = simpledialog.askstring("Admin Login", "Enter password:", show='*')
    if password == OWNER_PASSWORD:
        new_paper = simpledialog.askinteger("Update Paper", "Enter new paper count:", minvalue=1)
        if new_paper is not None:
            remaining_paper = new_paper
            update_paper_status()
            log_message(f"✅ Paper count updated to {remaining_paper}")
    else:
        log_message("❌ Incorrect password!")

# Settings Button
settings_button = tk.Button(root, text="⚙️ Settings", command=open_settings, font=("Arial", 10, "bold"), padx=10)
settings_button.grid(row=1, column=0, padx=10, pady=10, sticky="w")

# Status Labels (Right Side)
cost_label = tk.Label(root, text="Waiting for print job...", font=("Arial", 10))
cost_label.grid(row=1, column=2, padx=10, pady=5, sticky="e")

coin_label = tk.Label(root, text="Coins Inserted: ₱0", font=("Arial", 10))
coin_label.grid(row=2, column=2, padx=10, pady=5, sticky="e")

paper_status_label = tk.Label(root, text=f"📄 Paper Remaining: {remaining_paper}", fg="blue", font=("Arial", 10, "bold"))
paper_status_label.grid(row=3, column=2, padx=10, pady=5, sticky="e")

# # Paper Status
# paper_status_label = tk.Label(root, fg="blue")
# paper_status_label.grid(row=2, column=2, pady=10)


def update_paper_status():
    paper_status_label.config(text=f"📄 Paper Remaining: {remaining_paper}")
    update_firebase(inserted_coins, remaining_paper, {})
    db.reference("papers_remaining").set(remaining_paper)  # Sync with Firebase



# # Add settings button
# settings_button = tk.Button(root, text="⚙️ Settings", command=open_settings)
# settings_button.grid(row=1, column=1, padx=5, pady=5)


# Fetch initial paper count from Firebase
fetch_paper_from_firebase()
update_paper_status()

log_message("🚀 Printer Vendo System Starting...")
update_firebase(inserted_coins, remaining_paper, {})

# Function to clear print queue
def clear_print_queue():
    """Clears all pending print jobs for the specified printer."""
    log_message("🗑️ Clearing print queue...")
    try:
        printer_handle = win32print.OpenPrinter(PRINTER_NAME)
        jobs = win32print.EnumJobs(printer_handle, 0, -1, 1)
        for job in jobs:
            win32print.SetJob(printer_handle, job["JobId"], 0, None, win32print.JOB_CONTROL_CANCEL)
        win32print.ClosePrinter(printer_handle)
        log_message("✅ Print queue cleared successfully.")
    except Exception as e:
        log_message(f"❌ Error clearing print queue: {e}")

# Connect to ESP32
def connect_to_esp32():
    global ser
    try:
        ser = serial.Serial(ESP32_PORT, 115200, timeout=1)
        log_message(f"✅ ESP32 Connected on {ESP32_PORT}")

        # Wait for ESP32 to finish booting
        time.sleep(2)
        while ser.in_waiting > 0:
            log_message(f"⬅️ ESP32: {ser.readline().decode(errors='ignore').strip()}")

        # Startup sequence: REQUEST_COIN_DATA → Read Response → RESET
        ser.write(b"REQUEST_COIN_DATA\n")
        log_message("➡️ Sent to ESP32: REQUEST_COIN_DATA")
        time.sleep(0.5)
        if ser.in_waiting > 0:
            log_message(f"⬅️ ESP32: {ser.readline().decode(errors='ignore').strip()}")

        ser.write(b"RESET\n")
        log_message("➡️ Sent to ESP32: RESET")

    except serial.SerialException:
        ser = None
        log_message("❌ Error: Could not connect to ESP32. Retrying in 5s...")
        root.after(5000, connect_to_esp32)

connect_to_esp32()

# UI Components
# cost_label = tk.Label(root, text="Waiting for print job...")
# cost_label.grid(row=1, column=2, padx=5, pady=5)
# coin_label = tk.Label(root, text="Coins Inserted: ₱0")
# coin_label.grid(row=2, column=1, padx=5, pady=5) 
# paper_status_label = tk.Label(root, text=f"📄 Paper Remaining: {remaining_paper}", fg="blue")
# paper_status_label.pack(pady=10)

# def update_paper_status():
#     paper_status_label.config(text=f"📄 Paper Remaining: {remaining_paper}")

def set_printer_offline():
    c = wmi.WMI()
    for printer in c.Win32_Printer():
        if printer.Name == PRINTER_NAME:
            printer.WorkOffline = True
            printer.Put_()
            log_message(f"🚫 {PRINTER_NAME} is now OFFLINE.")

def set_printer_online():
    c = wmi.WMI()
    for printer in c.Win32_Printer():
        if printer.Name == PRINTER_NAME:
            printer.WorkOffline = False
            printer.Put_()
            log_message(f"✅ {PRINTER_NAME} is now ONLINE.")

def compute_cost():
    printer_handle = win32print.OpenPrinter(PRINTER_NAME)
    jobs = win32print.EnumJobs(printer_handle, 0, -1, 1)
    win32print.ClosePrinter(printer_handle)
    return sum(job.get('TotalPages', 0) for job in jobs) * BW_COST_PER_PAGE if jobs else 0

# Coin Detection Handling
def request_coin_data():
    """Enable coin insertion detection from ESP32."""
    if ser:
        ser.write(b"REQUEST_COIN_DATA\n")
        log_message("💰 Coin insertion enabled.")

def listen_for_coins_thread():
    """Continuously listens for coin insertions from ESP32 in a background thread."""
    global inserted_coins, total_cost
    while True:
        if ser and ser.in_waiting > 0:
            response = ser.readline().decode(errors='ignore').strip()
            log_message(f"⬅️ ESP32: {response}")
            try:
                response_data = json.loads(response)
                if "coin" in response_data:
                    inserted_coins += response_data["coin"]
                    root.after(0, update_ui)

                    if inserted_coins >= total_cost and total_cost > 0:
                        log_message("✅ Payment complete. Printing now...")
                        root.after(1000, set_printer_online)
                        root.after(1500, monitor_printing)
                        ser.write(b"RESET\n")

            except json.JSONDecodeError:
                log_message("⚠️ Invalid ESP32 response format.")

        time.sleep(0.2)

def update_ui():
    coin_label.config(text=f"Coins Inserted: ₱{inserted_coins}")

# Start coin listening in a separate thread
coin_thread = threading.Thread(target=listen_for_coins_thread, daemon=True)
coin_thread.start()

def monitor_printing():
    global remaining_paper, pages_printed

    time.sleep(2)
    pages_used = total_cost // BW_COST_PER_PAGE  
    pages_printed += pages_used
    remaining_paper -= max(pages_used, 0)

    log_message(f"✅ Printed {pages_used} pages. Cost: ₱{total_cost}. Paper left: {remaining_paper} sheets.")

    # Monitor ink levels every 10 pages
    if pages_printed >= INK_CHECK_THRESHOLD:
        pages_printed = 0
        check_ink_levels()

    update_firebase(inserted_coins, remaining_paper, {"pages": pages_used, "cost": total_cost})
    clear_print_queue()
    set_printer_offline()
    update_paper_status()
    root.after(1000, reset_transaction)

def check_ink_levels():
    log_message("🎨 Checking ink levels...")
    
    # Directly run inkleveltoPercent.py, skipping captureInkLevels.py
    result = subprocess.run(["python", "inkleveltoPercent.py"], capture_output=True, text=True)

    if result.returncode == 0:
        try:
            ink_levels = json.loads(result.stdout.strip())
            log_message(f"✅ Extracted Ink Levels: {ink_levels}")
            update_firebase(inserted_coins, remaining_paper, {}, ink_levels)
        except json.JSONDecodeError as e:
            log_message(f"❌ JSON Parsing Error: {e}")
    else:
        log_message(f"❌ inkleveltoPercent.py failed with error:\n{result.stderr}")

def reset_transaction():
    global inserted_coins, total_cost
    inserted_coins = 0  
    total_cost = 0  
    cost_label.config(text="Waiting for print job...")
    coin_label.config(text="Coins Inserted: ₱0")
    log_message("🔄 Ready for a new transaction.")
    set_printer_offline()

def main_loop():
    global total_cost
    total_cost = compute_cost()
    if total_cost > 0 and inserted_coins < total_cost:
        set_printer_offline()
        cost_label.config(text=f"Printing cost: ₱{total_cost}")
        log_message(f"Printing cost: ₱{total_cost}. Insert coins to continue.")
        request_coin_data()
    root.after(2000, main_loop)

log_message("🚀 Printer Vendo System Starting...")
clear_print_queue()
set_printer_offline()
root.after(2000, main_loop)
root.mainloop()