import cv2
import keyboard
import logging
import numpy as np
import pyautogui
from easyocr import Reader
import winsound
from requests import get as api_get

from collections import defaultdict
from dataclasses import dataclass, field
import io
from PIL import Image
import re
import time
from typing import List, Tuple, Union, Any

from constants import (
    SCANNER_REGION, MORE_ICON, GUNS_BUTTON_COORDS, LOCAL_REGION, SCRAMBLER_EQUIPPED, SCRAM, PC_SPECIFIC_CONFIDENCE,
    OVERVIEW_REGION, WEBIFIER_EQUIPPED, WEB, COORDS_AWAY_FROM_OVERVIEW, ALL_DESTROYERS, ALL_FRIGATES,
    MAX_PIXEL_SPREAD, LOCK_TARGET_ICON, SELECTED_ITEM_REGION, MAX_NUMBER_OF_ATTEMPTS, CAPACITOR_REGION,
    SCRAMBLER_BUTTON, WEBIFIER_BUTTON, PROP_MOD_BUTTON, REPAIRER_BUTTON, REPAIRER_BUTTON_COORDS, MASK_LOWER_BAND,
    MASK_UPPER_BAND, MAX_MODULE_ACTIVATION_CHECK_ATTEMPTS, LOWER_COLOR_THRESHOLD, UPPER_COLOR_THRESHOLD,
    AMARR_FACTION_ID, MINMATAR_FACTION_ID, MINMATAR_AMARR_FW_SYSTEMS
)

import scanning_and_information_gathering as sig

ocr_reader = Reader(['en'], gpu=True)

FW_SYSTEMS_URL = 'https://esi.evetech.net/latest/fw/systems/?datasource=tranquility'


@dataclass
class GenericVariables:
    unvisited_systems: list = field(default_factory=list)
    short_scan: bool = None
    dscan_confidence: float = 0.65
    destination: str = ''
    is_repairing: bool = False
    guns_activated: bool = False
    prop_module_on: bool = False
    graphics_removed: bool = False
    initial_scan: bool = True
    approaching_capture_point: bool = False


generic_variables = GenericVariables()


@dataclass
class ButtonDetectionConfig:
    initial_button_pixel_sums: defaultdict[dict] = field(default_factory=lambda: defaultdict(dict))
    buttons_coordinates: defaultdict[dict] = field(default_factory=lambda: defaultdict(dict))


button_detection_config = ButtonDetectionConfig()
button_detection_config.buttons_coordinates = {'SCRAMBLER_BUTTON': None, 'WEBIFIER_BUTTON': None,
                                               'PROP_MOD_BUTTON': None, 'REPAIRER_BUTTON': None,
                                               'GUNS_BUTTON_COORDS': GUNS_BUTTON_COORDS}


def bounding_box_center_coordinates(bounding_box: List, region: Tuple) -> [int, int]:
    x_min = bounding_box[0][0]
    y_min = bounding_box[0][1]
    x_max = bounding_box[1][0]
    y_max = bounding_box[2][1]
    region_x = region[0]
    region_y = region[1]
    x_center = (x_min + x_max) / 2 + region_x
    y_center = (y_min + y_max) / 2 + region_y
    return x_center, y_center


def beep_x_times(x: int) -> None:
    for _ in range(x):
        winsound.Beep(frequency=1500, duration=100)
        time.sleep(0.1)


