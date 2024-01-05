import random
import time
from typing import Tuple

import pyautogui

from constants import (
    AMARR_SYSTEMS, DESTINATION_HOME_STATION, DESTINATION_STATION, GATE_ON_ROUTE,
    HOME_SYSTEM, MAX_EXPECTED_TRAVEL_DISTANCE, MAX_NUMBER_OF_ATTEMPTS, MID_TO_TOP_REGION,
    MINMATAR_SYSTEMS, OVERVIEW_REGION, PC_SPECIFIC_CONFIDENCE, SCANNER_REGION, TOP_LEFT_REGION
)

import communication_and_coordination as cc
import helper_functions as hf
import main
import scanning_and_information_gathering as sig


def align_to(target: list) -> None:
    pyautogui.moveTo(target)
    with pyautogui.hold('a'):
        pyautogui.click()


def approach() -> None:
    with pyautogui.hold('q'):
        pyautogui.click()


def choose_system_to_travel_to(systems: list) -> str:
    if len(main.generic_variables.unvisited_systems) == 0:
        random_system = random.choice(systems)
        unvisited_systems = systems
        unvisited_systems.remove(random_system)
        return random_system
    random_system = random.choice(main.generic_variables.unvisited_systems)
    main.generic_variables.unvisited_systems.remove(random_system)
    return random_system


def dock_at_station() -> bool:
    stations = [DESTINATION_HOME_STATION, DESTINATION_STATION]
    hf.select_fw_tab()
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
                return True
        except pyautogui.ImageNotFoundException:
            return False


def gtfo() -> None:
    warp_to_safe_spot()

    time.sleep(4)
    for _ in MAX_NUMBER_OF_ATTEMPTS:
        if not sig.check_if_in_warp():
            break
    travel_home()


def jump_through_acceleration_gate() -> None:
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    hf.search_for_string_in_region('acceleration',
                                   OVERVIEW_REGION,
                                   screenshot,
                                   move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.1)
    pyautogui.press('d')


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
            return True
    except pyautogui.ImageNotFoundException:
        return False


def orbit_target() -> None:
    with pyautogui.hold('w'):
        pyautogui.click()


def set_destination(systems: list) -> bool:
    if main.generic_variables.destination and main.generic_variables.destination in systems:
        systems.remove(main.generic_variables.destination)
    hf.select_gates_only_tab()
    hf.move_mouse_away_from_overview()
    time.sleep(0.5)
    hf.open_or_close_notepad()
    time.sleep(4)
    main.generic_variables.destination = choose_system_to_travel_to(systems)
    screenshot = hf.jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    destination_system = hf.search_for_string_in_region(main.generic_variables.destination,
                                                        TOP_LEFT_REGION,
                                                        screenshot,
                                                        move_mouse_to_string=True)
    if destination_system:
        time.sleep(0.3)
        pyautogui.rightClick()
        time.sleep(0.3)
    else:

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
    return True


def set_destination_from_broadcast() -> bool:
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
        for system in MINMATAR_SYSTEMS:
            if hf.search_for_string_in_region(system, SCANNER_REGION, screenshot, move_mouse_to_string=True):
                main.generic_variables.destination = system
                pyautogui.rightClick()
                time.sleep(0.1)
                screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
                hf.search_for_string_in_region('dest', SCANNER_REGION, screenshot, move_mouse_to_string=True)
                pyautogui.click()
                return True
            time.sleep(2)
    return False


