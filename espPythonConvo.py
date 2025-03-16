import serial
import tkinter as tk
from tkinter import scrolledtext
import time

# Configure ESP32 serial port (Update COM port as needed)
ESP32_PORT = "COM4"  # Change this based on your ESP32 port
BAUD_RATE = 115200

try:
    ser = serial.Serial(ESP32_PORT, BAUD_RATE, timeout=1)
    
    # Wait for ESP32 to finish booting
    time.sleep(2)  # Give ESP32 enough time to boot

    # Read boot messages from ESP32
    boot_messages = []
    while ser.in_waiting > 0:
        boot_messages.append(ser.readline().decode(errors='ignore').strip())

    # Log boot messages
    for msg in boot_messages:
        print(f"⬅️ ESP32: {msg}")

    # 1️⃣ Send "REQUEST_COIN_DATA" once after bootup
    ser.write(b"REQUEST_COIN_DATA\n")
    print("➡️ Sent to ESP32: REQUEST_COIN_DATA")
    time.sleep(0.5)  # Allow ESP32 time to process

    # 2️⃣ Read ESP32 response
    if ser.in_waiting > 0:
        response = ser.readline().decode(errors='ignore').strip()
        print(f"⬅️ ESP32: {response}")

    # 3️⃣ Send "RESET" to clear any previous coin states
    ser.write(b"RESET\n")
    print("➡️ Sent to ESP32: RESET")
    time.sleep(0.5)

except serial.SerialException:
    ser = None
    print("⚠️ Error: Could not connect to ESP32.")

# UI Setup
root = tk.Tk()
root.title("ESP32 Coin Logger")
root.geometry("500x400")

# Checkbox state
detect_coins = tk.BooleanVar(value=False)

# Log display
log_box = scrolledtext.ScrolledText(root, width=60, height=15, state=tk.DISABLED)
log_box.pack(pady=10)

def log_message(message):
    """Log messages in the UI and print to console."""
    log_box.config(state=tk.NORMAL)
    log_box.insert(tk.END, message + "\n")
    log_box.see(tk.END)
    log_box.config(state=tk.DISABLED)
    print(message)

def toggle_coin_detection():
    """Send appropriate command based on checkbox state."""
    if ser:
        command = "REQUEST_COIN_DATA\n" if detect_coins.get() else "RESET\n"
        ser.write(command.encode())
        log_message(f"➡️ Sent to ESP32: {command.strip()}")

def read_serial():
    """Read serial data from ESP32."""
    if ser and ser.in_waiting > 0:
        response = ser.readline().decode(errors='ignore').strip()
        if response:
            log_message(f"⬅️ ESP32: {response}")

    root.after(100, read_serial)  # Continuously check for data

# Log startup sequence
log_message("➡️ Sent to ESP32: REQUEST_COIN_DATA (After Boot)")
log_message("➡️ Sent to ESP32: RESET (After Boot)")

# Checkbox for enabling coin detection
checkbox = tk.Checkbutton(root, text="Enable Coin Detection", variable=detect_coins, command=toggle_coin_detection)
checkbox.pack(pady=5)

# Start reading serial data
root.after(100, read_serial)

# Run UI
root.mainloop()
