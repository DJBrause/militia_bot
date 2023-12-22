from typing import Tuple, List, Union
import os
import json
from dotenv import load_dotenv
import ast

import cv2
import pyautogui
import io
import time
from easyocr import Reader
import keyboard
from PIL import Image
import winsound

load_dotenv()

DEFAULT_CONFIDENCE = 0.9
MAX_EXPECTED_TRAVEL_DISTANCE = 20
PROP_MOD = 'f1'
TACKLE_MODS = ['f2', 'f3']
GUNS = 'f4'

ocr_reader = Reader(['en'])
probe_scanner_region = ast.literal_eval(os.environ.get('PROBE_SCANNER_REGION'))
screen_center_region = ast.literal_eval(os.environ.get('SCREEN_CENTER_REGION'))
capacitor_region = ast.literal_eval(os.environ.get('CAPACITOR_REGION'))
overview_and_selected_item_region = ast.literal_eval(os.environ.get('OVERVIEW_AND_SELECTED_ITEM_REGION'))
top_left_region = ast.literal_eval(os.environ.get('TOP_LEFT_REGION'))
local_window_region = ast.literal_eval(os.environ.get('LOCAL_WINDOW_REGION'))
chat_window_region = ast.literal_eval(os.environ.get('CHAT_WINDOW_REGION'))
mid_to_top_region = ast.literal_eval(os.environ.get('MID_TO_TOP_REGION'))
targets_region = ast.literal_eval(os.environ.get('TARGETS_REGION'))
test_region = ast.literal_eval(os.environ.get('TEST_REGION'))

unlock_target_image = 'images/unlock_icon.PNG'
cannot_lock_icon = 'images/cannot_lock.PNG'
lock_target_icon = 'images/lock_target.PNG'
scrambler_on_icon = 'images/scrambler_on.PNG'
gate_on_route = 'images/gate_on_route.PNG'
destination_station = 'images/destination_station.PNG'
destination_home_station = 'images/destination_home_station.PNG'

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
# todo warping to safespot
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


def check_if_in_warp() -> bool:
    screenshot_of_the_bottom_of_the_screen = jpg_screenshot_of_the_selected_region(capacitor_region)
    if search_for_string_in_region('wa', capacitor_region, screenshot_of_the_bottom_of_the_screen, debug=True):
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
        target_is_lockable = pyautogui.locateCenterOnScreen(lock_target_icon, confidence=0.99,
                                                            region=overview_and_selected_item_region)
        if target_is_lockable is not None:
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


def orbit_target() -> None:
    pyautogui.keyDown('w')
    pyautogui.click()
    pyautogui.keyUp('w')


def target_and_engage_a_hostile_ship(region: Tuple, overview_content: list, ship: str) -> None:
    # turn_recording_on_or_off()
    for item in overview_content:
        if ship in item[1]:
            coordinates = bounding_box_center_coordinates(bounding_box=item[0], region=region)
            pyautogui.moveTo(coordinates)

            # Use AB/MWD
            pyautogui.press(PROP_MOD)

            for _ in range(3):
                approach()
            # counter = 0
            while True:
                target_lock()
                time.sleep(0.2)
                if check_if_target_is_locked(overview_and_selected_item_region):
                    for _ in range(3):
                        orbit_target()
                        time.sleep(0.1)
                    break

            # Fire guns and try to tackle
            pyautogui.press(GUNS)

            while True:
                if not check_if_scrambler_is_operating():
                    pyautogui.press('f2')
                else:
                    break

            notification_beep()


def check_if_target_is_locked(region: Tuple) -> bool:
    try:
        unlock_target_icon_present = pyautogui.locateCenterOnScreen(unlock_target_image, grayscale=False,
                                                                    confidence=DEFAULT_CONFIDENCE, region=region)
        if unlock_target_icon_present is not None:
            pyautogui.moveTo(x=unlock_target_icon_present[0], y=unlock_target_icon_present[1])
            return True
    except pyautogui.ImageNotFoundException:
        return False


def check_if_scrambler_is_operating() -> bool:
    try:
        if pyautogui.locateCenterOnScreen(scrambler_on_icon, grayscale=False, confidence=DEFAULT_CONFIDENCE,
                                          region=targets_region):
            return True
        return False
    except pyautogui.ImageNotFoundException:
        pass


def manage_engagement() -> None:
    if not check_if_target_is_locked(overview_and_selected_item_region):
        pass


def set_destination_home() -> None:
    pyautogui.keyDown('alt')
    pyautogui.press('a')
    pyautogui.keyUp('alt')
    screenshot = jpg_screenshot_of_the_selected_region(mid_to_top_region)
    search_for_string_in_region('home station', mid_to_top_region, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    screenshot = jpg_screenshot_of_the_selected_region(mid_to_top_region)
    search_for_string_in_region('set destination', mid_to_top_region, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    pyautogui.keyDown('alt')
    pyautogui.press('a')
    pyautogui.keyUp('alt')


def jump_through_gate_to_destination() -> bool:
    try:
        next_gate_on_route = pyautogui.locateCenterOnScreen(gate_on_route, confidence=DEFAULT_CONFIDENCE,
                                                            grayscale=False, region=overview_and_selected_item_region)
        if next_gate_on_route is not None:
            pyautogui.moveTo(x=next_gate_on_route[0], y=next_gate_on_route[1])
            pyautogui.keyDown('d')
            pyautogui.click()
            pyautogui.keyUp('d')
            move_mouse_away_from_overview()
            return True
    except pyautogui.ImageNotFoundException:
        return False


def travel_to_destination() -> None:
    for _ in range(MAX_EXPECTED_TRAVEL_DISTANCE):
        if not jump_through_gate_to_destination():
            break
        time.sleep(2)
        for c in range(100):
            if not check_if_in_warp():
                beep_x_times(2)
                break
            time.sleep(1)
        time.sleep(12)
    notification_beep()


def dock_at_station() -> None:
    stations = [destination_station, destination_home_station]
    for station in stations:
        try:
            docking_station = pyautogui.locateCenterOnScreen(station, confidence=DEFAULT_CONFIDENCE,
                                                             grayscale=False,
                                                             region=overview_and_selected_item_region)
            if docking_station is not None:
                pyautogui.moveTo(x=docking_station[0], y=docking_station[1])
                pyautogui.keyDown('d')
                pyautogui.click()
                pyautogui.keyUp('d')
                break
        except pyautogui.ImageNotFoundException:
            pass


def move_mouse_away_from_overview() -> None:
    pyautogui.moveTo(x=100, y=10)


def warp_to_safe_spot() -> None:
    pyautogui.moveTo(x=50, y=30)
    pyautogui.rightClick()
    time.sleep(0.1)
    screenshot = jpg_screenshot_of_the_selected_region(top_left_region)
    search_for_string_in_region('loc', top_left_region, screenshot, move_mouse_to_string=True, debug=True)
    pyautogui.click()
    time.sleep(0.1)
    screenshot = jpg_screenshot_of_the_selected_region(top_left_region)
    for _ in range(5):
        search_for_string_in_region('spo', top_left_region, screenshot, move_mouse_to_string=True, debug=True)
        pyautogui.click()
        break


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
    # region_selector()
    # main_loop()
    # undock()
    # time.sleep(5)
    # set_destination_home()
    # travel_to_destination()
    # dock_at_station()
    warp_to_safe_spot()