def clear_broadcast_history() -> None:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    search_for_string_in_region('clear', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def clear_local_chat_content() -> bool:
    try:
        more_icon = pyautogui.locateCenterOnScreen(MORE_ICON,
                                                   grayscale=False,
                                                   confidence=PC_SPECIFIC_CONFIDENCE,
                                                   region=LOCAL_REGION)
        if more_icon:
            pyautogui.moveTo(more_icon)
            pyautogui.click()
            time.sleep(0.2)
            screenshot = jpg_screenshot_of_the_selected_region(LOCAL_REGION)
            if search_for_string_in_region('clear', LOCAL_REGION, screenshot, move_mouse_to_string=True):
                pyautogui.click()
                return True
        return False
    except pyautogui.ImageNotFoundException:
        logging.error("Could not find MORE_ICON")
        return False


def extract_pilot_names_and_ship_types_from_screenshot() -> List[Tuple[str, Any]]:
    # Takes a screenshot of the overview region and returns a list of tuples containing the pilot's name and
    # the type of ship they are flying along with ship type's bounding box coordinates.
    try:
        screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
        output = ocr_reader.readtext(screenshot)
        sorted_output = sorted(output, key=lambda x: x[0][1][1])
        name_column_x_coordinate = [entry[0][0][0] for entry in sorted_output if entry[1] == 'Name'][0]
        logging.debug(f"sorted_output = {sorted_output}")
        name_and_ship_type_pair = [(clean_up_spaces(name[1]), ship_type[:2]) for ship_type in sorted_output
                                   if clean_up_spaces(ship_type[1]) in ALL_FRIGATES + ALL_DESTROYERS
                                   for name in sorted_output if name_column_x_coordinate - MAX_PIXEL_SPREAD
                                   <= name[0][0][0] <= name_column_x_coordinate + MAX_PIXEL_SPREAD and
                                   ship_type[0][0][1] - MAX_PIXEL_SPREAD <= name[0][0][1] <=
                                   ship_type[0][0][1] + MAX_PIXEL_SPREAD]
        return name_and_ship_type_pair
    except IndexError:
        logging.error("Index error in extract_pilot_names_and_ship_types_from_screenshot. "
                      "Attempting to fix the issue by switching tabs.")
        select_gates_only_tab()
        time.sleep(0.1)
        select_fw_tab()


def clean_up_spaces(input_string: str) -> str:
    # Replaces multiple consecutive spaces with a single space.
    cleaned_string = re.sub(r'\s+', ' ', input_string.strip())
    return cleaned_string


def get_and_return_system_name(region: Tuple) -> list:
    screenshot_of_top_left_corner = jpg_screenshot_of_the_selected_region(region)
    results = ocr_reader.readtext(screenshot_of_top_left_corner)
    return results


def get_module_buttons_coordinates() -> None:
    button_paths = {'SCRAMBLER_BUTTON': SCRAMBLER_BUTTON, 'WEBIFIER_BUTTON': WEBIFIER_BUTTON,
                    'PROP_MOD_BUTTON': PROP_MOD_BUTTON, 'REPAIRER_BUTTON': REPAIRER_BUTTON}
    for k, v in button_detection_config.buttons_coordinates.items():
        if v is None:
            try:
                x, y, w, h = pyautogui.locateOnScreen(button_paths[k],
                                                      grayscale=False,
                                                      confidence=PC_SPECIFIC_CONFIDENCE,
                                                      region=CAPACITOR_REGION)
                region_tuple = (x, y, w, h)
                region_tuple = tuple(int(parameter) for parameter in region_tuple)
                button_detection_config.buttons_coordinates[k] = region_tuple
            except pyautogui.ImageNotFoundException:
                if k == 'REPAIRER_BUTTON':
                    logging.warning(f"Could not find image related to {k}. Using hard coded coordinates instead.")
                    button_detection_config.buttons_coordinates[k] = REPAIRER_BUTTON_COORDS
                else:
                    logging.error(f"Error in get_module_buttons_coordinates. Could not find image related to {k}")


def get_initial_button_pixel_sum(region: Tuple) -> int:
    # Sets initial pixel sums of module button. This should be done when they are off.
    screenshot = jpg_screenshot_of_the_selected_region(region)
    hsv_screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_screenshot, lowerb=MASK_LOWER_BAND, upperb=MASK_UPPER_BAND)
    initial_pixel_sum = int(np.sum(mask))
    return initial_pixel_sum


def initialize_button_pixel_sums() -> None:
    for button, region in button_detection_config.buttons_coordinates.items():
        if region is not None:
            initial_pixel_sum = get_initial_button_pixel_sum(region)
            button_detection_config.initial_button_pixel_sums[button] = initial_pixel_sum


def is_module_active(key: str, region_tuple: tuple) -> bool:
    logging.debug(f"{key, region_tuple}")
    for _ in range(MAX_MODULE_ACTIVATION_CHECK_ATTEMPTS):
        try:
            screenshot = jpg_screenshot_of_the_selected_region(region_tuple)
            hsv_screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv_screenshot, lowerb=LOWER_COLOR_THRESHOLD, upperb=UPPER_COLOR_THRESHOLD)
            initial_pixel_sum = button_detection_config.initial_button_pixel_sums[key]
            pixel_sum_in_mask = np.sum(mask)
            logging.debug(f"initial_pixel_sum = {initial_pixel_sum}, pixel_sum_in_mask = {pixel_sum_in_mask}")
            if pixel_sum_in_mask > initial_pixel_sum*1.1:
                return True
        except Exception as e:
            logging.error(f"Error occurred in is_module_active function: {e}")
    return False


