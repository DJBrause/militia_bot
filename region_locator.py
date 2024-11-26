import logging
import re
from typing import Any, Dict, Tuple

import cv2
import numpy as np
import pyautogui
from dotenv import set_key

import helper_functions as hf
from constants import (REGION_PADDING, TARGETS_REGION_HEIGHT_SCALE, FIND_CAPACITOR_REGION_SCAN_HEIGHT,
                       FIND_CAPACITOR_REGION_SCAN_TOLERANCE)

screen_width, screen_height = pyautogui.size()


OVERVIEW = 'overview'
DIRECTIONAL_SCANNER = 'directional'
SELECTED_ITEM = 'selected'
LOCAL = 'local'

window_names = [OVERVIEW, DIRECTIONAL_SCANNER, SELECTED_ITEM, LOCAL]


def locate_window_by_name(window_name: str) -> Tuple[bool, Any] | Tuple[bool, None]:
    screen_region = (0, 0, screen_width, screen_height)
    screenshot = hf.jpg_screenshot_of_the_selected_region(screen_region)
    ocr_results = hf.ocr_reader.readtext(screenshot)
    for result in ocr_results:
        text = result[1]  # result[1] contains the recognized text
        if window_name.lower() in text.lower():
            return True, result[0]
    return False, None


def find_selected_item_region(window_coords: Dict) -> Tuple:
    selected_item_data = window_coords['selected']
    overview_data = window_coords['overview']
    selected_item_found = selected_item_data[0]
    overview_found = overview_data[0]

    if selected_item_found and overview_found:
        x = int(selected_item_data[1][0][0] - REGION_PADDING)
        y = int(0)
        region_width = int(screen_width - x)
        region_height = int(overview_data[1][0][1] - REGION_PADDING)
        hf.jpg_screenshot_of_the_selected_region((x, y, region_width, region_height), debug=True)
        logging.info(f"'Selected item' region screenshot saved")
        return x, y, region_width, region_height
    return 0, 0, int(screen_width), int(screen_height)


def find_overview_region(window_coords: Dict) -> Tuple:
    overview_data = window_coords['overview']
    overview_found = overview_data[0]
    directional_scanner_data = window_coords['directional']
    directional_scanner_found = directional_scanner_data[0]
    if overview_found and directional_scanner_found:
        x = int(overview_data[1][0][0] - REGION_PADDING)
        y = int(overview_data[1][0][1])
        region_width = int(screen_width - x)
        region_height = int(directional_scanner_data[1][0][1] - y - REGION_PADDING)
        hf.jpg_screenshot_of_the_selected_region((x, y, region_width, region_height), debug=True)
        logging.info(f"'Overview' region screenshot saved")
        return x, y, region_width, region_height
    return 0, 0, int(screen_width), int(screen_height)


def find_directional_scanner_region(window_coords: Dict) -> Tuple:
    directional_scanner_data = window_coords['directional']
    directional_scanner_found = directional_scanner_data[0]
    if directional_scanner_found:
        x = int(directional_scanner_data[1][0][0] - REGION_PADDING)
        y = int(directional_scanner_data[1][0][1] - REGION_PADDING)
        region_width = int(screen_width - x)
        region_height = int(screen_height - y)
        hf.jpg_screenshot_of_the_selected_region((x, y, region_width, region_height), debug=True)
        logging.info(f"'Directional Scanner' region screenshot saved")
        return x, y, region_width, region_height
    return 0, 0, int(screen_width), int(screen_height)


def find_top_left_region() -> Tuple:
    x = REGION_PADDING
    y = 0
    region_width = int(screen_width / 2 - REGION_PADDING)
    region_height = int(screen_height/2)
    region = x, y, region_width, region_height
    hf.jpg_screenshot_of_the_selected_region((x, y, region_width, region_height), debug=True)
    logging.info(f"'Top Left' region screenshot saved")
    return region


def find_local_region() -> Tuple | None:
    """
    Returns:
        The x-coordinate of the bounding box of the number that matches the number next to 'Local'
        and is found to the right and below it.
    """
    screen_region = (0, 0, screen_width, screen_height)
    screenshot = hf.jpg_screenshot_of_the_selected_region(screen_region, debug=True)
    ocr_results = hf.ocr_reader.readtext(screenshot)
    local_box = None
    number = None
    local_bottom_box = None

    # Step 1: Iterate through OCR output to find 'Local' and the number next to it
    for bbox, text, _ in ocr_results:
        if 'Local' in text:
            local_box = bbox

            # Step 2: Search for the number between square brackets after 'Local'
            number_match = re.search(r'\[(\d+)]', text)
            if number_match:
                number = number_match.group(1)
            break

    for bbox, text, _ in ocr_results:
        if 'Corp' in text or 'Uncanny' in text:
            local_bottom_box = bbox

            break

    if not local_box or not number:
        return None

    # Step 3: Find the identical number that is to the right and below 'Local'
    for bbox, text, _ in ocr_results:
        if text == number:
            # Compare the position of the bounding box to ensure it's to the right and below 'Local'
            if bbox[0] > local_box[2] and bbox[1] > local_box[3]:
                # Step 4: Return the x-coordinate of the left side of its bounding box
                if local_bottom_box is not None:
                    region = int(local_box[0][0]), int(local_box[0][1]), int(bbox[0][0] - local_box[0][0]), \
                        int(local_bottom_box[0][1] - local_box[0][1])
                    hf.jpg_screenshot_of_the_selected_region(region, debug=True)
                    logging.info(f"'Local' region screenshot saved")
                    return region
                else:
                    region = int(local_box[0][0]), int(local_box[0][1]), int(bbox[0][0] - local_box[0][0]), \
                        int(screen_height - local_box[0][1])
                    hf.jpg_screenshot_of_the_selected_region(region, debug=True)
                    logging.info(f"'Local' region screenshot saved")
                    return region

    return None


