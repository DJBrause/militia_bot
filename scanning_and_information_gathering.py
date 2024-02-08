import time
from typing import Tuple
import logging

import pyautogui
import pyscreeze

from constants import (
    ALL_FRIGATES, AVOID, CAPACITOR_REGION, LOCAL_REGION, DEFAULT_CONFIDENCE, TARGETS_REGION,
    SCRAMBLER_ON_ICON, UNLOCK_TARGET_ICON, MAX_NUMBER_OF_ATTEMPTS, MID_TO_TOP_REGION, NPC_MINMATAR,
    SELECTED_ITEM_REGION, OVERVIEW_REGION, WEBIFIER_ON_ICON, SCANNER_REGION, LOCK_TARGET_ICON, WEBIFIER_ON_ICON_SMALL,
    MAX_PIXEL_SPREAD, DSCAN_SLIDER, SHIP_HEALTH_BARS_COORDS, REPAIRER, SCRAMBLER_ON_ICON_SMALL, RAT_ICON,
    OFFENSIVE_PLEXING, PC_SPECIFIC_CONFIDENCE
)

import communication_and_coordination as cc
import helper_functions as hf
import navigation_and_movement as nm


def get_dscan_result() -> list:
    # Check if any frigate is present in the directional scanner readout.
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    results = hf.ocr_reader.readtext(screenshot)
    frigate_on_scan = [f for f in ALL_FRIGATES for r in results if f == r[1]]
    return frigate_on_scan





def test_if_station_in_system() -> bool:
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if hf.search_for_string_in_region('station', OVERVIEW_REGION, screenshot):
        return True
    return False


# to be used by fm
def check_for_target_broadcast() -> bool:
    pass


def check_if_avoided_ship_is_on_scan_result(scan_result: list) -> bool:
    avoided_ship_on_scan = [ship for ship in scan_result for avoided_ship in AVOID if ship == avoided_ship]
    if len(avoided_ship_on_scan) > 0:
        logging.info("Detected ship is present on avoidance list.")
        return True
    return False


def check_if_destination_system_was_reached(destination_system: str, region: Tuple) -> bool:
    hf.select_fleet_tab()
    hf.select_broadcasts()
    hf.clear_broadcast_history()
    cc.broadcast_current_location()
    time.sleep(0.2)
    screenshot = hf.jpg_screenshot_of_the_selected_region(region)
    if hf.search_for_string_in_region(destination_system, region, screenshot):
        return True
    return False


def check_if_docked() -> bool:
    logging.info("Checking if ship is docked.")
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if hf.search_for_string_in_region('undock', OVERVIEW_REGION, screenshot, move_mouse_to_string=True):
        logging.info("The ship is docked.")
        return True
    logging.info("The ship is not docked.")
    return False


def check_if_in_fleet(is_docked: bool = True) -> bool:
    logging.info("Checking if ship is in fleet.")
    if not is_docked:
        hf.select_fleet_tab()
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if hf.search_for_string_in_region('respawn', SCANNER_REGION, screenshot):
        logging.info("The ship is in fleet.")
        return True
    logging.info("The ship is not in fleet.")
    return False


def check_if_in_plex() -> bool:
    logging.info("Checking if ship is in the plex.")
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if hf.search_for_string_in_region('capture', OVERVIEW_REGION, screenshot):
        logging.info("Capture point found. Ship is in the plex.")
        return True
    logging.warning("Capture point not found. Ship is not in the plex.")
    return False


def check_if_location_secured() -> bool:
    screenshot = hf.jpg_screenshot_of_the_selected_region(LOCAL_REGION)
    if OFFENSIVE_PLEXING:
        if hf.search_for_string_in_region('captured', LOCAL_REGION, screenshot):
            return True
    else:
        if hf.search_for_string_in_region('secure', LOCAL_REGION, screenshot):
            return True
    return False


def check_if_scrambler_is_operating() -> bool:
    try:
        if pyautogui.locateCenterOnScreen(SCRAMBLER_ON_ICON,
                                          grayscale=False,
                                          confidence=DEFAULT_CONFIDENCE,
                                          region=TARGETS_REGION):
            return True
    except pyautogui.ImageNotFoundException:
        try:
            if pyautogui.locateCenterOnScreen(SCRAMBLER_ON_ICON_SMALL,
                                              grayscale=False,
                                              confidence=DEFAULT_CONFIDENCE,
                                              region=TARGETS_REGION):
                return True
        except pyautogui.ImageNotFoundException:
            return False