def prepare_module_buttons_coordinates_and_initial_pixel_sums() -> None:
    logging.info("Obtaining module buttons regions and setting initial pixel sums.")
    remove_graphics()
    get_module_buttons_coordinates()
    initialize_button_pixel_sums()
    logging.debug(f"initial_button_pixel_sums = {button_detection_config.initial_button_pixel_sums.items()}")
    remove_graphics()


def jpg_screenshot_of_the_selected_region(region: Tuple) -> Image:
    screenshot = pyautogui.screenshot(region=region)
    temp_image = io.BytesIO()
    screenshot.save(temp_image, format="JPEG")
    temp_image.seek(0)
    screenshot_jpeg = Image.open(temp_image)
    return screenshot_jpeg


def move_mouse_away_from_overview(coords: list = COORDS_AWAY_FROM_OVERVIEW) -> None:
    pyautogui.moveTo(coords)


def notification_beep() -> None:
    winsound.Beep(frequency=2000, duration=100)
    winsound.Beep(frequency=3000, duration=100)
    winsound.Beep(frequency=2000, duration=100)


def open_or_close_mail() -> None:
    with pyautogui.hold('alt'):
        pyautogui.press('i')


def open_or_close_notepad() -> None:
    pyautogui.hotkey('ctrl', 'n', interval=0.1)


def region_selector():
    beep_x_times(1)
    x, y = 0, 0
    while True:
        if keyboard.is_pressed('ctrl'):
            x, y = pyautogui.position()
            z = pyautogui.pixel(x, y)
            print(f"{x, y, z}")
            beep_x_times(1)

        if keyboard.is_pressed('alt'):
            x_, y_ = pyautogui.position()
            print(f"{x}, {y}, {x_ - x}, {y_ - y}")
            beep_x_times(3)

        if keyboard.is_pressed('`'):
            x, y = pyautogui.position()
            print(f"x: {x}, y: {y}")
            beep_x_times(1)
            time.sleep(1)

        if keyboard.is_pressed('end'):
            x, y = pyautogui.position()
            color = pyautogui.pixel(x, y)
            print(f"x: {x}, y: {y}, color: {color}")
            if color[0] >= color[1] + color[2]:
                print("red")
                beep_x_times(2)

            time.sleep(1)

        if keyboard.is_pressed('shift'):
            beep_x_times(2)
            break


def search_for_string_in_region(searched_string: str, region: Tuple, image_file: Image,
                                move_mouse_to_string: bool = False, selected_result: int = 0, debug: bool = False) \
        -> Union[bool, list]:
    results = ocr_reader.readtext(image_file)
    if debug:
        logging.debug(f"{results}")
    try:
        matching_results = []
        for result in results:
            if searched_string.lower() in result[1].lower():
                matching_results.append(result)
        middle_of_bounding_box = bounding_box_center_coordinates(matching_results[selected_result][0],
                                                                 region=region)
        if move_mouse_to_string:
            pyautogui.moveTo(middle_of_bounding_box)
        return middle_of_bounding_box
    except TypeError:
        return False
    except IndexError:
        return False