def find_capacitor_region() -> Tuple | None:
    """
    Scan the bottom of the screen for pixels that match yellow hues using OpenCV and return the bounding box.

    FIND_CAPACITOR_REGION_SCAN_TOLERANCE (int): Allowed color variation for yellow detection.
    FIND_CAPACITOR_REGION_SCAN_HEIGHT (int): Height in pixels from the bottom to scan.
    """

    if not hf.generic_variables.graphics_removed:
        hf.remove_graphics()
        hf.generic_variables.graphics_removed = True

    # Capture the bottom part of the screen (last 'scan_height' rows)
    screenshot = pyautogui.screenshot(region=(0, screen_height - FIND_CAPACITOR_REGION_SCAN_HEIGHT, screen_width,
                                              FIND_CAPACITOR_REGION_SCAN_HEIGHT))

    if hf.generic_variables.graphics_removed:
        hf.remove_graphics()
        hf.generic_variables.graphics_removed = False

    # Convert screenshot to a numpy array (RGB format) and then to BGR for OpenCV
    img = np.array(screenshot)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Define a range for yellow in BGR
    lower_yellow_bound = np.array([0, 200 - FIND_CAPACITOR_REGION_SCAN_TOLERANCE,
                                   200 - FIND_CAPACITOR_REGION_SCAN_TOLERANCE], dtype=np.uint8)
    upper_yellow_bound = np.array([100 + FIND_CAPACITOR_REGION_SCAN_TOLERANCE, 255, 255], dtype=np.uint8)

    # Create a mask where the pixels fall within the yellow range
    mask = cv2.inRange(img, lower_yellow_bound, upper_yellow_bound)

    # Find contours (group of connected pixels) from the mask
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        # Find the largest contour and get the bounding rectangle
        largest_contour = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(largest_contour)

        padding_x = int(screen_width/50)
        padding_y = int(screen_height/10)

        y = screen_height - FIND_CAPACITOR_REGION_SCAN_HEIGHT + y - padding_y
        region = x - padding_x, y, int(screen_width / 8), screen_height - y
        hf.jpg_screenshot_of_the_selected_region(region, debug=True)
        logging.info(f"'Capacitor' region screenshot saved")
        return region

    return None


# This has to be run after find_local_region() and find_overview_region() and takes their output as input
def find_mid_to_top_region(local_region_coords: Tuple, overview_region_coords: Tuple) -> Tuple:
    region_left_edge = local_region_coords[0] + local_region_coords[2]
    region_width = screen_width - (screen_width - overview_region_coords[0]) - region_left_edge
    region_height = int(screen_height / 2)
    region = (region_left_edge, 0, region_width, region_height)
    hf.jpg_screenshot_of_the_selected_region(region, debug=True)
    logging.info(f"'Top Mid' region screenshot saved")
    return region


# This has to be run after find_overview_region() and takes their output as input
def find_targets_region(overview_region_coords: Tuple) -> Tuple:
    region_left_edge = int(screen_width/2)
    region_width = int(screen_width - (screen_width - overview_region_coords[0]) - region_left_edge)
    region_height = int(overview_region_coords[1] * TARGETS_REGION_HEIGHT_SCALE)
    region = region_left_edge, 0, region_width, region_height
    hf.jpg_screenshot_of_the_selected_region(region, debug=True)
    logging.info(f"'Targets' region screenshot saved")
    return region


def locate_all_regions():
    env_file = '.env'

    window_coords = {window_name: locate_window_by_name(window_name) for window_name in window_names}
    selected_item_region = find_selected_item_region(window_coords)
    overview_region = find_overview_region(window_coords)
    directional_scanner_region = find_directional_scanner_region(window_coords)
    local_region = find_local_region()
    mid_to_top_region = find_mid_to_top_region(local_region, overview_region)
    targets_region = find_targets_region(overview_region)
    top_left_region = find_top_left_region()
    capacitor_region = find_capacitor_region()

    # Save regions to .env file
    set_key(env_file, 'SCANNER_REGION', str(directional_scanner_region))
    set_key(env_file, 'OVERVIEW_REGION', str(overview_region))
    set_key(env_file, 'SELECTED_ITEM_REGION', str(selected_item_region))
    set_key(env_file, 'LOCAL_REGION', str(local_region))
    set_key(env_file, 'MID_TO_TOP_REGION', str(mid_to_top_region))
    set_key(env_file, 'TARGETS_REGION', str(targets_region))
    set_key(env_file, 'TOP_LEFT_REGION', str(top_left_region))
    set_key(env_file, 'CAPACITOR_REGION', str(capacitor_region))
