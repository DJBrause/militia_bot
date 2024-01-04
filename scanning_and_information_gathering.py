import time
from typing import Tuple
import logging

import pyautogui
import pyscreeze

from constants import (ALL_FRIGATES, AVOID, CAPACITOR_REGION, LOCAL_REGION, DEFAULT_CONFIDENCE, TARGETS_REGION,
                       SCRAMBLER_ON_ICON, UNLOCK_TARGET_ICON, MAX_NUMBER_OF_ATTEMPTS, MID_TO_TOP_REGION, NPC_MINMATAR,
                       SELECTED_ITEM_REGION, OVERVIEW_REGION, WEBIFIER_ON_ICON, SCANNER_REGION, LOCK_TARGET_ICON,
                       MAX_PIXEL_SPREAD, DSCAN_SLIDER)

from communication_and_coordination import broadcast_current_location, bounding_box_center_coordinates

from helper_functions import (jpg_screenshot_of_the_selected_region, move_mouse_away_from_overview, select_broadcasts,
                              clear_broadcast_history, ocr_reader, search_for_string_in_region, select_fw_tab,
                              open_or_close_mail, select_fleet_tab)

from main import generic_variables

from navigation_and_movement import warp_within_70_km, warp_to_safe_spot


def check_dscan_result() -> list:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    results = ocr_reader.readtext(screenshot)
    frigate_on_scan = [f for f in ALL_FRIGATES for r in results if f == r[1]]
    return frigate_on_scan


