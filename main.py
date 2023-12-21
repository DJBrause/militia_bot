from typing import Tuple, List, Union
from pathlib import Path

import cv2
import pyautogui
import io
import time
from easyocr import Reader
import keyboard
from PIL import Image
import winsound

DEFAULT_CONFIDENCE = 0.8
PROP_MOD = 'f1'
TACKLE_MODS = ['f2', 'f3']
GUNS = 'f4'

ocr_reader = Reader(['en'])
probe_scanner_region = (2836, 811, 603, 627)
screen_center_region = (1146, 360, 1318, 780)
bottom_of_the_screen_region = (1408, 1251, 306, 169)
overview_and_selected_item_region = (2900, 0, 539, 937)
top_left_region = (0, 0, 354, 401)
local_window_region = (43, 810, 398, 239)
chat_window_region = (52, 1396, 384, 37)
mid_to_top_region = (1160, 1, 976, 730)
test_region = (2704, 1, 732, 977)

unlock_target_image = 'images/unlock_icon.PNG'
cannot_lock_icon = 'images/cannot_lock.PNG'
lock_target_icon = 'images/lock_target.PNG'

amarr_frigates = ['Executioner', 'Inquisitor', 'Crucifier', 'Punisher', 'Magnate', 'Tormentor', 'Slicer']
caldari_frigates = ['Condor', 'Bantam', 'Griffin', 'Kestrel', 'Merlin', 'Heron', 'Hookbill']
gallente_frigates = ['Atron', 'Navitas', 'Tristan', 'Incursus', 'Maulus', 'Imicus', 'Comet']
minmatar_frigates = ['Slasher', 'Burst', 'Breacher', 'Rifter', 'Probe', 'Reaper', 'Firetail', 'Vigil']
rookie_ships = ['Ibis', 'Reaper', 'Impairor', 'Velator']
npc = 'Minmatar Frigate'
all_frigates = amarr_frigates + caldari_frigates + gallente_frigates + minmatar_frigates + rookie_ships

# todo killing rat at the plex
# todo scanning for hostiles
# todo GTFO if conditions are unfavorable
# todo if FC - sending broadcasts
# todo if wingman, then warping to FC and aggroing broadcast target
# todo report local system needs further work // Auto Link -> Solar System


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


