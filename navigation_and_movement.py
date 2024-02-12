import random
import time
import logging
from typing import Tuple

import pyautogui

from constants import (
    DESTINATION_HOME_STATION, DESTINATION_STATION, GATE_ON_ROUTE, CAPACITOR_REGION, IS_FC,
    HOME_SYSTEM, MAX_EXPECTED_TRAVEL_DISTANCE, MAX_NUMBER_OF_ATTEMPTS, MID_TO_TOP_REGION,
    OVERVIEW_REGION, PC_SPECIFIC_CONFIDENCE, SCANNER_REGION, TOP_LEFT_REGION, SYSTEMS_TO_TRAVEL_TO,
    PAUSE_AFTER_DESTINATION_BROADCAST, AMARR_SYSTEMS, MINMATAR_SYSTEMS
)

import communication_and_coordination as cc
import helper_functions as hf
import scanning_and_information_gathering as sig
import tests as test


def align_to(target: list) -> None:
    pyautogui.moveTo(target)
    with pyautogui.hold('a'):
        pyautogui.click()


def approach() -> None:
    time.sleep(0.1)
    logging.info("Approaching target.")
    pyautogui.keyDown('q')
    time.sleep(0.1)
    pyautogui.keyUp('q')


def approach_capture_point() -> None:
    logging.info("Approaching capture point.")
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    hf.search_for_string_in_region('capture',
                                   OVERVIEW_REGION,
                                   screenshot,
                                   move_mouse_to_string=True,
                                   )
    time.sleep(0.1)
    pyautogui.click()
    time.sleep(0.1)
    approach()
    hf.move_mouse_away_from_overview()
    hf.generic_variables.approaching_capture_point = True


def choose_system_to_travel_to(systems: list) -> str:
    if len(hf.generic_variables.unvisited_systems) == 0:
        random_system = random.choice(systems)
        unvisited_systems = systems
        unvisited_systems.remove(random_system)
        return random_system
    random_system = random.choice(hf.generic_variables.unvisited_systems)
    hf.generic_variables.unvisited_systems.remove(random_system)
    return random_system


def dock_at_station() -> bool:
    logging.info("Attempting to dock at station.")
    stations = [DESTINATION_HOME_STATION, DESTINATION_STATION]
    hf.select_stations_and_beacons_tab()
    time.sleep(0.2)
    for station in stations:
        try:
            docking_station = pyautogui.locateCenterOnScreen(station,
                                                             confidence=PC_SPECIFIC_CONFIDENCE,
                                                             grayscale=False,
                                                             region=OVERVIEW_REGION)
            if docking_station is not None:
                pyautogui.moveTo(docking_station)
                pyautogui.keyDown('d')
                pyautogui.click()
                pyautogui.keyUp('d')
                logging.info("Station found, attempting to warp and dock.")
                return True
        except pyautogui.ImageNotFoundException:
            logging.warning("Station was not found.")
            return False


def gtfo() -> None:
    warp_to_safe_spot()
    wait_for_warp_to_end()
    travel_home()


def jump_through_acceleration_gate() -> bool:
    logging.info("Attempting to jump through acceleration gate.")
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if hf.search_for_string_in_region('acceleration',
                                      OVERVIEW_REGION,
                                      screenshot,
                                      move_mouse_to_string=True):
        pyautogui.click()
        time.sleep(0.1)
        pyautogui.keyDown('d')
        time.sleep(0.1)
        pyautogui.keyUp('d')
        logging.info("Acceleration gate icon found. Jumping.")
        time.sleep(0.1)
        hf.move_mouse_away_from_overview()
        time.sleep(0.1)
        pyautogui.click()
        return True
    else:
        logging.warning("Acceleration gate icon was not found.")
        return False


def jump_through_gate_to_destination() -> bool:
    try:
        next_gate_on_route = pyautogui.locateCenterOnScreen(GATE_ON_ROUTE,
                                                            confidence=PC_SPECIFIC_CONFIDENCE,
                                                            grayscale=False,
                                                            region=OVERVIEW_REGION)
        if next_gate_on_route is not None:
            pyautogui.moveTo(next_gate_on_route)
            pyautogui.keyDown('d')
            pyautogui.click()
            pyautogui.keyUp('d')
            hf.move_mouse_away_from_overview()
            logging.info("Gate to destination was found.")
            return True
    except pyautogui.ImageNotFoundException:
        logging.info("Gate to destination was not found.")
        return False