def check_for_broadcast_and_align() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if search_for_string_in_region('align', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.rightClick()
        time.sleep(0.1)
        screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
        search_for_string_in_region('lign to', SCANNER_REGION, screenshot, move_mouse_to_string=True)
        pyautogui.click()
        clear_broadcast_history()
        return True
    return False


def check_for_in_position_broadcast() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if search_for_string_in_region('position', SCANNER_REGION, screenshot):
        clear_broadcast_history()
        return True
    return False


def check_for_station_in_system() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if search_for_string_in_region('station', OVERVIEW_REGION, screenshot):
        return True
    return False


def check_if_avoided_ship_is_on_scan_result(scan_result: list) -> bool:
    avoided_ship_on_scan = [ship for ship in scan_result for avoided_ship in AVOID if ship == avoided_ship]
    print(avoided_ship_on_scan)
    if len(avoided_ship_on_scan) > 0:
        return True
    return False


def check_if_destination_system_was_reached(destination_system: str, region: Tuple) -> bool:
    select_fleet_tab()
    select_broadcasts()
    clear_broadcast_history()
    broadcast_current_location()
    time.sleep(0.2)
    screenshot = jpg_screenshot_of_the_selected_region(region)
    if search_for_string_in_region(destination_system, region, screenshot):
        return True
    return False


def check_if_docked() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if search_for_string_in_region('undock', OVERVIEW_REGION, screenshot, move_mouse_to_string=True):
        return True
    return False


def check_if_in_fleet(is_docked: bool = True) -> bool:
    if not is_docked:
        select_fleet_tab()
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if search_for_string_in_region('respawn', SCANNER_REGION, screenshot):
        return True
    return False


def check_if_in_warp() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(CAPACITOR_REGION)
    if search_for_string_in_region('wa', CAPACITOR_REGION, screenshot):
        return True
    return False


def check_if_location_secured() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(LOCAL_REGION)
    if search_for_string_in_region('secure', LOCAL_REGION, screenshot):
        return True
    return False


def check_if_scrambler_is_operating() -> bool:
    try:
        if pyautogui.locateCenterOnScreen(SCRAMBLER_ON_ICON, grayscale=False, confidence=DEFAULT_CONFIDENCE,
                                          region=TARGETS_REGION):
            return True
        return False
    except pyautogui.ImageNotFoundException:
        pass


def check_if_target_is_locked() -> bool:
    try:
        unlock_target_icon_present = pyautogui.locateCenterOnScreen(UNLOCK_TARGET_ICON,
                                                                    grayscale=False,
                                                                    confidence=DEFAULT_CONFIDENCE,
                                                                    region=SELECTED_ITEM_REGION)
        if unlock_target_icon_present is not None:
            pyautogui.moveTo(unlock_target_icon_present)
            return True
    except pyautogui.ImageNotFoundException:
        return False


def check_if_target_is_outside_range() -> bool:
    too_far_away_message = ['the', 'target', 'too', 'far', 'away', 'within']
    region_screenshot = jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    results = ocr_reader.readtext(region_screenshot)
    filtered_strings = [item for sublist in results for item in sublist if isinstance(item, str)]
    for word in too_far_away_message:
        if word in filtered_strings:
            return True
    return False


def check_if_webifier_is_operating() -> bool:
    try:
        if pyautogui.locateCenterOnScreen(WEBIFIER_ON_ICON, grayscale=False, confidence=DEFAULT_CONFIDENCE,
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
    if open_mail:
        open_or_close_mail()
    screenshot = jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    if search_for_string_in_region('insurance', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        if search_for_string_in_region('commerce', MID_TO_TOP_REGION, screenshot):
            search_for_string_in_region('delete', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            open_or_close_mail()
            return True
        open_or_close_mail()
        return False
    search_for_string_in_region('communications', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    check_insurance(open_mail=False)


def check_overview_for_hostiles() -> list:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    results = ocr_reader.readtext(screenshot)
    targets = [(bounding_box_center_coordinates(target[0], OVERVIEW_REGION), target[1]) for target in results
               for ship in ALL_FRIGATES if target[1] == ship]
    if targets:
        logging.info('Targets were detected')
        return targets
    npc_targets = [(bounding_box_center_coordinates(target[0], OVERVIEW_REGION), target[1]) for target in results if
                   target[1] == NPC_MINMATAR]
    if npc_targets:
        logging.info('NPC targets were detected')
        return npc_targets


def check_probe_scanner_for_sites_and_warp_to_70(searched_site: str) -> bool:
    select_probe_scanner()
    time.sleep(0.2)
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    site = search_for_string_in_region(searched_site, SCANNER_REGION, screenshot)
    if site:
        warp_within_70_km(site, SCANNER_REGION)
        select_directional_scanner()
        return True
    return False


def make_a_short_range_three_sixty_scan(initial_scan: bool = True) -> list:
    if initial_scan:
        select_directional_scanner()
        set_dscan_range_to_minimum()
        set_dscan_angle_to_three_sixty_degree()
    time.sleep(4)
    # pyautogui.press('v') doesn't seem to be working here
    pyautogui.keyDown('v')
    time.sleep(0.1)
    pyautogui.keyUp('v')
    result = check_dscan_result()
    return result


def scan_sites_in_system(site: str) -> None:
    targets_within_and_outside_scan_range = scan_targets_within_and_outside_scan_range(site)

    for target_within_range in targets_within_and_outside_scan_range['targets_within_scan_range']:
        scan_target_within_range(target_within_range)
        time.sleep(5)

    for target_outside_range in targets_within_and_outside_scan_range['targets_outside_scan_range']:
        warp_within_70_km(bounding_box_center_coordinates(target_outside_range[1][0], OVERVIEW_REGION), OVERVIEW_REGION)
        time.sleep(3)
        for _ in range(MAX_NUMBER_OF_ATTEMPTS):
            if not check_if_in_warp():
                break
        make_a_short_range_three_sixty_scan()
        time.sleep(2)
        warp_to_safe_spot()


# returns coordinates of the scanned site if scan results were empty (no ship was detected in that location)
def scan_sites_within_scan_range(scanned_site_type: str) -> list:
    scan_results = scan_targets_within_and_outside_scan_range(scanned_site_type)
    if scan_results['targets_within_scan_range']:
        target_coordinates = [bounding_box_center_coordinates(target[1][0], OVERVIEW_REGION) for target in
                              scan_results['targets_within_scan_range'] if len(scan_target_within_range(target)) == 0]
        return target_coordinates
    return []


def scan_target_within_range(target: list) -> list:
    pyautogui.moveTo(bounding_box_center_coordinates(target[1][0], OVERVIEW_REGION))
    pyautogui.keyDown('v')
    pyautogui.click()
    pyautogui.keyUp('v')
    scan_result = check_dscan_result()
    return scan_result


def scan_targets_within_and_outside_scan_range(scan_target: str) -> dict:
    targets_within_and_outside_scan_range = {'targets_within_scan_range': [], 'targets_outside_scan_range': []}
    targets_within_scan_range = []
    targets_outside_scan_range = []
    select_fw_tab()
    select_directional_scanner()
    set_dscan_range_to_maximum()
    set_dscan_angle_to_five_degree()
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    results = ocr_reader.readtext(screenshot)
    searched_term_found = [result for result in results if scan_target.lower() in result[1].lower()]

    # filtering out items with the same string that are in the same row
    filtered_searched_term_found = searched_term_found

    for i in searched_term_found:
        for y in searched_term_found:
            y_value = y[0][2][1]
            if i != y and y_value-MAX_PIXEL_SPREAD <= i[0][2][1] <= y_value+MAX_PIXEL_SPREAD:
                filtered_searched_term_found.remove(i)

    distance_in_au = [result for result in results if result[1][0].lower().isdigit()]
    distance_and_site_pairs = [(distance, site) for distance in distance_in_au for site in filtered_searched_term_found
                               if site[0][2][1]-MAX_PIXEL_SPREAD <= distance[0][2][1] <= site[0][2][1]+MAX_PIXEL_SPREAD]

    for pair in distance_and_site_pairs:
        distance_str_to_float = pair[0][1].replace(',', '.')
        if 'AU' in distance_str_to_float:
            distance_str_to_float = float(distance_str_to_float[:-3])
        else:
            distance_str_to_float = float(distance_str_to_float)
        try:
            if distance_str_to_float <= 14.3:
                targets_within_scan_range.append(pair)
            else:
                targets_outside_scan_range.append(pair)
        except ValueError:
            targets_outside_scan_range.append(pair)
    targets_within_and_outside_scan_range['targets_within_scan_range'] = targets_within_scan_range
    targets_within_and_outside_scan_range['targets_outside_scan_range'] = targets_outside_scan_range
    return targets_within_and_outside_scan_range


def select_directional_scanner() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if search_for_string_in_region('direct', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        return True

    pyautogui.hotkey('alt', 'd', interval=0.1)
    if not search_for_string_in_region('direct', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        return False


def select_probe_scanner() -> None:
    pyautogui.hotkey('alt', 'p', interval=0.1)


def set_dscan_angle_to_five_degree() -> None:
    angle_slider = None
    screen_width, screen_height = pyautogui.size()
    sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER,
                                          confidence=generic_variables.dscan_confidence,
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
    move_mouse_away_from_overview()


def set_dscan_angle_to_three_sixty_degree() -> None:
    angle_slider = None
    screen_width, screen_height = pyautogui.size()
    sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER,
                                          confidence=generic_variables.dscan_confidence,
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
    move_mouse_away_from_overview()


def set_dscan_range_to_maximum() -> bool:
    range_slider = None
    screen_width, screen_height = pyautogui.size()
    try:
        sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER,
                                              confidence=generic_variables.dscan_confidence,
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
        move_mouse_away_from_overview()
        return True
    except pyscreeze.ImageNotFoundException:
        return False


def set_dscan_range_to_minimum() -> None:
    range_slider = None
    screen_width, screen_height = pyautogui.size()
    sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER,
                                          confidence=generic_variables.dscan_confidence,
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
    move_mouse_away_from_overview()
