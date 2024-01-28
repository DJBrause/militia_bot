from dataclasses import dataclass, field

import pyautogui
import time
import logging

from constants import (
    PROP_MOD, GUNS, IS_FC, OVERVIEW_REGION, REPAIRER, SYSTEMS_TO_TRAVEL_TO
)

import communication_and_coordination as cc
import helper_functions as hf
import navigation_and_movement as nm
import scanning_and_information_gathering as sig
import tests as test

import atexit

# todo killing rat at the plex
# todo GTFO if conditions are unfavorable
# todo if wingman, then warping to FC and aggroing broadcast target
# todo create status checklist to make sure all steps were completed successfully
# todo create confusion detection to check if bot is stuck
# todo think about utilizing watchlist for fleet management
# todo make readme
# todo test the shit out of this project


logging.basicConfig(filename='logfile.log',
                    level=logging.INFO,
                    filemode='w',
                    encoding='utf-8',
                    format="%(asctime)s %(levelname)s %(message)s")


@dataclass
class GenericVariables:
    unvisited_systems: list = field(default_factory=list)
    short_scan: bool = None
    dscan_confidence: float = 0.65
    destination: str = ''
    repairing: bool = False


generic_variables = GenericVariables()


def behaviour_at_the_site() -> None:
    logging.info("Awaiting site completion while checking if enemy is present.")
    start_time = time.time()
    initial_scan = True
    enemy_on_scan = False
    short_range_scan_result = None
    counter = 0
    while True:
        detected_hostiles = sig.check_overview_for_hostiles()
        if detected_hostiles:
            logging.info(f"Hostiles are present in the overview: {detected_hostiles}")
            cc.broadcast_enemy_spotted()
            engagement_protocol()

        if (time.time() - start_time) > 900:
            logging.info("15 minutes have passed. I got bored. Moving on.")
            nm.warp_to_safe_spot()
            nm.wait_for_warp_to_end()
            break

        if sig.check_if_location_secured():
            logging.info("Site capture completed. Long live the Holy Amarr!")
            break

        if initial_scan:
            logging.info("Scanning for enemy in short range.")
            short_range_scan_result = sig.make_a_short_range_three_sixty_scan()
            initial_scan = False

        elif not enemy_on_scan:
            short_range_scan_result = sig.make_a_short_range_three_sixty_scan(False)
            if short_range_scan_result:
                logging.warning(f"A ship was detected on scan: {short_range_scan_result}")
                enemy_on_scan = True

        if sig.check_if_avoided_ship_is_on_scan_result(short_range_scan_result):
            logging.info("Running away from the avoided ship.")
            nm.warp_to_safe_spot()
            break

        if enemy_on_scan:
            if counter >= 20:
                logging.info("No enemy ship jumped in. Resuming scanning.")
                enemy_on_scan = False
                counter = 0
            counter += 1

    nm.warp_to_safe_spot()
    time.sleep(4)
    nm.wait_for_warp_to_end()
    hf.clear_local_chat_content()


def engagement_protocol() -> None:
    enemy_selected = False
    start_time = None
    target_lock_lost = False
    while True:
        enemy = hf.extract_pilot_names_and_ship_types_from_screenshot()
        if enemy:
            if enemy_selected is False:
                logging.info(f"Enemy ship was detected and engaged: {enemy[0][0], enemy[0][1][1]}")
                pyautogui.moveTo(hf.bounding_box_center_coordinates(enemy[0][1][0], OVERVIEW_REGION))
                pyautogui.click()
                hf.move_mouse_away_from_overview()
                nm.approach()
                time.sleep(0.1)
                pyautogui.press(PROP_MOD)
                time.sleep(0.1)
                hf.tackle_enemy_ship(initial_run=True)
                time.sleep(0.1)
                pyautogui.press(GUNS)
                time.sleep(0.1)
                hf.target_lock()
                time.sleep(0.1)
                cc.broadcast_target(hf.bounding_box_center_coordinates(enemy[0][1][0], OVERVIEW_REGION))
                time.sleep(0.1)
                hf.launch_drones()
            if test.test_if_target_in_selected_items(enemy[0][0]):
                enemy_selected = True
            else:
                enemy_selected = False

        hf.tackle_enemy_ship()
        sig.check_health_and_decide_if_to_repair()

        if target_lock_lost and start_time is None:
            start_time = time.time()

        if not sig.check_if_target_is_locked():
            pyautogui.press(GUNS)
            time.sleep(0.1)
            logging.info("Target lock lost.")
            target_lock_lost = True
            pyautogui.moveTo(enemy)
            hf.target_lock()
            time.sleep(1)
            if start_time and (time.time() - start_time) > 60:
                nm.warp_to_safe_spot()
                break
        else:
            logging.info("Target is locked.")
            hf.order_drones_to_engage()
            start_time = None
            target_lock_lost = False

        if not enemy:
            logging.info("No enemy ship found. Resuming mission plan.")
            pyautogui.press(PROP_MOD)
            time.sleep(0.1)
            hf.return_drones_to_bay()
            time.sleep(0.1)
            nm.approach_capture_point()
            break


def scan_site_and_warp_to_70_if_empty(site: str) -> bool:
    logging.info("Scanning site in range and warping to 70km if it is empty.")
    coordinates = sig.scan_sites_within_scan_range(site)
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
    detected_hostiles = sig.check_overview_for_hostiles()
    if detected_hostiles:
        logging.info(f"Hostiles are present in the overview: {detected_hostiles}")
        cc.broadcast_enemy_spotted()
        engagement_protocol()
    nm.warp_to_safe_spot()


def engage_site_protocol(wait_for_warp_to_end: bool = True) -> None:
    # Decides whether jump through acceleration gate was successfull or intercepted and act accordingly.
    if wait_for_warp_to_end:
        time.sleep(4)
        nm.wait_for_warp_to_end()
    nm.jump_through_acceleration_gate()
    time.sleep(4)
    nm.wait_for_warp_to_end()
    if sig.check_if_in_plex():
        behaviour_at_the_site()
    else:
        reaction_to_possible_interception()


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
            bounding_box = hf.bounding_box_center_coordinates(sites['sites_outside_scan_range'][1][0], OVERVIEW_REGION)
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


def main_loop() -> None:
    hf.turn_recording_on_or_off()
    time.sleep(8)
    if IS_FC:
        fc_mission_plan()
    else:
        fm_mission_plan()


if __name__ == "__main__":
    # atexit.register(hf.turn_recording_on_or_off)
    # main_loop()
    hf.beep_x_times(1)
    # behaviour_at_the_site()
    engagement_protocol()