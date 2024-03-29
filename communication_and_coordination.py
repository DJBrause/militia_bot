import logging
import pyautogui
import time
from typing import Tuple

from constants import (
    FLEET_MEMBERS_COUNT, MAX_NUMBER_OF_ATTEMPTS, MID_TO_TOP_REGION, OVERVIEW_REGION, SCANNER_REGION,
    TOP_LEFT_REGION, IS_FC
)

import helper_functions as hf
import navigation_and_movement as nm
import tests as test


def await_fleet_members_to_arrive() -> None:
    logging.info("Waiting for all fleet members to arrive at destination.")
    broadcast_hold_position()
    fleet_members_to_arrive = FLEET_MEMBERS_COUNT
    hf.select_broadcasts()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        logging.info(f"Number of fleet members to report in: {fleet_members_to_arrive}")
        if test.test_in_position_broadcast():
            fleet_members_to_arrive -= 1
        if fleet_members_to_arrive == 0:
            logging.info("All fleet members reported in position. Proceeding.")
            return
        time.sleep(10)


def await_command_decision_on_safe_spot() -> bool:
    logging.info("Awaiting orders.")
    hf.select_fleet_tab()
    hf.select_broadcasts()
    in_align = False
    in_position_sent = False
    while True:
        if not in_position_sent and test.test_if_correct_broadcast_was_sent('hold'):
            broadcast_in_position()
            in_position_sent = True
        if test.test_if_correct_broadcast_was_sent('travel'):
            return False
        if not in_align and align_to_broadcast_reaction():
            in_align = True
        if warp_to_member_if_enemy_is_spotted():
            return True


def broadcast_align_to(target: list) -> None:
    time.sleep(0.1)
    with pyautogui.hold('alt'):
        with pyautogui.hold('v'):
            pyautogui.moveTo(target)
            pyautogui.click()
    logging.info('Align to broadcast sent.')
    hf.clear_broadcast_history()


def broadcast_current_location() -> None:
    pyautogui.press(',')


def broadcast_destination(retry: bool = False) -> bool:
    if hf.generic_variables.destination is not None:
        hf.open_or_close_notepad()
        time.sleep(0.5)
        screenshot = hf.jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
        hf.search_for_string_in_region(hf.generic_variables.destination,
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
            time.sleep(0.2)
            pyautogui.click()
            hf.move_mouse_away_from_overview()

        hf.open_or_close_notepad()

        if test.test_if_correct_broadcast_was_sent('travel'):
            logging.info(f"Destination broadcast to {hf.generic_variables.destination} sent")
            return True
        elif retry is False:
            logging.error("Expected broadcast was not sent: Destination. Retrying...")
            broadcast_destination(retry=True)
        else:
            logging.critical("Broadcast destination failed after retry.")
            return False
    logging.error("Destination not found. Cannot broadcast.")
    return False


def broadcast_enemy_spotted() -> None:
    time.sleep(0.1)
    logging.info("Enemy was spotted.")
    pyautogui.press('z')


def broadcast_in_position() -> None:
    # Apparently if '.' is pressed after selecting broadcasts, it expands the menu right below broadcast tab.
    # In order to avoid this bug an empty space needs to be clicked somewhere.
    hf.move_mouse_away_from_overview()
    pyautogui.click()
    time.sleep(0.3)
    pyautogui.keyDown('.')
    time.sleep(0.1)
    pyautogui.keyUp('.')
    logging.info("In position broadcast sent.")


def broadcast_hold_position() -> None:
    logging.info("Hold position broadcast sent.")
    with pyautogui.hold('ctrl'):
        pyautogui.press('.')


def broadcast_target(target_coordinates: list) -> None:
    logging.info("Target broadcast.")
    pyautogui.moveTo(target_coordinates)
    pyautogui.rightClick()
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    hf.search_for_string_in_region('broadcast', OVERVIEW_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def align_to_broadcast_reaction() -> bool:
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if hf.search_for_string_in_region('align', SCANNER_REGION, screenshot, move_mouse_to_string=True, debug=True):
        pyautogui.rightClick()
        time.sleep(0.1)
        screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
        if hf.search_for_string_in_region('lign to', SCANNER_REGION, screenshot, move_mouse_to_string=True, debug=True):
            pyautogui.click()
            # Sending broadcast_in_position in order to occlude the "align to" broadcast below broadcast history.
            broadcast_in_position()
            hf.clear_broadcast_history()
            logging.info("Align to broadcast found.")
            return True
        elif hf.search_for_string_in_region('align', SCANNER_REGION, screenshot, selected_result=1,
                                            move_mouse_to_string=True, debug=True):
            pyautogui.click()
            # Sending broadcast_in_position in order to occlude the "align to" broadcast below broadcast history.
            broadcast_in_position()
            hf.clear_broadcast_history()
            logging.info("Align to broadcast found.")
            return True
        else:
            logging.error("check_for_broadcast_and_align - could not find 'align to'")
    return False


def create_fleet_advert() -> None:
    logging.info("Creating fleet advert.")
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
    logging.info("Fleet advert created.")


def form_fleet() -> None:
    logging.info("Forming fleet.")
    if not hf.select_fleet_tab():
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
    if IS_FC:
        create_fleet_advert()
    hf.select_broadcasts()
    hf.clear_broadcast_history()
    hf.move_mouse_away_from_overview()
    logging.info("Fleet formed.")


def join_existing_fleet() -> None:
    logging.info("Joining an existing fleet.")
    if not hf.select_fleet_tab():
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
            logging.info("Fleet joined.")
            return
        else:
            time.sleep(3)


def target_broadcast_ship(region: Tuple) -> bool:
    screenshot = hf.jpg_screenshot_of_the_selected_region(region)
    if hf.search_for_string_in_region('target', region, screenshot, move_mouse_to_string=True):
        for _ in range(3):
            pyautogui.keyDown('ctrl')
            pyautogui.click()
            pyautogui.keyUp('ctrl')
        return True
    return False


def wait_for_fleet_members_to_join_and_broadcast_destination() -> None:
    logging.info("Awaiting 'in position' broadcast from all fleet members.")
    broadcast_count = 0
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if test.test_in_position_broadcast():
            broadcast_destination()
            broadcast_count += 1
        if broadcast_count == FLEET_MEMBERS_COUNT:
            logging.info("All fleet members are ready. Proceeding to destination.")
            hf.clear_broadcast_history()
            return
        time.sleep(3)
    broadcast_destination()


def wait_for_in_position_broadcast() -> None:
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if test.test_in_position_broadcast():
            break
        time.sleep(1)


def warp_to_member_if_enemy_is_spotted() -> bool:
    logging.info("Checking for 'enemy spotted' broadcast.")
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    broadcast = hf.search_for_string_in_region('spotted', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    if broadcast:
        logging.info("'Enemy spotted' broadcast detected. Warping to fleet member.")
        nm.warp_within_70_km(broadcast, SCANNER_REGION)
        # broadcast_in_position is needed to obscure the last broadcast sent just above the broadcast icons
        broadcast_in_position()
        hf.clear_broadcast_history()
        return True
    return False
