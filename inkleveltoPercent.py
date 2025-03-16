import cv2
import numpy as np
import json

# Define the sample images and their corresponding ink colors
samples = {
    "Black": "blackSample.png",
    "Yellow": "yellowSample.png",
    "Magenta": "magentaSample.png",
    "Cyan": "cyanSample.png",
}

target_path = "capture.png"
target = cv2.imread(target_path)

if target is None:
    print("❌ Error: Target image not found.")
    exit()

target_gray = cv2.cvtColor(target, cv2.COLOR_BGR2GRAY)

# Dictionary to store ink levels
ink_levels = {}

# Process each ink color
for color, sample_path in samples.items():
    sample = cv2.imread(sample_path, cv2.IMREAD_GRAYSCALE)

    if sample is None:
        print(f"⚠️ Warning: Sample image for {color} not found. Skipping...")
        continue

    # Match the sample within the target image
    result = cv2.matchTemplate(target_gray, sample, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    # Get bounding box coordinates
    x, y = max_loc
    h, w = sample.shape

    # Extract the detected ink bar region
    roi = target[y:y + h, x:x + w]

    # Convert ROI to HSV for color-based detection
    roi_hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Define HSV thresholds for detecting ink colors
    color_ranges = {
        "Black": [(0, 0, 0), (180, 255, 50)],  # Black color range
        "Yellow": [(20, 100, 100), (40, 255, 255)],  # Yellow range
        "Magenta": [(140, 100, 100), (170, 255, 255)],  # Magenta range
        "Cyan": [(80, 100, 100), (100, 255, 255)],  # Cyan range
    }

    lower, upper = np.array(color_ranges[color][0]), np.array(color_ranges[color][1])
    mask = cv2.inRange(roi_hsv, lower, upper)

    # Compute ink percentage
    filled_pixels = np.count_nonzero(mask)  # Count ink pixels
    total_pixels = roi.shape[0] * roi.shape[1]  # Total pixels in the detected bar
    ink_percentage = int((filled_pixels / total_pixels) * 100)  # Convert to percentage

    # Store ink percentage
    ink_levels[color] = min(100, max(0, ink_percentage))

# Print ink levels in proper JSON format
print(json.dumps(ink_levels))
