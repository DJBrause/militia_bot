import pyautogui
import time
import logging

from constants import (
    PROP_MOD, GUNS, OVERVIEW_REGION, SYSTEMS_TO_TRAVEL_TO, REPAIRER_EQUIPPED, MAX_NUMBER_OF_ATTEMPTS, DRONES_EQUIPPED,
    NPC_MINMATAR, SELECTED_ITEM_REGION, UNLOCK_TARGET_ICON, DEFAULT_CONFIDENCE, SHORT_SCAN_THRESHOLD, TIMEOUT_DURATION,
    REPAIRER_CYCLE_TIME, IS_FC, HOME_SYSTEM
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
            nm.warp_to_safe_spot()
            nm.wait_for_warp_to_end()
            break

        hf.beep_x_times(1)
        logging.debug(f"measure_behaviour_at_the_site_loop = {time.time() - measure_behaviour_at_the_site_loop}")

    pyautogui.scroll(2000)
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
    logging.info(f"Attempting to select: {name}")
    hf.move_mouse_away_from_overview()
    original_and_split_names = [name] + name.split()
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    for item in original_and_split_names:
        if hf.search_for_string_in_region(item, OVERVIEW_REGION, screenshot, move_mouse_to_string=True):
            pyautogui.click()
            time.sleep(0.1)
            if test.test_if_target_in_selected_items(item):
                nm.approach()
                if not hf.generic_variables.prop_module_on:
                    time.sleep(0.1)
                    pyautogui.press(PROP_MOD)
                    hf.generic_variables.prop_module_on = True
                time.sleep(0.1)
                hf.move_mouse_away_from_overview()
                return True
    logging.info("Enemy is no longer present in the overview.")
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
    # Perform engagement actions
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
            sig.check_health_and_decide_if_to_repair()


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
    logging.info("Scanning site in range and warping to 70km if it is empty.")
    hf.select_stations_and_beacons_tab()
    try:
        sites = sig.get_sites_within_and_outside_scan_range(site_type)
        coordinates = []
        if sites:
            coordinates = sig.scan_sites_within_scan_range(sites['sites_within_scan_range'])
        if coordinates:
            try:
                nm.warp_within_70_km(coordinates[0], OVERVIEW_REGION)
            except pyautogui.PyAutoGUIException:
                logging.info(f"Could not find site coordinates: {coordinates[0]}")
                return False
            cc.broadcast_align_to(coordinates[0])
            logging.info("Warping to the site and align broadcast was sent.")
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


def engage_site_protocol(wait_for_warp_to_end: bool = True) -> None:
    # Decides whether jump through acceleration gate was successful or intercepted and act accordingly.
    if wait_for_warp_to_end:
        nm.wait_for_warp_to_end()
    hf.select_fw_tab()
    nm.jump_through_acceleration_gate()
    nm.wait_for_warp_to_end()
    hf.move_mouse_away_from_overview()

    if IS_FC:
        fc_behaviour_at_the_site()
    # else:
    #     reaction_to_possible_interception()
    else:
        fm_behaviour_at_the_site()


def fc_mission_plan() -> None:
    for _ in range(len(SYSTEMS_TO_TRAVEL_TO)):
        nm.travel_to_destination_as_fc()
        cc.await_fleet_members_to_arrive()
        if scan_site_and_warp_to_70_if_empty('scout'):
            engage_site_protocol()
        elif sig.check_probe_scanner_and_try_to_activate_site('scout'):
            if scan_site_and_warp_to_70_if_empty('scout'):
                engage_site_protocol()
        else:
            sites = sig.get_sites_within_and_outside_scan_range('scout')
            if sites['sites_outside_scan_range']:
                bounding_box = hf.bounding_box_center_coordinates(sites['sites_outside_scan_range'][1][0],
                                                                  OVERVIEW_REGION)
                nm.warp_within_70_km(bounding_box, OVERVIEW_REGION)
                time.sleep(4)
                nm.wait_for_warp_to_end()
                if not sig.make_a_short_range_three_sixty_scan():
                    engage_site_protocol(wait_for_warp_to_end=False)

    nm.travel_home()
    logging.info("Mission plan ended.")


def fm_mission_plan() -> None:
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        nm.travel_to_destination_as_fleet_member()
        cc.await_orders()
        while True:
            if cc.warp_to_member_if_enemy_is_spotted():
                break
        engage_site_protocol()
        if hf.generic_variables.destination.lower() == HOME_SYSTEM[0].lower():
            break

    nm.travel_home()
    logging.info("Mission plan ended.")

