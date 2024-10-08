import pyautogui
import time
import logging

from constants import (
    PROP_MOD, GUNS, OVERVIEW_REGION, SYSTEMS_TO_TRAVEL_TO, REPAIRER_EQUIPPED, MAX_NUMBER_OF_ATTEMPTS, DRONES_EQUIPPED,
    NPC_MINMATAR, SELECTED_ITEM_REGION, UNLOCK_TARGET_ICON, DEFAULT_CONFIDENCE, SHORT_SCAN_THRESHOLD, TIMEOUT_DURATION,
    REPAIRER_CYCLE_TIME, IS_FC, HOME_SYSTEM, OFFENSIVE_PLEXING, SCRAMBLER_EQUIPPED, WEBIFIER_EQUIPPED, SCRAM, WEB
)

import communication_and_coordination as cc
import helper_functions as hf
import navigation_and_movement as nm
import scanning_and_information_gathering as sig
import tests as test


def fc_behaviour_at_the_site() -> None:
    logging.info("Awaiting site completion while checking if enemy is present.")
    start_time = time.time()
    enemy_on_scan = False
    counter = 0
    while True:
        measure_behaviour_at_the_site_loop = time.time()

        engage_actions()
        restore_graphics_and_reload_ammo()

        if DRONES_EQUIPPED:
            hf.return_drones_to_bay()

        short_range_scan_result, enemy_on_scan = perform_scan_protocol(hf.generic_variables.initial_scan, enemy_on_scan)

        measure_check_if_avoided_ship_is_on_scan_result = time.time()
        if sig.check_if_avoided_ship_is_on_scan_result(short_range_scan_result):
            logging.info("Running away from the avoided ship.")
            break
        logging.debug(f"measure_check_if_avoided_ship_is_on_scan_result = "
                      f"{time.time() - measure_check_if_avoided_ship_is_on_scan_result}")

        if enemy_on_scan:
            logging.debug(f"counter = {counter}")
            if counter >= SHORT_SCAN_THRESHOLD:
                logging.info("No enemy ship jumped in. Resuming scanning.")
                enemy_on_scan = False
                counter = 0
            counter += 1

        measure_approach_capture_point = time.time()
        if not hf.generic_variables.approaching_capture_point:
            nm.approach_capture_point()
        logging.debug(
            f"measure_approach_capture_point = {time.time() - measure_approach_capture_point}")

        measure_unlock_outpost_if_locked = time.time()
        unlock_outpost_if_locked()
        logging.debug(
            f"measure_unlock_outpost_if_locked = {time.time() - measure_unlock_outpost_if_locked}")

        measure_check_if_location_secured = time.time()
        if sig.check_if_location_secured():
            logging.info("Site capture completed. Long live the Holy Amarr!")
            break
        logging.debug(
            f"measure_check_if_location_secured = {time.time()- measure_check_if_location_secured}")

        if (time.time() - start_time) > TIMEOUT_DURATION:
            logging.info("15 minutes have passed. I got bored. Moving on.")
            break

        hf.beep_x_times(1)
        logging.debug(f"measure_behaviour_at_the_site_loop = {time.time() - measure_behaviour_at_the_site_loop}")

    pyautogui.scroll(2000)
    time.sleep(0.2)
    nm.warp_to_safe_spot()
    nm.wait_for_warp_to_end()
    hf.clear_local_chat_content()


def fm_behaviour_at_the_site() -> None:
    measure_engage_hostiles = time.time()
    engage_hostiles()
    logging.debug(f"measure_engage_hostiles = {time.time() - measure_engage_hostiles}")
    pyautogui.scroll(2000)
    nm.warp_to_safe_spot()
    nm.wait_for_warp_to_end()


