from typing import List, Tuple, Union
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
    logging.info("Testing if target name is present in Selected Item window.")
    screenshot = hf.jpg_screenshot_of_the_selected_region(SELECTED_ITEM_REGION)
    if hf.search_for_string_in_region(target_name, SELECTED_ITEM_REGION, screenshot):
        logging.info("Test passed - Intended target is selected.")
        return True
    logging.error("Test failed - Intended target is not selected.")
    return False
