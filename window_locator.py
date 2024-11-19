import cv2
import numpy as np
from PIL import ImageGrab, Image
import easyocr
import io
import winsound
import pyautogui
from typing import Tuple
import re


screen_width, screen_height = pyautogui.size()

PADDING = 15

overview = 'overview'
directional_scanner = 'directional'
selected_item = 'selected'
local = 'local'

window_names = [overview, directional_scanner, selected_item, local]


def beep():
    winsound.Beep(1400, 100)


# SCANNER_REGION = '[2780, 900, 659, 539]'
# CAPACITOR_REGION = '[1535, 1067, 510, 364]'
# OVERVIEW_REGION = '[2778, 133, 661, 761]'
# SELECTED_ITEM_REGION = '[2780, 2, 657, 126]'
# TOP_LEFT_REGION = '[50, 5, 825, 618]'
MID_TO_TOP_REGION = '[821, 0, 1467, 827]'
TARGETS_REGION = '[2245, 0, 528, 193]'
# LOCAL_REGION = '[49, 683, 597, 379]'

# Initialize EasyOCR Reader
reader = easyocr.Reader(['en'])

# Capture the screen

screenshot = np.array(ImageGrab.grab())

# Convert screenshot to grayscale
gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

# OCR to detect the window title using EasyOCR
ocr_results = reader.readtext(gray)


# Function to locate window by name in OCR results
def locate_window_by_name(ocr_results, window_name):
    for result in ocr_results:
        text = result[1]  # result[1] contains the recognized text
        if window_name.lower() in text.lower():
            return True, result[0]  # Return True and the bounding box of the matched text
    return False, None


def find_selected_item_region():
    selected_item_data = window_coords['selected']
    overview_data = window_coords['overview']
    selected_item_found = selected_item_data[0]
    overview_found = overview_data[0]
    print(selected_item_data, overview_data, selected_item_found, overview_found)
    if selected_item_found and overview_found:
        x = int(selected_item_data[1][0][0] - PADDING)
        y = int(0)
        region_width = int(screen_width - x)
        region_height = int(overview_data[1][0][1] - PADDING)
        return x, y, region_width, region_height
    return 0, 0, int(screen_width), int(screen_height)


def find_overview_region():
    overview_data = window_coords['overview']
    overview_found = overview_data[0]
    directional_scanner_data = window_coords['directional']
    directional_scanner_found = directional_scanner_data[0]
    if overview_found and directional_scanner_found:
        x = int(overview_data[1][0][0] - PADDING)
        y = int(overview_data[1][0][1])
        region_width = int(screen_width - x)
        region_height = int(directional_scanner_data[1][0][1] - y - PADDING)
        return x, y, region_width, region_height
    return 0, 0, int(screen_width), int(screen_height)


def find_directional_scanner_region():
    directional_scanner_data = window_coords['directional']
    directional_scanner_found = directional_scanner_data[0]
    if directional_scanner_found:
        x = int(directional_scanner_data[1][0][0] - PADDING)
        y = int(directional_scanner_data[1][0][1] - PADDING)
        region_width = int(screen_width - x)
        region_height = int(screen_height - y)
        return x, y, region_width, region_height
    return 0, 0, int(screen_width), int(screen_height)


def jpg_screenshot_of_the_selected_region(region: Tuple) -> Image:
    screenshot = pyautogui.screenshot(region=region)
    temp_image = io.BytesIO()
    screenshot.save(temp_image, format="JPEG")
    temp_image.seek(0)
    screenshot_jpeg = Image.open(temp_image)
    return screenshot_jpeg


def find_top_left_region():
    x = PADDING
    y = 0
    width = screen_width/2 - PADDING
    height = screen_height/2
    return x, y, width, height


def find_local_region(easyocr_output):
    """
    Args:
        easyocr_output: The result of EasyOCR, which is a list of tuples, where each tuple contains
                        the bounding box, the text, and the confidence (e.g., [([x1, y1, x2, y2], text, conf), ...]).

    Returns:
        The x-coordinate of the bounding box of the number that matches the number next to 'Local'
        and is found to the right and below it.
    """

    local_box = None
    number = None
    local_bottom_box = None

    # Step 1: Iterate through OCR output to find 'Local' and the number next to it
    for bbox, text, _ in easyocr_output:
        if 'Local' in text:
            local_box = bbox

            # Step 2: Search for the number between square brackets after 'Local'
            number_match = re.search(r'\[(\d+)\]', text)
            if number_match:
                number = number_match.group(1)
            break

    for bbox, text, _ in easyocr_output:
        if 'Corp' in text or 'Uncanny' in text:
            local_bottom_box = bbox

            break

    if not local_box or not number:
        return None

    # Step 3: Find the identical number that is to the right and below 'Local'
    for bbox, text, _ in easyocr_output:
        if text == number:
            # Compare the position of the bounding box to ensure it's to the right and below 'Local'
            if bbox[0] > local_box[2] and bbox[1] > local_box[3]:
                # Step 4: Return the x-coordinate of the left side of its bounding box
                if local_bottom_box is not None:
                    return int(local_box[0][0]), int(local_box[0][1]), int(bbox[0][0] - local_box[0][0]), \
                        int(local_bottom_box[0][1] - local_box[0][1])
                else:
                    return int(local_box[0][0]), int(local_box[0][1]), int(bbox[0][0] - local_box[0][0]), \
                        int(screen_height - local_box[0][1])

    return None


def find_capacitor_region(tolerance=40, scan_height=100):
    """
    Scan the bottom of the screen for pixels that match yellow hues using OpenCV and return the bounding box.

    Parameters:
    tolerance (int): Allowed color variation for yellow detection.
    scan_height (int): Height in pixels from the bottom to scan.

    Returns:
    tuple: (x, y, width, height) representing the bounding box around yellow pixels. Returns None if no pixels found.
    """

    # Capture the bottom part of the screen (last 'scan_height' rows)
    screenshot = pyautogui.screenshot(region=(0, screen_height - scan_height, screen_width, scan_height))

    # Convert screenshot to a numpy array (RGB format) and then to BGR for OpenCV
    img = np.array(screenshot)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Define a range for yellow in BGR
    lower_yellow = np.array([0, 200 - tolerance, 200 - tolerance], dtype=np.uint8)  # Lower bound of yellow in BGR
    upper_yellow = np.array([100 + tolerance, 255, 255], dtype=np.uint8)  # Upper bound of yellow in BGR

    # Create a mask where the pixels fall within the yellow range
    mask = cv2.inRange(img, lower_yellow, upper_yellow)

    # Find contours (group of connected pixels) from the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Find the largest contour and get the bounding rectangle
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        # Adjust y-coordinate to match the full screen height
        # return (x, screen_height - scan_height + y, w + int(screen_width/5), h + int(screen_height/6))
        padding_x = int(screen_width/50)
        padding_y = int(screen_height/10)

        y = screen_height - scan_height + y - padding_y
        return x-padding_x, y, int(screen_width/8), screen_height-y

    # Return None if no matching region was found
    return None


if __name__ == '__main__':
    # Example usage:
    yellow_region = find_capacitor_region()

    window_coords = {window_name: locate_window_by_name(ocr_results, window_name) for window_name in window_names}
    print(window_coords)

    print(yellow_region)

    # selected_item_region = find_selected_item_region()
    # overview_region = find_overview_region()
    # directional_scanner = find_directional_scanner_region()
    #
    # Capture screenshot
    screenshot_jpeg = jpg_screenshot_of_the_selected_region(yellow_region)

    # Display the screenshot
    screenshot_jpeg.show()
    beep()