def unlock_outpost_if_locked() -> None:
    screenshot = hf.jpg_screenshot_of_the_selected_region(SELECTED_ITEM_REGION)
    if hf.search_for_string_in_region('outpost', SELECTED_ITEM_REGION, screenshot):
        try:
            unlock_target_icon_coordinates = pyautogui.locateCenterOnScreen(UNLOCK_TARGET_ICON,
                                                                            grayscale=False,
                                                                            confidence=DEFAULT_CONFIDENCE,
                                                                            region=SELECTED_ITEM_REGION,
                                                                            )
            if unlock_target_icon_coordinates:
                pyautogui.moveTo(unlock_target_icon_coordinates)
                pyautogui.click()
                hf.move_mouse_away_from_overview()
        except pyautogui.ImageNotFoundException:
            logging.error("unlock_outpost_if_locked - UNLOCK_TARGET_ICON image not found")


def engage_hostiles() -> None:
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        detected_hostiles = sig.check_overview_for_hostiles()
        if detected_hostiles:
            hf.generic_variables.approaching_capture_point = False
            logging.info(f"Hostiles are present in the overview: {detected_hostiles}")
            if not hf.generic_variables.graphics_removed:
                logging.info("Removing graphics for the time of engagement")
                hf.remove_graphics()
                hf.generic_variables.graphics_removed = True

            primary_target = detected_hostiles[0][0]

            if engagement_protocol(primary_target):
                cc.broadcast_enemy_spotted()
                maintain_engagement(primary_target)
        else:
            break


def restore_graphics_and_reload_ammo() -> None:
    if hf.generic_variables.graphics_removed:
        logging.info("No rat or hostile present. Restoring graphics and reloading ammo.")
        hf.remove_graphics()
        hf.generic_variables.graphics_removed = False
        hf.reload_ammo()


def engage_rat() -> None:
    rat = sig.check_overview_for_rats()
    if rat:
        hf.generic_variables.approaching_capture_point = False
        logging.info(f"Rat is present in the overview: {rat}")
        if not hf.generic_variables.graphics_removed:
            logging.info("Removing graphics for the time of engagement")
            hf.remove_graphics()
            hf.generic_variables.graphics_removed = True
        if engagement_protocol(rat):
            maintain_engagement(rat)


def attempt_to_select_the_enemy(name: str) -> bool:
    # This function attempts to populate the Selected Item window with the intended target based on Overview screenshot
    logging.info(f"Attempting to select: {name}")
    hf.move_mouse_away_from_overview()
    original_and_split_names = [name] + name.split()
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    for item in original_and_split_names:
        if hf.search_for_string_in_region(item, OVERVIEW_REGION, screenshot, move_mouse_to_string=True):
            pyautogui.click()
            time.sleep(0.1)
            if engage_target_and_approach(item):
                return True
    logging.info("Enemy is no longer present in the overview.")
    return False


def engage_target_and_approach(item: str) -> bool:
    # Engages the target and initiates approach if present in selected items.
    if test.test_if_target_in_selected_items(item):
        nm.approach()
        if not hf.generic_variables.prop_module_on:
            time.sleep(0.1)
            pyautogui.press(PROP_MOD)
            hf.generic_variables.prop_module_on = True
        time.sleep(0.1)
        hf.move_mouse_away_from_overview()
        return True
    return False


def attempt_to_target_lock_the_enemy(name: str) -> bool:
    logging.info(f"Attempting to acquire target lock on: {name}")
    if not hf.target_lock_using_selected_item(name):
        original_and_split_names = [name] + name.split()
        new_screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
        for item in original_and_split_names:
            if hf.search_for_string_in_region(item, OVERVIEW_REGION, new_screenshot, move_mouse_to_string=True):
                if hf.target_lock_using_overview(item):
                    hf.move_mouse_away_from_overview()
                    return True
        hf.move_mouse_away_from_overview()
        logging.info("Enemy is no longer present in the overview.")
        return False
    return True


def engagement_protocol(name: str) -> bool:
    logging.info("Engagement protocol is active.")
    if DRONES_EQUIPPED:
        hf.launch_drones()
    if attempt_to_select_the_enemy(name):
        if not attempt_to_target_lock_the_enemy(name):
            return False
        hf.tackle_enemy_ship(initial_run=True)
        time.sleep(0.1)
        pyautogui.press(GUNS)
        time.sleep(0.1)
        return True
    else:
        return False