def check_if_target_is_locked() -> bool:
    try:
        if pyautogui.locateCenterOnScreen(UNLOCK_TARGET_ICON,
                                          grayscale=False,
                                          confidence=DEFAULT_CONFIDENCE,
                                          region=SELECTED_ITEM_REGION):
            logging.info("Target is locked.")
            return True
    except pyautogui.ImageNotFoundException:
        logging.info("Target is not locked.")
        return False


def check_if_target_is_outside_range() -> bool:
    too_far_away_message = ['the', 'target', 'too', 'far', 'away', 'within']
    region_screenshot = hf.jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    results = hf.ocr_reader.readtext(region_screenshot)
    filtered_strings = [item for sublist in results for item in sublist if isinstance(item, str)]
    for word in too_far_away_message:
        if word in filtered_strings:
            return True
    return False


def check_if_webifier_is_operating() -> bool:
    time.sleep(0.1)
    try:
        if pyautogui.locateCenterOnScreen(WEBIFIER_ON_ICON, grayscale=False, confidence=PC_SPECIFIC_CONFIDENCE,
                                          region=TARGETS_REGION):
            return True
    except pyautogui.ImageNotFoundException:
        try:
            if pyautogui.locateCenterOnScreen(WEBIFIER_ON_ICON_SMALL, grayscale=False, confidence=PC_SPECIFIC_CONFIDENCE,
                                              region=TARGETS_REGION):
                return True
        except pyautogui.ImageNotFoundException:
            return False


def check_if_within_targeting_range() -> bool:
    try:
        target_is_lockable = pyautogui.locateCenterOnScreen(LOCK_TARGET_ICON, confidence=0.99,
                                                            region=SELECTED_ITEM_REGION)
        if target_is_lockable is not None:
            return True
    except pyautogui.ImageNotFoundException:
        return False


