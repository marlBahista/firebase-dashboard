import sys
import ctypes
import serial
import time
import wmi
import win32print
import tkinter as tk
import threading
from sendDataToFirebase import update_firebase

# Constants
BW_COST_PER_PAGE = 5  
PRINTER_NAME = "EPSON L4160 Series"
ESP32_PORT = "COM4"
PAPER_FEED_CAPACITY = 18  
LOW_PAPER_THRESHOLD = 5  

# Global Variables
remaining_paper = PAPER_FEED_CAPACITY  
inserted_coins = 0  
total_cost = 0  

# Check if the script is running as Admin
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    print("🔴 Restarting with Admin privileges...")
    ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
    sys.exit()

# Initialize UI
root = tk.Tk()
root.title("Printer Vendo System")
root.geometry("400x500")

log_box = tk.Text(root, height=10, width=50)
log_box.pack(pady=10)

def log_message(message):
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)
    print(message)  # Keep console logs for debugging

# Connect to ESP32
try:
    ser = serial.Serial(ESP32_PORT, 115200, timeout=1)
    esp_status = f"✅ ESP32 Connected on {ESP32_PORT}"
except serial.SerialException:
    ser = None
    esp_status = "❌ Error: Could not connect to ESP32."

log_message(esp_status)

# UI Components
status_label = tk.Label(root, text=esp_status, fg="green")
status_label.pack(pady=10)
cost_label = tk.Label(root, text="Waiting for print job...")
cost_label.pack(pady=10)
coin_label = tk.Label(root, text="Coins Inserted: ₱0")
coin_label.pack(pady=10)
paper_status_label = tk.Label(root, text=f"📄 Paper Remaining: {remaining_paper}", fg="blue")
paper_status_label.pack(pady=10)

def update_paper_status():
    paper_status_label.config(text=f"📄 Paper Remaining: {remaining_paper}")

def clear_print_queue():
    log_message("🗑️ Clearing all remaining print jobs...")
    printer_handle = win32print.OpenPrinter(PRINTER_NAME)
    jobs = win32print.EnumJobs(printer_handle, 0, -1, 1)
    for job in jobs:
        try:
            win32print.SetJob(printer_handle, job["JobId"], 0, None, win32print.JOB_CONTROL_DELETE)
            log_message(f"🗑️ Deleted job {job['JobId']}.")
        except Exception as e:
            log_message(f"⚠️ Error deleting job {job['JobId']}: {e}")
    win32print.ClosePrinter(printer_handle)
    log_message("✅ Print queue cleared.")

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

def request_coin_data():
    if ser:
        ser.write(b"REQUEST_COIN_DATA\n")
        log_message("💰 Coin insertion enabled.")

def listen_for_coins():
    global inserted_coins, total_cost
    if not ser:
        log_message("❌ Error: ESP32 is not connected.")
        return
    while ser.in_waiting > 0:
        response = ser.readline().decode(errors='ignore').strip()
        log_message(f"ESP32 Response: {response}")
        if response.startswith("COIN VALUE: "):
            try:
                coin_amount = int(response.split(": ")[1]) 
                inserted_coins += coin_amount
                coin_label.config(text=f"Coins Inserted: ₱{inserted_coins}")
                if inserted_coins >= total_cost and total_cost > 0:
                    log_message("✅ Payment complete. Printing now...")
                    root.after(1000, set_printer_online)
                    root.after(1500, monitor_printing)
                    ser.write(b"RESET\n")
                    return  
            except ValueError:
                log_message("⚠️ Error reading coin value!")
    root.after(200, listen_for_coins)

def monitor_printing():
    global remaining_paper
    time.sleep(2)
    clear_print_queue()
    pages_used = total_cost // BW_COST_PER_PAGE  
    remaining_paper -= max(pages_used, 0)
    log_message(f"✅ Printed {pages_used} pages. Cost: ₱{total_cost}. Paper left: {remaining_paper} sheets.")
    update_firebase(inserted_coins, remaining_paper, {"pages": pages_used, "cost": total_cost})
    set_printer_offline()
    update_paper_status()
    root.after(1000, reset_transaction)

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
        root.after(500, listen_for_coins)
    root.after(2000, main_loop)

# Log startup messages
log_message("🚀 Printer Vendo System Starting...")
clear_print_queue()
set_printer_offline()
log_message("✅ System Ready!")

root.after(2000, main_loop)
root.mainloop()