def orbit_target() -> None:
    with pyautogui.hold('w'):
        pyautogui.click()


def set_destination(systems: list) -> bool:
    logging.info("Setting new destination.")
    if hf.generic_variables.destination and hf.generic_variables.destination in systems:
        systems.remove(hf.generic_variables.destination)
    hf.select_gates_only_tab()
    hf.move_mouse_away_from_overview()
    time.sleep(0.5)
    hf.open_or_close_notepad()
    time.sleep(4)
    hf.generic_variables.destination = choose_system_to_travel_to(systems)
    screenshot = hf.jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    destination_system = hf.search_for_string_in_region(hf.generic_variables.destination,
                                                        TOP_LEFT_REGION,
                                                        screenshot,
                                                        move_mouse_to_string=True)
    if destination_system:
        time.sleep(0.3)
        pyautogui.rightClick()
        time.sleep(0.3)
    else:
        logging.error(f"Cannot set new destination. Could not find {hf.generic_variables.destination}.")
        hf.open_or_close_notepad()
        return False
    screenshot = hf.jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    destination_confirmation = hf.search_for_string_in_region('destination',
                                                              TOP_LEFT_REGION,
                                                              screenshot,
                                                              move_mouse_to_string=True)
    if destination_confirmation:
        pyautogui.click()
        pyautogui.moveTo(destination_system)
    hf.open_or_close_notepad()
    x, y = pyautogui.size()
    hf.move_mouse_away_from_overview([x/2, y/2])
    logging.info(f"New destination set: {hf.generic_variables.destination}.")
    return True


