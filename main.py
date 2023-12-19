from typing import Tuple, List

import pyautogui
import io
import time
from easyocr import Reader
import keyboard
from PIL import Image
import winsound

ocr_reader = Reader(['en'])
probe_scanner_region = (2836, 811, 603, 627)
screen_center_region = (1146, 360, 1318, 780)
bottom_of_the_screen_region = (1408, 1251, 306, 169)
overview_and_selected_item_region = (2900, 0, 539, 937)

# todo killing rat at the plex
# todo scanning for hostiles
# todo if FC - sending broadcasts
# todo if wingman, then warping to FC and aggroing broadcast target
# todo check if in warp



"""
In directional scanner following keys filter out:

1 - Anomalies
2 - Cosmic signatures
3 - Deployables
4 - Structures
5 - Ships
6 - Drones and Charges

Acceleration Gate
D - Activate Gate
"""


def region_selector():
    beep_x_times(1)
    x, y = 0, 0
    while True:
        if keyboard.is_pressed('ctrl'):
            x, y = pyautogui.position()

            # print(pyautogui.pixel(x,y))
            z = pyautogui.pixel(x, y)
            print(x, y, z)
            beep_x_times(1)

        if keyboard.is_pressed('alt'):
            x_, y_ = pyautogui.position()
            print(f"{x}, {y}, {x_ - x}, {y_ - y}")
            beep_x_times(3)

        if keyboard.is_pressed('shift'):
            beep_x_times(2)
            break


def undock():
    undock_keys = ['ctrl', 'shift', 'x']
    for key in undock_keys:
        pyautogui.keyDown(key)
    time.sleep(0.2)
    for key in undock_keys:
        pyautogui.keyUp(key)


def search_for_string_in_region(searched_string: str, region: Tuple, image_file: Image, move_mouse_to_string: bool) \
        -> bool:
    results = ocr_reader.readtext(image_file)
    try:
        for result in results:
            if searched_string.lower() in result[1].lower():
                middle_of_bounding_box = bounding_box_center_coordinates(result[0], region=region)
                if move_mouse_to_string:
                    pyautogui.moveTo(x=middle_of_bounding_box[0], y=middle_of_bounding_box[1])
                beep_x_times(1)
                return True
        print(f"{searched_string} not found within specified region.")
        with open(f'failed_ocr_log_for_{searched_string}.txt', 'w') as file:
            file.write(str(results))
        return False
    except TypeError:
        beep_x_times(3)
        return False


def warp_to_scout_combat_site(region: Tuple) -> None:
    screenshot_of_scanner = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('probe', probe_scanner_region, screenshot_of_scanner, True)
    pyautogui.click()
    screenshot_of_scanner = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('scout', probe_scanner_region, screenshot_of_scanner, True)
    pyautogui.rightClick()
    screenshot_of_scanner_with_warp_to_option = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('to within', probe_scanner_region, screenshot_of_scanner_with_warp_to_option, True)
    pyautogui.click()
    beep_x_times(2)


def jump_through_acceleration_gate(region: Tuple) -> None:
    overview_and_selected_item_screenshot = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('acceleration', overview_and_selected_item_region,overview_and_selected_item_screenshot,
                                True)
    pyautogui.click()
    time.sleep(0.1)
    for _ in range(3):
        pyautogui.press('d')
        time.sleep(0.2)


def jpg_screenshot_of_the_selected_region(region: Tuple) -> Image:
    screenshot = pyautogui.screenshot(region=region)
    temp_image = io.BytesIO()
    screenshot.save(temp_image, format="JPEG")
    temp_image.seek(0)
    screenshot_jpeg = Image.open(temp_image)
    return screenshot_jpeg


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


def check_if_in_warp(region: Tuple) -> bool:
    screenshot_of_the_bottom_of_the_screen = jpg_screenshot_of_the_selected_region(region)
    if search_for_string_in_region('warp', bottom_of_the_screen_region, screenshot_of_the_bottom_of_the_screen, False):
        return True
    return False


def beep_x_times(x):
    for _ in range(x):
        winsound.Beep(frequency=1500, duration=100)
        time.sleep(0.1)


def notification_beep():
    winsound.Beep(frequency=2000, duration=100)
    winsound.Beep(frequency=3000, duration=100)
    winsound.Beep(frequency=2000, duration=100)


if __name__ == "__main__":
    time.sleep(1)

    # undock()
    # region_selector()

    warp_to_scout_combat_site(probe_scanner_region)
    beep_x_times(1)
    time.sleep(2)
    for _ in range(160):
        if check_if_in_warp(bottom_of_the_screen_region):
            print(check_if_in_warp(bottom_of_the_screen_region))
            beep_x_times(1)
        else:
            print(check_if_in_warp(bottom_of_the_screen_region))
            notification_beep()
            break
    time.sleep(3)
    jump_through_acceleration_gate(overview_and_selected_item_region)




