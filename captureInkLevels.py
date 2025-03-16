import pyautogui
import time
import os

def open_ink_levels():
    print("🔎 Opening 'Printers & Scanners' faster...")
    pyautogui.hotkey("win", "r")  # Run dialog
    time.sleep(0.5)
    pyautogui.write("ms-settings:printers")
    pyautogui.press("enter")
    time.sleep(2.5)  # Reduced wait time

    print("🖨️ Selecting 'EPSON L4160 Series'...")
    printer_button = locate_with_debug("epson_printer_button.png", confidence=0.8)
    if printer_button:
        pyautogui.click(printer_button)
    else:
        return
    time.sleep(3)

    print("⚙️ Opening 'Printing Preferences'...")
    preferences_button = locate_with_debug("printing_preferences_button.png", confidence=0.9)
    if preferences_button:
        pyautogui.click(preferences_button)
    else:
        return
    time.sleep(2)

    print("🎨 Clicking 'Ink Levels' button...")
    ink_levels_button = locate_with_debug("ink_levels_button.png", confidence=0.7)
    if ink_levels_button:
        pyautogui.click(ink_levels_button)
        print("✅ Ink Levels window opened successfully!")
        time.sleep(1.5)
        take_screenshot_of_window()
    else:
        return

def take_screenshot_of_window():
    print("📸 Capturing only the 'EPSON L4160 Series' window...")

    window_location = locate_with_debug("epson_window_title.png", confidence=0.85)

    if window_location:
        if len(window_location) == 4:
            x, y, width, height = map(int, window_location)
            print(f"✅ Window found at ({x}, {y}, {width}, {height})")

            screenshot = pyautogui.screenshot(region=(x, y, width, height))
            screenshot_path = os.path.join(os.getcwd(), "capture.png")
            screenshot.save(screenshot_path)
            print(f"✅ Screenshot saved as {screenshot_path}")
        else:
            print("⚠️ Unexpected output from locateOnScreen. Taking full-screen screenshot.")
            pyautogui.screenshot("capture.png")
    else:
        print("❌ Window not found. Taking full-screen screenshot.")
        pyautogui.screenshot("capture.png")

    close_windows()

def close_windows():
    print("❌ Closing all open windows...")
    for _ in range(3):
        pyautogui.hotkey("alt", "f4")
        time.sleep(0.5)  # Reduced wait time
    print("✅ All windows closed.")

def locate_with_debug(image_path, retries=2, confidence=0.9):
    """Tries to locate an image on screen faster with grayscale processing."""
    for attempt in range(retries):
        button = pyautogui.locateOnScreen(image_path, confidence=confidence, grayscale=True)
        if button:
            return button
        print(f"❌ Attempt {attempt+1}/{retries}: '{image_path}' not found.")
        time.sleep(3)

    debug_image = f"debug_{image_path}.png"
    pyautogui.screenshot(debug_image)
    print(f"📸 Debug screenshot saved as '{debug_image}'. Check UI image matching.")

    return None

# Run the function
open_ink_levels()