def set_destination_from_broadcast(test_mode: bool = False) -> bool:
    logging.info("Trying to obtain destination from broadcast.")
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if test_mode:
        destination_systems = AMARR_SYSTEMS + MINMATAR_SYSTEMS + [HOME_SYSTEM]
    else:
        destination_systems = SYSTEMS_TO_TRAVEL_TO.copy()

    for system in destination_systems:
        if hf.search_for_string_in_region(system, SCANNER_REGION, screenshot, move_mouse_to_string=True):
            hf.generic_variables.destination = system
            pyautogui.rightClick()
            time.sleep(0.1)
            screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
            hf.search_for_string_in_region('dest', SCANNER_REGION, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            logging.info("Traveling to new destination.")
            return True
    logging.error("Could not read destination from broadcast.")
    return False


def set_destination_home(initial_run: bool = False) -> None:
    pyautogui.hotkey('alt', 'a', interval=0.1)
    screenshot = hf.jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    if hf.search_for_string_in_region('set destination',
                                      MID_TO_TOP_REGION,
                                      screenshot,
                                      move_mouse_to_string=True):
        pyautogui.click()
    elif initial_run is False:
        screenshot = hf.jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
        hf.search_for_string_in_region('character', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
        pyautogui.click()
        screenshot = hf.jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
        hf.search_for_string_in_region('home station', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
        pyautogui.click()
        set_destination_home(True)

    pyautogui.hotkey('alt', 'a', interval=0.1)
    hf.generic_variables.destination = HOME_SYSTEM


def stop_ship() -> None:
    with pyautogui.hold('ctrl'):
        pyautogui.press('space')


def travel_home(fleet_up: bool = False) -> None:
    logging.info(f"Returning to home system: {HOME_SYSTEM}")
    if fleet_up:
        cc.form_fleet()
    set_destination_home()
    if IS_FC is True:
        cc.broadcast_destination()

    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if not sig.check_if_destination_system_was_reached(HOME_SYSTEM, SCANNER_REGION):
            travel_to_destination()
        else:
            break
    dock_at_station()


def travel_to_destination() -> None:
    for _ in range(MAX_EXPECTED_TRAVEL_DISTANCE):
        logging.info("Attempting to find next gate to destination.")
        if not jump_through_gate_to_destination():
            hf.select_gates_only_tab()
            if not jump_through_gate_to_destination():
                hf.select_fw_tab()
                break
        wait_for_warp_to_end()
        time.sleep(12)
        # Repairer turns off automatically after jump.
        hf.generic_variables.is_repairing = False
    logging.info("Destination reached.")
    hf.notification_beep()


def travel_to_destination_as_fc() -> None:
    if sig.check_if_docked():
        if not sig.check_if_in_fleet():
            cc.form_fleet()
            time.sleep(0.1)
        undock()
        time.sleep(20)
    else:
        if not sig.check_if_in_fleet(is_docked=False):
            cc.form_fleet()
            time.sleep(0.1)
    # cannot broadcast destination while docked
    set_destination(SYSTEMS_TO_TRAVEL_TO)
    hf.select_fleet_tab()
    hf.select_broadcasts()
    cc.broadcast_hold_position()
    cc.wait_for_fleet_members_to_join_and_broadcast_destination()
    if hf.generic_variables.destination:
        for _ in range(MAX_NUMBER_OF_ATTEMPTS):
            if not sig.check_if_destination_system_was_reached(hf.generic_variables.destination, SCANNER_REGION):
                travel_to_destination()
            else:
                break
        warp_to_safe_spot()
        wait_for_warp_to_end()


def travel_to_destination_as_fleet_member(initial_run: bool = True) -> None:
    if initial_run:
        if not sig.check_if_in_fleet():
            cc.join_existing_fleet()
        if not hf.select_broadcasts():
            logging.error("Cannot locate broadcasts.")
        if sig.check_if_docked():
            undock()
            time.sleep(20)
        if not hf.select_fleet_tab():
            logging.error("Cannot locate fleet tab.")
        cc.broadcast_in_position()
        time.sleep(2)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if set_destination_from_broadcast():
            break

    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if not sig.check_if_destination_system_was_reached(hf.generic_variables.destination, SCANNER_REGION):
            travel_to_destination()
        else:
            break
    warp_to_safe_spot()
    wait_for_warp_to_end()
    cc.broadcast_in_position()


def undock():
    pyautogui.hotkey('ctrl', 'shift', 'x', interval=0.1)
    hf.move_mouse_away_from_overview()


def warp_to_safe_spot() -> None:
    logging.info("Warping to a safe spot.")
    hf.move_mouse_away_from_overview()
    pyautogui.rightClick()
    time.sleep(0.1)
    screenshot = hf.jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    hf.search_for_string_in_region('loc', TOP_LEFT_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.1)
    screenshot = hf.jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    hf.search_for_string_in_region('spo', TOP_LEFT_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


# This won't work for warping to probe scanner items.
def warp_within_70_km(coords: list, region: Tuple, retry: bool = False) -> bool:
    logging.info("Warping within 70km.")
    pyautogui.moveTo(coords)
    pyautogui.rightClick()
    screenshot = hf.jpg_screenshot_of_the_selected_region(region)

    if hf.search_for_string_in_region('ithin',
                                      region, screenshot,
                                      move_mouse_to_string=True,
                                      selected_result=0):
        time.sleep(0.5)
        screenshot = hf.jpg_screenshot_of_the_selected_region(region)
        if hf.search_for_string_in_region('ithin 70',
                                          region,
                                          screenshot,
                                          move_mouse_to_string=True):
            pyautogui.click()

            if IS_FC is True:
                cc.broadcast_align_to(coords)

            hf.move_mouse_away_from_overview()
            return True

    if retry is False:
        logging.info(f"Retrying warp.")
        hf.move_mouse_away_from_overview()
        pyautogui.click()
        new_coords = [coords[0] + random.randint(-10, 10), coords[1]]
        warp_within_70_km(new_coords, region, retry=True)

    if retry is True:
        logging.critical("Could not warp after retry.")
        test.test_check_region(OVERVIEW_REGION)
        return False


def warp_to_0(target: list, region: Tuple) -> bool:
    logging.info("Warping to 0.")
    pyautogui.moveTo(target)
    pyautogui.rightClick()
    screenshot = hf.jpg_screenshot_of_the_selected_region(region)
    if hf.search_for_string_in_region('warp', region, screenshot,
                                      move_mouse_to_string=True):
        pyautogui.click()
        return True
    logging.error(f"Something went wrong. Can't find the related string in region: {region}.")
    return False


def wait_for_warp_to_end() -> None:
    time.sleep(4)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        time.sleep(3)
        screenshot = hf.jpg_screenshot_of_the_selected_region(CAPACITOR_REGION)
        if not hf.search_for_string_in_region('wa', CAPACITOR_REGION, screenshot):
            logging.info("Warp complete.")
            return
        hf.generic_variables.prop_module_on = False
        logging.info("In warp.")