def select_broadcasts() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if search_for_string_in_region('cast', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        return True
    else:
        return False


def select_fleet_tab() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if search_for_string_in_region('eet', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        return True
    return False


def select_fw_tab() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if search_for_string_in_region('fw', OVERVIEW_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        move_mouse_away_from_overview()
        return True
    return False


def select_stations_and_beacons_tab() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if search_for_string_in_region('stations', OVERVIEW_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        move_mouse_away_from_overview()
        return True
    return False


def select_gates_only_tab() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if search_for_string_in_region('gates', OVERVIEW_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        move_mouse_away_from_overview()
        return True
    return False


def set_correct_confidence(image):
    for min_confidence_level in range(100, -1, -1):
        try:
            x, y = pyautogui.locateCenterOnScreen(image,
                                                  grayscale=False,
                                                  confidence=min_confidence_level / 100,
                                                  region=SELECTED_ITEM_REGION)
            pyautogui.moveTo(x, y)

            return min_confidence_level
        except pyautogui.ImageNotFoundException:
            pass
    return None


def reload_ammo() -> None:
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'r', interval=0.1)


def remove_graphics() -> None:
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'shift', 'f9', interval=0.1)


def tackle_enemy_ship(initial_run: bool = False) -> None:
    if initial_run:
        if SCRAMBLER_EQUIPPED is True:
            pyautogui.press(SCRAM)
        if WEBIFIER_EQUIPPED is True:
            pyautogui.press(WEB)
    else:
        if SCRAMBLER_EQUIPPED is True and not sig.check_if_scrambler_is_operating():
            pyautogui.press(SCRAM)
        if WEBIFIER_EQUIPPED is True and not sig.check_if_webifier_is_operating():
            pyautogui.press(WEB)


def target_lock_using_overview(target_name: str) -> bool:
    logging.info("Attempting to lock target using overview.")
    with pyautogui.hold('ctrl'):
        pyautogui.click()
        move_mouse_away_from_overview()
    for attempt in range(MAX_NUMBER_OF_ATTEMPTS):
        logging.info(f"Checking if lock is complete. Current attempt: {attempt + 1}")
        if sig.check_if_target_is_locked():
            return True
        screenshot = jpg_screenshot_of_the_selected_region(SELECTED_ITEM_REGION)
        if not search_for_string_in_region(target_name, SELECTED_ITEM_REGION, screenshot):
            logging.info("Target is no longer present in selected item window.")
            return False
    logging.info(f"Could not lock the target after {MAX_NUMBER_OF_ATTEMPTS} attempts.")
    return False


def target_lock_using_selected_item(target_name: str) -> bool:
    logging.info("Attempting to lock target using Selected Item window.")
    try:
        if not sig.check_if_target_is_locked():
            x_, y_ = pyautogui.locateCenterOnScreen(LOCK_TARGET_ICON,
                                                    confidence=PC_SPECIFIC_CONFIDENCE,
                                                    region=SELECTED_ITEM_REGION)
            time.sleep(0.1)
            pyautogui.moveTo(x_, y_)
            time.sleep(0.1)
            pyautogui.click()
            time.sleep(0.1)
            move_mouse_away_from_overview()
            for attempt in range(MAX_NUMBER_OF_ATTEMPTS):
                logging.info(f"Checking if lock is complete. Current attempt: {attempt+1}")
                if sig.check_if_target_is_locked():
                    return True
                screenshot = jpg_screenshot_of_the_selected_region(SELECTED_ITEM_REGION)
                if not search_for_string_in_region(target_name, SELECTED_ITEM_REGION, screenshot):
                    logging.info("Target is no longer present in selected item window.")
                    return False
            logging.info(f"Could not lock the target after {MAX_NUMBER_OF_ATTEMPTS} attempts.")
            return False
    except pyautogui.ImageNotFoundException:
        logging.error("Image related to target_lock_using_selected_item function not found.")
        return False


def convert_nine_to_percent(input_string: str) -> str:
    if input_string[-1] == '9':
        return input_string[:-1] + '%'
    return input_string


def launch_drones() -> None:
    time.sleep(0.1)
    pyautogui.hotkey('shift', 'f', interval=0.1)


def order_drones_to_engage() -> None:
    time.sleep(0.1)
    pyautogui.press('f')


def return_drones_to_bay() -> None:
    time.sleep(0.1)
    pyautogui.hotkey('shift', 'r', interval=0.1)


def turn_recording_on_or_off() -> None:
    time.sleep(0.1)
    pyautogui.hotkey('alt', 'f9', interval=0.1)


def unlock_target() -> None:
    time.sleep(0.1)
    pyautogui.hotkey('ctrl', 'shift', interval=0.1)


def get_amarr_systems():
    amarr_controlled_fw_systems = []
    fw_systems = api_get(FW_SYSTEMS_URL).json()
    for system in fw_systems:
        if system['owner_faction_id'] == AMARR_FACTION_ID:
            amarr_controlled_fw_systems.append(get_system_name_based_on_system_id(system['solar_system_id']))
    return amarr_controlled_fw_systems


def get_minmatar_systems():
    minmatar_controlled_fw_systems = []
    fw_systems = api_get(FW_SYSTEMS_URL).json()
    for system in fw_systems:
        if system['owner_faction_id'] == MINMATAR_FACTION_ID:
            minmatar_controlled_fw_systems.append(get_system_name_based_on_system_id(system['solar_system_id']))
    return minmatar_controlled_fw_systems


def get_system_name_based_on_system_id(system_id):
    for system in MINMATAR_AMARR_FW_SYSTEMS:
        if system[1] == system_id:
            return system[0]
