from typing import List, Tuple, Union
import time
import logging


import helper_functions as hf
from constants import SELECTED_ITEM_REGION


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
        logging.debug(f"test_time = {time.time() - test_time}")
        logging.error(f"Index error occurred in test_if_target_in_selected_items - target_name: {target_name}")
        return False
