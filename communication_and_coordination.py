import pyautogui
import time
from typing import Tuple

from constants import (
    FLEET_MEMBERS_COUNT, MAX_NUMBER_OF_ATTEMPTS, MID_TO_TOP_REGION, OVERVIEW_REGION, SCANNER_REGION,
    TOP_LEFT_REGION
)

import helper_functions as hf
import main
import scanning_and_information_gathering as sig


def await_fleet_members_to_arrive() -> None:
    fleet_members_to_arrive = FLEET_MEMBERS_COUNT
    hf.select_broadcasts()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if sig.check_for_in_position_broadcast():
            fleet_members_to_arrive -= 1
        if fleet_members_to_arrive == 0:
            return
        time.sleep(2)


def await_orders() -> None:
    hf.select_fleet_tab()
    hf.select_broadcasts()
    while True:
        if sig.check_for_broadcast_and_align():
            break
        time.sleep(1)


def broadcast_align_to(target: list) -> None:
    with pyautogui.hold('alt'):
        with pyautogui.hold('v'):
            pyautogui.moveTo(target)
            pyautogui.click()
    hf.clear_broadcast_history()


def broadcast_current_location() -> None:
    pyautogui.press(',')


def broadcast_destination() -> bool:
    if main.generic_variables.destination is not None:
        hf.open_or_close_notepad()
        screenshot = hf.jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
        hf.search_for_string_in_region(main.generic_variables.destination,
                                       TOP_LEFT_REGION,
                                       screenshot,
                                       move_mouse_to_string=True)
        pyautogui.rightClick()
        screenshot = hf.jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
        broadcast = hf.search_for_string_in_region('broadcast',
                                                   TOP_LEFT_REGION,
                                                   screenshot,
                                                   move_mouse_to_string=True)
        if broadcast:
            time.sleep(0.3)
            pyautogui.click()
        hf.open_or_close_notepad()
        print(f'Destination broadcast to {main.generic_variables.destination} sent')
        return True
    return False


def broadcast_enemy_spotted() -> None:
    pyautogui.press('z')
    hf.clear_broadcast_history()


def broadcast_in_position() -> None:
    pyautogui.press('.')


def broadcast_target(target_coordinates: list) -> None:
    pyautogui.moveTo(target_coordinates)
    pyautogui.rightClick()
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    hf.search_for_string_in_region('broadcast', OVERVIEW_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def create_fleet_advert() -> None:
    hf.select_fleet_tab()
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    hf.search_for_string_in_region('advert', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    hf.search_for_string_in_region('create', SCANNER_REGION, screenshot, selected_result=1, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(1)
    screenshot = hf.jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    hf.search_for_string_in_region('submit', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def form_fleet() -> None:
    pyautogui.hotkey('ctrl', 'alt', 'f', interval=0.1)
    time.sleep(0.2)
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    form_fleet_button = hf.search_for_string_in_region('form fleet', SCANNER_REGION, screenshot,
                                                       move_mouse_to_string=True)
    if form_fleet_button:
        pyautogui.click()
        hf.move_mouse_away_from_overview()
    else:
        results = hf.ocr_reader.readtext(screenshot)
        for result in results:
            searched_string = 'fleet'
            if searched_string.lower() in result[1].lower():
                middle_of_bounding_box = hf.bounding_box_center_coordinates(result[0], region=SCANNER_REGION)
                pyautogui.click(middle_of_bounding_box)
                screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
            if hf.search_for_string_in_region('form fleet', SCANNER_REGION, screenshot, move_mouse_to_string=True):
                pyautogui.click()
                hf.move_mouse_away_from_overview()
    create_fleet_advert()
    hf.select_broadcasts()


def join_existing_fleet() -> None:
    pyautogui.hotkey('ctrl', 'alt', 'f', interval=0.1)
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    hf.search_for_string_in_region('ind', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.2)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        hf.search_for_string_in_region('ind', SCANNER_REGION, screenshot, selected_result=2, move_mouse_to_string=True)
        pyautogui.click()
        time.sleep(0.2)
        screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
        if hf.search_for_string_in_region('uncanny', SCANNER_REGION, screenshot, move_mouse_to_string=True):
            pyautogui.rightClick()
            time.sleep(0.2)
            screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
            hf.search_for_string_in_region('join', SCANNER_REGION, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            time.sleep(0.2)
            screenshot = hf.jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
            hf.search_for_string_in_region('yes', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            print('fleet joined')
            return
        else:
            time.sleep(3)


def target_broadcast_ship(region: Tuple) -> None:
    screenshot = hf.jpg_screenshot_of_the_selected_region(region)
    hf.search_for_string_in_region('target', region, screenshot, move_mouse_to_string=True)
    for _ in range(3):
        pyautogui.keyDown('ctrl')
        pyautogui.click()
        pyautogui.keyUp('ctrl')