def search_for_string_in_region(searched_string: str, region: Tuple, image_file: Image,
                                move_mouse_to_string: bool = False, debug: bool = False) -> bool:
    results = ocr_reader.readtext(image_file)
    if debug:
        print(results)
    try:
        for result in results:
            if searched_string.lower() in result[1].lower():
                middle_of_bounding_box = bounding_box_center_coordinates(result[0], region=region)
                if move_mouse_to_string:
                    pyautogui.moveTo(x=middle_of_bounding_box[0], y=middle_of_bounding_box[1])
                return True
        return False
    except TypeError:
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
    search_for_string_in_region('acceleration', overview_and_selected_item_region,
                                overview_and_selected_item_screenshot,
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


def get_and_return_system_name(region: Tuple) -> list:
    screenshot_of_top_left_corner = jpg_screenshot_of_the_selected_region(region)
    results = ocr_reader.readtext(screenshot_of_top_left_corner)
    return results


def beep_x_times(x) -> None:
    for _ in range(x):
        winsound.Beep(frequency=1500, duration=100)
        time.sleep(0.1)


def notification_beep() -> None:
    winsound.Beep(frequency=2000, duration=100)
    winsound.Beep(frequency=3000, duration=100)
    winsound.Beep(frequency=2000, duration=100)


def report_local_system() -> None:
    local_system = get_and_return_system_name(local_window_region)
    pyautogui.moveTo(chat_window_region[0] + 5, chat_window_region[1] + 5)
    pyautogui.click()
    pyautogui.write(local_system[-1][1])
    pyautogui.rightClick()
    beep_x_times(3)


def test_check_region(region) -> list:
    overview_and_selected_item_screenshot = jpg_screenshot_of_the_selected_region(region)
    test_result = ocr_reader.readtext(overview_and_selected_item_screenshot)
    return test_result


def check_for_hostiles_and_engage(region: Tuple) -> None:
    region_screenshot = jpg_screenshot_of_the_selected_region(region)
    results = ocr_reader.readtext(region_screenshot)
    filtered_strings = [item for sublist in results for item in sublist if isinstance(item, str)]
    for player_ship in all_frigates:
        if player_ship in filtered_strings:
            target_and_engage_a_hostile_ship(region, results, player_ship)
    if npc in filtered_strings:
        target_and_engage_a_hostile_ship(region, results, npc)
    return None


def check_if_target_is_outside_range() -> bool:
    too_far_away_message = ['the', 'target', 'too', 'far', 'away', 'within']
    region_screenshot = jpg_screenshot_of_the_selected_region(mid_to_top_region)
    results = ocr_reader.readtext(region_screenshot)
    filtered_strings = [item for sublist in results for item in sublist if isinstance(item, str)]
    for word in too_far_away_message:
        if word in filtered_strings:
            return True
    return False


def check_if_within_targeting_range() -> bool:
    try:
        target_is_lockable = pyautogui.locateCenterOnScreen(lock_target_icon, confidence=0.99, region=overview_and_selected_item_region)
        if target_is_lockable is not None:
            print(target_is_lockable)
            return True
    except pyautogui.ImageNotFoundException:
        return False


def approach() -> None:
    pyautogui.keyDown('q')
    pyautogui.click()
    pyautogui.keyUp('q')


def target_lock() -> None:
    pyautogui.keyDown('ctrl')
    pyautogui.click()
    pyautogui.keyUp('ctrl')


def turn_recording_on_or_off() -> None:
    pyautogui.keyDown('alt')
    pyautogui.press('f9')
    pyautogui.keyUp('alt')


def target_and_engage_a_hostile_ship(region: Tuple, overview_content: list, ship: str) -> None:
    turn_recording_on_or_off()
    for item in overview_content:
        if ship in item[1]:
            coordinates = bounding_box_center_coordinates(bounding_box=item[0], region=region)
            pyautogui.moveTo(coordinates)

            # Use AB/MWD
            pyautogui.press(PROP_MOD)

            approach()

            while True:
                target_lock()
                time.sleep(0.2)
                if check_if_target_is_outside_range():
                    pass
                else:
                    break

            target_lock()

            while True:
                if check_if_target_is_locked(overview_and_selected_item_region):
                    break
                target_lock()


            # Fire guns and try to tackle
            pyautogui.press(GUNS)
            mods = TACKLE_MODS
            while len(mods) != 0:
                for mod in mods:
                    pyautogui.press(mod)
                    if check_if_target_is_outside_range():
                        pass
                    else:
                        mods.remove(mod)

            notification_beep()


def check_if_target_is_locked(region: Tuple) -> bool:
    try:
        unlock_target_icon_present = pyautogui.locateCenterOnScreen(unlock_target_image, grayscale=False,
                                                                    confidence=DEFAULT_CONFIDENCE, region=region)
        if unlock_target_icon_present is not None:
            return True
    except pyautogui.ImageNotFoundException:
        return False


def manage_engagement() -> None:
    pass

# Undock, fly to scout site, kill rat, attack hostile if it warps in and call help,
# check if the ship is targetted still or not, if the plex finishes, fly back to station or safe spot.
def main_loop() -> None:
    # undock()
    # warp_to_scout_combat_site(probe_scanner_region)
    # time.sleep(2)
    # for _ in range(160):
    #     if check_if_in_warp(bottom_of_the_screen_region):
    #         pass
    #     else:
    #         time.sleep(3)
    #         break
    # jump_through_acceleration_gate(overview_and_selected_item_region)
    # time.sleep(2)
    # for _ in range(160):
    #     if check_if_in_warp(bottom_of_the_screen_region):
    #         pass
    #     else:
    #         time.sleep(3)
    #         break
    check_for_hostiles_and_engage(overview_and_selected_item_region)


if __name__ == "__main__":
    # time.sleep(3)
    # region_selector()
    main_loop()




