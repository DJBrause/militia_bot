import pyautogui
import time
import logging

from constants import (
    PROP_MOD, GUNS, OVERVIEW_REGION, SYSTEMS_TO_TRAVEL_TO, REPAIRER_EQUIPPED,
)

import communication_and_coordination as cc
import helper_functions as hf
import navigation_and_movement as nm
import scanning_and_information_gathering as sig
import tests as test


def behaviour_at_the_site() -> None:
    logging.info("Awaiting site completion while checking if enemy is present.")
    start_time = time.time()
    initial_scan = True
    enemy_on_scan = False
    short_range_scan_result = None
    counter = 0
    while True:
        time.sleep(0.1)
        while True:
            detected_hostiles = sig.check_overview_for_hostiles()
            if detected_hostiles:
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

        rat = sig.check_overview_for_rats()
        if rat:
            reaction_to_rat_presence(rat)

        if hf.generic_variables.graphics_removed:
            logging.info("No rat or hostile present. Restoring graphics.")
            hf.remove_graphics()
            hf.generic_variables.graphics_removed = False

        if initial_scan:
            logging.info("Making a short range scan.")
            short_range_scan_result = sig.make_a_short_range_three_sixty_scan()
            if short_range_scan_result:
                logging.warning(f"A ship was detected on scan: {short_range_scan_result}")
                enemy_on_scan = True
            initial_scan = False

        elif not enemy_on_scan:
            logging.info("Making a short range scan.")
            short_range_scan_result = sig.make_a_short_range_three_sixty_scan(False)
            if short_range_scan_result:
                logging.warning(f"A ship was detected on scan: {short_range_scan_result}")
                enemy_on_scan = True

        if sig.check_if_avoided_ship_is_on_scan_result(short_range_scan_result):
            logging.info("Running away from the avoided ship.")
            break

        if enemy_on_scan:
            if counter >= 20:
                logging.info("No enemy ship jumped in. Resuming scanning.")
                enemy_on_scan = False
                counter = 0
            counter += 1

        nm.approach_capture_point()

        if sig.check_if_location_secured():
            logging.info("Site capture completed. Long live the Holy Amarr!")
            break

        if (time.time() - start_time) > 900:
            logging.info("15 minutes have passed. I got bored. Moving on.")
            nm.warp_to_safe_spot()
            nm.wait_for_warp_to_end()
            break

    nm.warp_to_safe_spot()
    nm.wait_for_warp_to_end()
    hf.clear_local_chat_content()


def reaction_to_rat_presence(rat):
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
    screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if hf.search_for_string_in_region(name, OVERVIEW_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        time.sleep(0.1)
        if test.test_if_target_in_selected_items(name):
            nm.approach()
            if not hf.generic_variables.prop_module_on:
                time.sleep(0.1)
                pyautogui.press(PROP_MOD)
                hf.generic_variables.prop_module_on = True
            time.sleep(0.1)
            hf.move_mouse_away_from_overview()
            return True
    else:
        logging.info("Enemy is no longer present in the overview.")
        return False


def attempt_to_target_lock_the_enemy(name: str) -> bool:
    logging.info(f"Attempting to acquire target lock on: {name}")
    if not hf.target_lock_using_selected_item(name):
        new_screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
        if hf.search_for_string_in_region(name, OVERVIEW_REGION, new_screenshot, move_mouse_to_string=True):
            if hf.target_lock_using_overview(name):
                hf.move_mouse_away_from_overview()
                return True
            hf.move_mouse_away_from_overview()
            return False
        else:
            logging.info("Enemy is no longer present in the overview.")
            return False
    return True


def engagement_protocol(name: str) -> bool:
    logging.info("Engagement protocol is active.")
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


def maintain_engagement(name: str) -> None:
    logging.info("Maintaining engagement.")
    while True:
        if sig.check_if_target_is_locked():
            handle_locked_target()
        else:
            if not handle_unlocked_target(name):
                return
        if REPAIRER_EQUIPPED:
            sig.check_health_and_decide_if_to_repair()


def handle_locked_target() -> None:
    logging.info("Handling a locked target.")
    nm.approach()
    time.sleep(0.1)
    hf.tackle_enemy_ship()


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
    nm.jump_through_acceleration_gate()
    nm.wait_for_warp_to_end()
    hf.move_mouse_away_from_overview()

    behaviour_at_the_site()
    # else:
    #     reaction_to_possible_interception()


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
    nm.travel_to_destination_as_fleet_member()
    cc.check_for_broadcast_and_align()
    while True:
        nm.warp_to_member_if_enemy_is_spotted()