def engage_actions():
    if OFFENSIVE_PLEXING:
        measure_engage_rat = time.time()
        engage_rat()
        logging.debug(f"measure_engage_rat = {time.time() - measure_engage_rat}")

    measure_engage_hostiles = time.time()
    engage_hostiles()
    logging.debug(f"measure_engage_hostiles = {time.time() - measure_engage_hostiles}")


def maintain_engagement(name: str) -> None:
    logging.info("Maintaining engagement.")
    start = time.time()
    while True:
        if sig.check_if_target_is_locked():
            handle_locked_target()
        else:
            if not handle_unlocked_target(name):
                return

        if name == NPC_MINMATAR[0]:
            detected_hostiles = sig.check_overview_for_hostiles()
            if detected_hostiles:
                return

        if REPAIRER_EQUIPPED and time.time() - start >= REPAIRER_CYCLE_TIME:
            sig.check_health_and_decide_if_to_repair_using_picture_detection()

        if SCRAMBLER_EQUIPPED and not hf.is_module_active('SCRAMBLER_BUTTON',
                                                          hf.button_detection_config.buttons_coordinates
                                                          ['SCRAMBLER_BUTTON']):
            pyautogui.press(SCRAM)

        if WEBIFIER_EQUIPPED and not hf.is_module_active('WEBIFIER_BUTTON',
                                                         hf.button_detection_config.buttons_coordinates
                                                         ['WEBIFIER_BUTTON']):
            pyautogui.press(WEB)

        if not hf.is_module_active('PROP_MOD_BUTTON',
                                   hf.button_detection_config.buttons_coordinates['PROP_MOD_BUTTON']):
            pyautogui.press(PROP_MOD)
            hf.generic_variables.prop_module_on = True

        if not hf.is_module_active('GUNS_BUTTON_COORDS',
                                   hf.button_detection_config.buttons_coordinates['GUNS_BUTTON_COORDS']):
            pyautogui.press(GUNS)
            hf.generic_variables.guns_activated = True


def handle_locked_target() -> None:
    logging.info("Handling a locked target.")
    nm.approach()
    time.sleep(0.1)
    hf.tackle_enemy_ship()
    if DRONES_EQUIPPED:
        hf.order_drones_to_engage()


def perform_scan_protocol(initial_scan, enemy_on_scan):
    measure_scans = time.time()
    logging.info("Making a short range scan.")
    if not enemy_on_scan:
        short_range_scan_result = sig.make_a_short_range_three_sixty_scan(initial_scan)
        hf.generic_variables.initial_scan = False
        if short_range_scan_result:
            logging.warning(f"A ship was detected on scan: {short_range_scan_result}")
            enemy_on_scan = True
    else:
        short_range_scan_result = []
    logging.debug(f"measure_scans = {time.time() - measure_scans}")
    return short_range_scan_result, enemy_on_scan


def handle_unlocked_target(name: str) -> bool:
    logging.info("Handling an unlocked target.")
    if test.test_if_target_in_selected_items(name):
        handle_locked_target()
        attempt_to_target_lock_the_enemy(name)
        return True
    else:
        if handle_enemy_selection(name):
            return True
        return False


def handle_enemy_selection(name: str) -> bool:
    updated_enemy_and_ship_type_pairs = hf.extract_pilot_names_and_ship_types_from_screenshot()
    if updated_enemy_and_ship_type_pairs and name in updated_enemy_and_ship_type_pairs[0][0]:
        attempt_to_select_the_enemy(name)
        return True
    return False


