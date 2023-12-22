from typing import Tuple
import pyautogui
import time

from main import jpg_screenshot_of_the_selected_region, search_for_string_in_region, move_mouse_away_from_overview, \
    beep_x_times, notification_beep
from constants import *


def undock():
    undock_keys = ['ctrl', 'shift', 'x']
    for key in undock_keys:
        pyautogui.keyDown(key)
    time.sleep(0.2)
    for key in undock_keys:
        pyautogui.keyUp(key)


def approach() -> None:
    pyautogui.keyDown('q')
    pyautogui.click()
    pyautogui.keyUp('q')


def orbit_target() -> None:
    pyautogui.keyDown('w')
    pyautogui.click()
    pyautogui.keyUp('w')


def check_if_in_warp() -> bool:
    screenshot_of_the_bottom_of_the_screen = jpg_screenshot_of_the_selected_region(capacitor_region)
    if search_for_string_in_region('wa', capacitor_region, screenshot_of_the_bottom_of_the_screen, debug=True):
        return True
    return False


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


def warp_to_scout_combat_site(region: Tuple) -> None:
    screenshot_of_scanner = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('probe', scanner_region, screenshot_of_scanner, True)
    pyautogui.click()
    screenshot_of_scanner = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('scout', scanner_region, screenshot_of_scanner, True)
    pyautogui.rightClick()
    screenshot_of_scanner_with_warp_to_option = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('to within', scanner_region, screenshot_of_scanner_with_warp_to_option, True)
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