def set_destination_home() -> None:
    pyautogui.hotkey('alt', 'a', interval=0.1)
    screenshot = hf.jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    hf.search_for_string_in_region('character', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    screenshot = hf.jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    hf.search_for_string_in_region('home station', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    screenshot = hf.jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    hf.search_for_string_in_region('set destination', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    pyautogui.hotkey('alt', 'a', interval=0.1)


def stop_ship() -> None:
    with pyautogui.hold('ctrl'):
        pyautogui.press('space')


def travel_home(fleet_up: bool = False) -> None:
    if fleet_up:
        cc.form_fleet()
    set_destination_home()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if not sig.check_if_destination_system_was_reached(HOME_SYSTEM, SCANNER_REGION):
            travel_to_destination()
        else:
            break
    dock_at_station()


def travel_to_destination() -> None:
    for _ in range(MAX_EXPECTED_TRAVEL_DISTANCE):
        if not jump_through_gate_to_destination():
            hf.select_gates_only_tab()
            if not jump_through_gate_to_destination():
                hf.select_fw_tab()
                break

        for _ in range(100):
            time.sleep(3)
            if not sig.check_if_in_warp():
                hf.beep_x_times(2)
                break
            time.sleep(1)
        time.sleep(12)
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
    set_destination(AMARR_SYSTEMS)

    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if hf.select_fleet_tab():
            break
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if hf.select_broadcasts():
            break
    main.wait_for_fleet_members_to_join_and_broadcast_destination()
    if main.generic_variables.destination:
        for _ in range(MAX_NUMBER_OF_ATTEMPTS):
            if not sig.check_if_destination_system_was_reached(main.generic_variables.destination, SCANNER_REGION):
                travel_to_destination()
            else:
                break
        warp_to_safe_spot()
        time.sleep(4)
        for _ in range(MAX_NUMBER_OF_ATTEMPTS):
            if not sig.check_if_in_warp():
                return


def travel_to_destination_as_fleet_member() -> None:
    cc.join_existing_fleet()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if hf.select_broadcasts():
            break
        else:
            print('cannot locate broadcasts')
            time.sleep(2)
    if sig.check_if_docked():
        undock()
        time.sleep(20)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        hf.select_fleet_tab()
    cc.broadcast_in_position()
    time.sleep(2)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if set_destination_from_broadcast():
            break

    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if not sig.check_if_destination_system_was_reached(main.generic_variables.destination, SCANNER_REGION):
            travel_to_destination()
        else:
            break
    warp_to_safe_spot()
    time.sleep(4)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if not sig.check_if_in_warp():
            break
    cc.broadcast_in_position()


def undock():
    pyautogui.hotkey('ctrl', 'shift', 'x', interval=0.1)
    hf.move_mouse_away_from_overview()


def warp_to_member_if_enemy_is_spotted() -> None:
    screenshot = hf.jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    broadcast = hf.search_for_string_in_region('spotted', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    if broadcast:
        warp_within_70_km(broadcast, OVERVIEW_REGION)


def warp_to_safe_spot() -> None:
    hf.move_mouse_away_from_overview()
    pyautogui.rightClick()
    time.sleep(0.1)
    screenshot = hf.jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    hf.search_for_string_in_region('loc', TOP_LEFT_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.1)
    screenshot = hf.jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    for _ in range(5):
        hf.search_for_string_in_region('spo', TOP_LEFT_REGION, screenshot, move_mouse_to_string=True)
        pyautogui.click()
        break


def warp_to_scout_combat_site(region: Tuple) -> None:
    sig.select_probe_scanner()
    screenshot_of_scanner = hf.jpg_screenshot_of_the_selected_region(region)
    hf.search_for_string_in_region('scout', SCANNER_REGION, screenshot_of_scanner, True)
    pyautogui.rightClick()
    screenshot_of_scanner_with_warp_to_option = hf.jpg_screenshot_of_the_selected_region(region)
    hf.search_for_string_in_region('to within', SCANNER_REGION, screenshot_of_scanner_with_warp_to_option, True)
    pyautogui.click()


def warp_within_70_km(target: list, region: Tuple) -> bool:
    pyautogui.moveTo(target)
    pyautogui.rightClick()
    screenshot = hf.jpg_screenshot_of_the_selected_region(region)
    if hf.search_for_string_in_region('ithin (', region, screenshot,
                                      move_mouse_to_string=True):
        screenshot = hf.jpg_screenshot_of_the_selected_region(region)
        hf.search_for_string_in_region('ithin 70', region, screenshot,
                                       move_mouse_to_string=True)
        pyautogui.click()
        return True
    elif hf.search_for_string_in_region('ithin', region, screenshot,
                                        move_mouse_to_string=True, selected_result=1):
        screenshot = hf.jpg_screenshot_of_the_selected_region(region)
        hf.search_for_string_in_region('ithin 70', region, screenshot,
                                       move_mouse_to_string=True)
        pyautogui.click()
        return True
    return False
