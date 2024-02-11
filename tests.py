import pprint

import pyautogui
import pyscreeze
from typing import Tuple
import time
import logging


import helper_functions as hf
import communication_and_coordination as cc
import navigation_and_movement as nm
from constants import (
    SELECTED_ITEM_REGION, SCANNER_REGION, UNLOCK_TARGET_ICON, CANNOT_LOCK_ICON, LOCK_TARGET_ICON, SCRAMBLER_ON_ICON,
    SCRAMBLER_ON_ICON_SMALL, WEBIFIER_ON_ICON, WEBIFIER_ON_ICON_SMALL, LASER_ON, LASER_ON_SMALL, RAT_ICON,
    GATE_ON_ROUTE, DESTINATION_STATION, DESTINATION_HOME_STATION, DSCAN_SLIDER, MORE_ICON, DEFAULT_CONFIDENCE,
    LOCAL_REGION, SYSTEMS_TO_TRAVEL_TO
)
import scanning_and_information_gathering as sig

images_used_in_program = [UNLOCK_TARGET_ICON, CANNOT_LOCK_ICON, LOCK_TARGET_ICON, SCRAMBLER_ON_ICON,
                          SCRAMBLER_ON_ICON_SMALL, WEBIFIER_ON_ICON, WEBIFIER_ON_ICON_SMALL, LASER_ON, LASER_ON_SMALL,
                          RAT_ICON, GATE_ON_ROUTE, DESTINATION_STATION, DESTINATION_HOME_STATION, DSCAN_SLIDER,
                          MORE_ICON]




def test_check_region(region: Tuple, save_screenshot: bool = False) -> list:
    screenshot = hf.jpg_screenshot_of_the_selected_region(region)
    if save_screenshot:
        try:
            image_path = r"images\test_region_image.jpg"
            screenshot.save(image_path)
        except Exception as e:
            print(e)

    test_result = hf.ocr_reader.readtext(screenshot)
    return test_result


def test_if_target_in_selected_items(target_name: str) -> bool:
    # Tests if the intended target is indeed selected. Otherwise, program is interacting with wrong object.
    test_time = time.time()
    try:
        logging.info("Testing if target name is present in Selected Item window.")
        split_target_name = target_name.split(' ')
        logging.debug(f"split_target_name = {split_target_name}")
        screenshot = hf.jpg_screenshot_of_the_selected_region(SELECTED_ITEM_REGION)
        for word in split_target_name:
            if hf.search_for_string_in_region(word, SELECTED_ITEM_REGION, screenshot, debug=True):
                logging.info("Test passed - Intended target is selected.")
                logging.debug(f"test_time = {time.time() - test_time}")
                return True
        logging.debug(f"test_time = {time.time() - test_time}")
        logging.error("Test failed - Intended target is not selected.")
        return False
    except IndexError:
        logging.debug(f"test_time_of_test_if_target_in_selected_items = {time.time() - test_time}")
        logging.error(f"Index error occurred in test_if_target_in_selected_items - target_name: {target_name}")
        return False


def test_if_correct_broadcast_was_sent(broadcast_keyword: str) -> bool:
    logging.info(f"Checking if broadcast keyword is present in broadcasts: {broadcast_keyword}")
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    results = hf.ocr_reader.readtext(screenshot)
    for result in results:
        if broadcast_keyword.lower() in result[1].lower():
            logging.info("Broadcast was sent correctly.")
            return True
    logging.error(f"Broadcast keyword was not found: {broadcast_keyword}.")
    return False


def test_in_position_broadcast() -> bool:
    # Checks if the 'in position' string is present in the SCANNER_REGION.
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if hf.search_for_string_in_region('in position', SCANNER_REGION, screenshot):
        hf.clear_broadcast_history()
        return True
    return False


class TestFleetCommunication:
    def test_more_icon_present_in_local_chat(self):
        more_icon = pyautogui.locateCenterOnScreen(MORE_ICON,
                                                   grayscale=False,
                                                   confidence=DEFAULT_CONFIDENCE,
                                                   region=LOCAL_REGION)
        pyautogui.moveTo(more_icon)
        pyautogui.click()
        time.sleep(0.1)
        screenshot = hf.jpg_screenshot_of_the_selected_region(LOCAL_REGION)
        clear_all_content = hf.search_for_string_in_region('clear', LOCAL_REGION, screenshot, move_mouse_to_string=True)

        assert more_icon is not None
        assert clear_all_content is not None
        assert isinstance(more_icon, pyscreeze.Point)
        assert isinstance(clear_all_content, tuple)

    # In order to run the broadcast test, ship has to be undocked. Preferably in a safe spot.
    def test_if_fleet_tab_is_selectable(self):
        if not sig.check_if_in_fleet():
            cc.form_fleet()
            time.sleep(0.1)
        fleet_tab_was_selected = hf.select_fleet_tab()

        assert fleet_tab_was_selected is True

    def test_if_broadcasts_tab_is_selectable(self):
        if not sig.check_if_in_fleet():
            cc.form_fleet()
            time.sleep(0.1)
        broadcasts_tab_was_selected = hf.select_broadcasts()

        assert broadcasts_tab_was_selected is True

    def test_in_position_broadcast(self):
        if not sig.check_if_in_fleet():
            cc.form_fleet()
            time.sleep(0.1)
        hf.select_fleet_tab()
        hf.select_broadcasts()
        hf.clear_broadcast_history()
        cc.broadcast_in_position()
        result = test_if_correct_broadcast_was_sent('in position')

        assert result is True

    def test_travel_to_broadcast(self):
        systems = SYSTEMS_TO_TRAVEL_TO.copy()
        if not sig.check_if_in_fleet():
            cc.form_fleet()
            time.sleep(0.1)
        hf.select_fleet_tab()
        hf.select_broadcasts()
        hf.clear_broadcast_history()
        nm.set_destination(systems)
        cc.broadcast_destination()
        result = test_if_correct_broadcast_was_sent(hf.generic_variables.destination)

        assert result is True

    def test_set_destination_from_broadcast(self):
        hf.generic_variables.destination = ''
        if not sig.check_if_in_fleet():
            cc.form_fleet()
            time.sleep(0.1)
        hf.select_fleet_tab()
        hf.select_broadcasts()
        result = nm.set_destination_from_broadcast()

        assert result is True