def scan_site_and_warp_to_70_if_empty(site_type: str) -> bool:
    # The purpose of this function is to scan the site if it is within the 14.3 AU limit and to warp to 70km
    # from the acceleration gate.
    logging.info("Scanning site in range and warping to 70km if it is empty.")
    hf.select_stations_and_beacons_tab()
    try:
        sites = sig.get_sites_within_and_outside_scan_range(site_type)
        coordinates = []
        if sites:
            coordinates = sig.scan_sites_within_scan_range(sites['sites_within_scan_range'])
        if coordinates:
            try:
                logging.debug(f"Coordinates = {coordinates}")
                nm.warp_within_70_km(coordinates[0], OVERVIEW_REGION)
            except pyautogui.PyAutoGUIException:
                logging.info(f"Could not find site coordinates: {coordinates[0]}")
                return False

            logging.info("Warping to the site.")
            return True
        logging.info("Scanned site is either outside scan range or is not empty.")
        return False
    except Exception as e:
        logging.error(f"An error occurred in scan_site_and_warp_to_70_if_empty: {e}")
        return False


def reaction_to_possible_interception() -> None:
    logging.info("Checking for possible interception.")
    hostiles = sig.check_overview_for_hostiles()
    if hostiles:
        logging.info(f"Hostiles are present in the overview: {hostiles}")
        cc.broadcast_enemy_spotted()
        if engagement_protocol(hostiles[0][0]):
            maintain_engagement(hostiles[0][0])
    nm.warp_to_safe_spot()


def decide_site_protocol_and_engage(wait_for_warp_to_end: bool = True) -> None:
    # Once at the site this function decides if FC or FM protocol should be used
    if wait_for_warp_to_end:
        nm.wait_for_warp_to_end()
    hf.select_fw_tab()
    nm.jump_through_acceleration_gate()

    nm.wait_for_warp_to_end()
    hf.move_mouse_away_from_overview()

    if IS_FC:
        fc_behaviour_at_the_site()
    else:
        fm_behaviour_at_the_site()


def explore_and_engage_outside_scan_range():
    # If a searched site is present in the system, but outside scan range, the ship will warp to 70km away from the site
    # and make a short range scan to ensure noone is inside.
    try:
        sites = sig.get_sites_within_and_outside_scan_range('scout')
        if sites['sites_outside_scan_range']:
            bounding_box = hf.bounding_box_center_coordinates(sites['sites_outside_scan_range'][0][1][0],
                                                              OVERVIEW_REGION)
            nm.warp_within_70_km(bounding_box, OVERVIEW_REGION)
            time.sleep(4)
            nm.wait_for_warp_to_end()
            if not sig.make_a_short_range_three_sixty_scan():
                decide_site_protocol_and_engage(wait_for_warp_to_end=False)
    except Exception as e:
        logging.critical(f"Following critical error occurred in explore_and_engage_outside_scan_range: {e}")


def fc_mission_plan(defensive_plexing: bool) -> None:
    destination_systems = list
    if defensive_plexing:
        amarr_frontline_systems = hf.get_amarr_frontline_systems_from_json()
        destination_systems = [system for system in SYSTEMS_TO_TRAVEL_TO if system in amarr_frontline_systems]
    for _ in range(len(destination_systems)):
        nm.travel_to_destination_as_fc(destination_systems)
        cc.await_fleet_members_to_arrive()
        if scan_site_and_warp_to_70_if_empty('scout'):
            decide_site_protocol_and_engage()
        elif sig.check_probe_scanner_and_try_to_activate_site('scout'):
            if scan_site_and_warp_to_70_if_empty('scout'):
                decide_site_protocol_and_engage()
            else:
                explore_and_engage_outside_scan_range()

    nm.travel_home()
    logging.info("Mission plan ended.")


def fm_mission_plan() -> None:
    nm.travel_to_destination_as_fleet_member()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if hf.generic_variables.destination.lower() == HOME_SYSTEM[0].lower():
            break
        if cc.await_command_decision_on_safe_spot():
            decide_site_protocol_and_engage()
        else:
            nm.travel_to_destination_as_fleet_member(False)

    logging.info(f"New destination was set for home: {HOME_SYSTEM}.")
    nm.travel_home()
    logging.info("Mission plan ended.")