def check_insurance(open_mail: bool = True) -> bool:
    logging.info("Checking if ship insurance was paid out.")
    if open_mail:
        hf.open_or_close_mail()
    screenshot = hf.jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    if hf.search_for_string_in_region('insurance', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        if hf.search_for_string_in_region('commerce', MID_TO_TOP_REGION, screenshot):
            hf.search_for_string_in_region('delete', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            hf.open_or_close_mail()
            logging.info("Insurance was paid. Ship considered to be destroyed.")
            return True
        hf.open_or_close_mail()
        logging.info("Insurance was not paid out. Ship considered to be alive.")
        return False
    hf.search_for_string_in_region('communications', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    check_insurance(open_mail=False)


def check_overview_for_hostiles() -> list:
    targets = hf.extract_pilot_names_and_ship_types_from_screenshot()
    if targets:
        logging.info(f"A target was detected in the overview: {targets[0][0], targets[0][1][1]}.")
        return targets
    logging.info("No target detected in the overview.")


def check_overview_for_rats() -> str:
    logging.info("Checking overview for rats.")
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if hf.search_for_string_in_region(NPC_MINMATAR[0], OVERVIEW_REGION, screenshot):
        return NPC_MINMATAR[0]
    try:
        if pyautogui.locateOnScreen(RAT_ICON,
                                    grayscale=False,
                                    confidence=DEFAULT_CONFIDENCE,
                                    region=OVERVIEW_REGION):
            return NPC_MINMATAR[0]
    except pyautogui.ImageNotFoundException:
        logging.info("Rat was not found in the overview.")


def check_probe_scanner_and_try_to_activate_site(searched_site: str) -> bool:
    logging.info("Checking for inactive sites in probe scanner.")
    select_probe_scanner()
    time.sleep(0.2)
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    site = hf.search_for_string_in_region(searched_site, SCANNER_REGION, screenshot)
    if site:
        logging.info("Inactive site found. Activating.")
        for _ in range(MAX_NUMBER_OF_ATTEMPTS):
            if nm.warp_to_0(site, SCANNER_REGION):
                time.sleep(0.1)
                nm.stop_ship()
                return True
    logging.info("No inactive site found.")
    return False


def check_ship_status() -> dict:
    ship_status = {'shield': None, 'armor': None, 'structure': None}
    logging.info("Checking ship status.")
    pyautogui.moveTo(SHIP_HEALTH_BARS_COORDS)
    time.sleep(0.4)
    screenshot = hf.jpg_screenshot_of_the_selected_region(CAPACITOR_REGION)
    result = hf.ocr_reader.readtext(screenshot)

    for i in range(len(result)):
        if 'sh' in result[i][1].lower():
            ship_status['shield'] = hf.convert_nine_to_percent(result[i + 1][1])
        if 'ar' in result[i][1].lower():
            ship_status['armor'] = hf.convert_nine_to_percent(result[i + 1][1])
        if 'str' in result[i][1].lower():
            ship_status['structure'] = hf.convert_nine_to_percent(result[i + 1][1])

    return ship_status


def make_a_short_range_three_sixty_scan(initial_scan: bool = True) -> list:
    logging.info("Making a short range 360 degrees scan.")
    if initial_scan:
        select_directional_scanner()
    if hf.generic_variables.short_scan is not True:
        logging.info("Setting scan range to minimum and scan angle to 360 degrees.")
        set_dscan_range_to_minimum()
        set_dscan_angle_to_three_sixty_degree()
        hf.generic_variables.short_scan = True
    time.sleep(3)
    # pyautogui.press('v') doesn't seem to be working here
    pyautogui.keyDown('v')
    time.sleep(0.1)
    pyautogui.keyUp('v')
    time.sleep(0.1)
    result = get_dscan_result()
    return result


def scan_sites_in_system(site: str) -> None:
    targets_within_and_outside_scan_range = get_sites_within_and_outside_scan_range(site)

    for target_within_range in targets_within_and_outside_scan_range['targets_within_scan_range']:
        set_dscan_range_to_maximum()
        time.sleep(0.1)
        set_dscan_angle_to_five_degree()
        scan_site_within_range(target_within_range)
        time.sleep(5)

    for target_outside_range in targets_within_and_outside_scan_range['targets_outside_scan_range']:
        nm.warp_within_70_km(hf.bounding_box_center_coordinates(target_outside_range[1][0],
                                                                OVERVIEW_REGION), OVERVIEW_REGION)
        nm.wait_for_warp_to_end()
        make_a_short_range_three_sixty_scan()
        time.sleep(2)
        nm.warp_to_safe_spot()


# returns screen coordinates of the scanned site if scan results were empty (no ship was detected in that location)
def scan_sites_within_scan_range(sites_to_scan: list) -> list:
    for scan in sites_to_scan:
        coordinates = hf.bounding_box_center_coordinates(scan[1][0], OVERVIEW_REGION)
        scan_results = scan_site_within_range(coordinates)
        if scan_results:
            logging.info("Ship or ships were detected at the site. Site is invalid.")
        else:
            logging.info("No ship detected at the site. Site is valid.")
            return coordinates
    return []


def scan_site_within_range(site_coordinates: list) -> list:
    pyautogui.moveTo(site_coordinates)
    pyautogui.keyDown('v')
    pyautogui.click()
    pyautogui.keyUp('v')
    time.sleep(0.5)
    scan_result = get_dscan_result()
    return scan_result


def get_sites_within_and_outside_scan_range(site: str) -> dict:
    sites_within_and_outside_scan_range = {'sites_within_scan_range': [], 'sites_outside_scan_range': []}
    sites_within_scan_range = []
    sites_outside_scan_range = []
    hf.select_stations_and_beacons_tab()
    select_directional_scanner()
    if hf.generic_variables.short_scan is True or hf.generic_variables.short_scan is None:
        logging.info("Setting scanner to long range and 5 degrees.")
        set_dscan_range_to_maximum()
        set_dscan_angle_to_five_degree()
        hf.generic_variables.short_scan = False
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    results = hf.ocr_reader.readtext(screenshot)
    searched_term_found = [result for result in results if site.lower() in result[1].lower()]

    # filtering out the same strings that are in the same row
    filtered_searched_term_found = searched_term_found

    for i in searched_term_found:
        for y in searched_term_found:
            y_value = y[0][2][1]
            if i != y and y_value - MAX_PIXEL_SPREAD <= i[0][2][1] <= y_value + MAX_PIXEL_SPREAD:
                filtered_searched_term_found.remove(i)

    distance_in_au = [result for result in results if result[1][0].lower().isdigit()]
    distance_and_site_pairs = [(distance, site) for distance in distance_in_au for site in filtered_searched_term_found
                               if site[0][2][1] - MAX_PIXEL_SPREAD <= distance[0][2][1] <= site[0][2][1] +
                               MAX_PIXEL_SPREAD]

    for pair in distance_and_site_pairs:
        distance_str_to_float = pair[0][1].replace(',', '.')
        try:
            if 'AU' in distance_str_to_float:
                distance_str_to_float = float(distance_str_to_float[:-3])
            else:
                distance_str_to_float = float(distance_str_to_float)

            if distance_str_to_float <= 14.3:
                sites_within_scan_range.append(pair)
            else:
                sites_outside_scan_range.append(pair)
        except ValueError:
            sites_outside_scan_range.append(pair)
    sites_within_and_outside_scan_range['sites_within_scan_range'] = sites_within_scan_range
    sites_within_and_outside_scan_range['sites_outside_scan_range'] = sites_outside_scan_range
    return sites_within_and_outside_scan_range


def select_directional_scanner() -> bool:
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if hf.search_for_string_in_region('direct', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        return True

    pyautogui.hotkey('alt', 'd', interval=0.1)
    if not hf.search_for_string_in_region('direct', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        return False


def select_probe_scanner() -> bool:
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if hf.search_for_string_in_region('probe', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        return True

    pyautogui.hotkey('alt', 'p', interval=0.1)
    if not hf.search_for_string_in_region('probe', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        return False


def set_dscan_angle_to_five_degree() -> None:
    try:
        angle_slider = None
        screen_width, screen_height = pyautogui.size()
        sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER,
                                              confidence=hf.generic_variables.dscan_confidence,
                                              region=SCANNER_REGION)
        for slider in sliders:
            if angle_slider is None:
                angle_slider = slider
            if slider[0] > angle_slider[0]:
                angle_slider = slider
        x = angle_slider[0] + (angle_slider[2] / 2)
        y = angle_slider[1] + (angle_slider[3] / 2)
        pyautogui.moveTo(x=x, y=y)
        pyautogui.click()
        pyautogui.dragTo(screen_width * 0.85, y, 0.5, button='left')
        hf.move_mouse_away_from_overview()
        hf.generic_variables.short_scan = False
        time.sleep(3)
    except pyscreeze.ImageNotFoundException:
        logging.error("Slider image not found. Trying to enable directional scanner.")
        select_directional_scanner()


def set_dscan_angle_to_three_sixty_degree() -> None:
    try:
        angle_slider = None
        screen_width, screen_height = pyautogui.size()
        sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER,
                                              confidence=hf.generic_variables.dscan_confidence,
                                              region=SCANNER_REGION)
        for slider in sliders:
            if angle_slider is None:
                angle_slider = slider
            if slider[0] > angle_slider[0]:
                angle_slider = slider
        x = angle_slider[0] + (angle_slider[2] / 2)
        y = angle_slider[1] + (angle_slider[3] / 2)
        pyautogui.moveTo(x=x, y=y)
        pyautogui.click()
        pyautogui.dragTo(screen_width, y, 0.5, button='left')
        hf.move_mouse_away_from_overview()
        hf.generic_variables.short_scan = True
    except pyscreeze.ImageNotFoundException:
        logging.error("Slider image not found. Trying to enable directional scanner.")
        select_directional_scanner()


def set_dscan_range_to_maximum() -> bool:
    range_slider = None
    screen_width, screen_height = pyautogui.size()
    try:
        sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER,
                                              confidence=hf.generic_variables.dscan_confidence,
                                              region=SCANNER_REGION)
        for slider in sliders:
            if range_slider is None:
                range_slider = slider
            if slider[0] < range_slider[0]:
                range_slider = slider
        x = range_slider[0] + (range_slider[2] / 2)
        y = range_slider[1] + (range_slider[3] / 2)
        pyautogui.moveTo(x=x, y=y)
        pyautogui.click()
        pyautogui.dragTo(screen_width * 0.95, y, 0.5, button='left')
        hf.move_mouse_away_from_overview()
        return True
    except pyscreeze.ImageNotFoundException:
        return False


def set_dscan_range_to_minimum() -> None:
    try:
        range_slider = None
        screen_width, screen_height = pyautogui.size()
        sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER,
                                              confidence=hf.generic_variables.dscan_confidence,
                                              region=SCANNER_REGION)
        for slider in sliders:
            if range_slider is None:
                range_slider = slider
            if slider[0] < range_slider[0]:
                range_slider = slider
        x = range_slider[0] + (range_slider[2] / 2)
        y = range_slider[1] + (range_slider[3] / 2)
        pyautogui.moveTo(x=x, y=y)
        pyautogui.click()
        pyautogui.dragTo(screen_width * 0.80, y, 0.5, button='left')
    except pyscreeze.ImageNotFoundException:
        logging.error("Slider image not found in set_dscan_range_to_minimum.")
    hf.move_mouse_away_from_overview()


def check_health_and_decide_if_to_repair() -> None:
    health = check_ship_status()
    time.sleep(0.1)

    if health:
        try:
            if health['armor'] != '100%' and not hf.generic_variables.is_repairing:
                logging.info("Damage detected. Turning repairer on.")
                time.sleep(0.1)
                pyautogui.press(REPAIRER)
                hf.generic_variables.is_repairing = True
            if health['armor'] == '100%' and hf.generic_variables.is_repairing:
                logging.info("No damage detected. Turning repairer off.")
                time.sleep(0.1)
                pyautogui.press(REPAIRER)
                hf.generic_variables.is_repairing = False

        except IndexError as e:
            logging.error(f"IndexError in check_health_and_decide_if_to_repair: {e}")
