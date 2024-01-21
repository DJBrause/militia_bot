import time
import keyboard
import winsound
import logging
import pyautogui
import io
from PIL import Image
from typing import List, Tuple, Union
from easyocr import Reader

from constants import (
    SCANNER_REGION, MORE_ICON, DEFAULT_CONFIDENCE, LOCAL_REGION, SCRAMBLER_EQUIPPED, SCRAM,
    OVERVIEW_REGION, WEBIFIER_EQUIPPED, WEB, COORDS_AWAY_FROM_OVERVIEW
)

import scanning_and_information_gathering as sig

ocr_reader = Reader(['en'], gpu=True)


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
                                                   confidence=DEFAULT_CONFIDENCE,
                                                   region=LOCAL_REGION)
        if more_icon:
            pyautogui.moveTo(more_icon)
            pyautogui.click()
            time.sleep(0.2)
            screenshot = jpg_screenshot_of_the_selected_region(LOCAL_REGION)
            search_for_string_in_region('clear', LOCAL_REGION, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            return True
        return False
    except pyautogui.ImageNotFoundException:
        return False


def check_if_correct_broadcast_was_sent(broadcast_keyword: str) -> bool:
    logging.info(f"Checking if broadcast keyword is present in broadcasts: {broadcast_keyword}")
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    results = ocr_reader.readtext(screenshot)
    for result in results:
        if broadcast_keyword.lower() in result[1].lower():
            logging.info("Broadcast was sent correctly.")
            return True
    logging.error(f"Broadcast keyword was not found: {broadcast_keyword}.")
    return False


def get_and_return_system_name(region: Tuple) -> list:
    screenshot_of_top_left_corner = jpg_screenshot_of_the_selected_region(region)
    results = ocr_reader.readtext(screenshot_of_top_left_corner)
    return results


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
        return True
    return False


def select_gates_only_tab() -> None:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    search_for_string_in_region('gates', OVERVIEW_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def tackle_enemy_ship(initial_run: bool = False) -> None:
    if initial_run:
        if SCRAMBLER_EQUIPPED:
            pyautogui.press(SCRAM)
        if WEBIFIER_EQUIPPED:
            pyautogui.press(WEB)
    elif SCRAMBLER_EQUIPPED and not sig.check_if_scrambler_is_operating():
        pyautogui.press(SCRAM)
    elif WEBIFIER_EQUIPPED and not sig.check_if_webifier_is_operating():
        pyautogui.press(WEB)


def target_lock() -> None:
    with pyautogui.hold('ctrl'):
        pyautogui.click()


def test_check_region(region: Tuple) -> list:
    overview_and_selected_item_screenshot = jpg_screenshot_of_the_selected_region(region)
    test_result = ocr_reader.readtext(overview_and_selected_item_screenshot)
    return test_result


def turn_recording_on_or_off() -> None:
    pyautogui.hotkey('alt', 'f9', interval=0.1)
