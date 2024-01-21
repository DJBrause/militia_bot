from dataclasses import dataclass, field

import pyautogui
import time
import logging

from constants import (
    PROP_MOD, GUNS, AMARR_SYSTEMS, IS_FC, OVERVIEW_REGION, REPAIRER
)

import communication_and_coordination as cc
import helper_functions as hf
import navigation_and_movement as nm
import scanning_and_information_gathering as sig

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
    logging.info("Arrived at the site. Awaiting for hostiles or site completion.")
    hostiles = get_hostiles_list_or_await_site_completion()
    if hostiles:
        cc.broadcast_enemy_spotted()
        target_lock_and_engage_a_hostile_ship(hostiles)


def check_health_and_decide_if_to_repair() -> None:
    health = sig.check_ship_status()
    try:
        if health[1] != '100%' and generic_variables.repairing is False:
            logging.info("Damage detected. Turning repairer on.")
            pyautogui.press(REPAIRER)
            generic_variables.repairing = True
        if health[1] == '100%' and generic_variables.repairing is True:
            logging.info("No damage detected. Turning repairer off.")
            pyautogui.press(REPAIRER)
            generic_variables.repairing = False
    except IndexError as e:
        logging.error(f"IndexError in check_health_and_decide_if_to_repair: {e}")


def target_lock_and_engage_a_hostile_ship(hostiles: list) -> None:
    default_hostile_ship = hostiles[0]
    engagement_is_on = True
    initial_loop = True
    start_time = None
    target_lock_lost = False
    while engagement_is_on:
        screenshot = hf.jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
        enemy_ship = hf.search_for_string_in_region(default_hostile_ship[1],
                                                    OVERVIEW_REGION,
                                                    screenshot,
                                                    move_mouse_to_string=True)

        if enemy_ship:
            logging.info(f'Enemy ship was detected and engaged: {enemy_ship}')
            if initial_loop:
                nm.approach()
                time.sleep(0.1)
                pyautogui.press(PROP_MOD)
                time.sleep(0.1)
                hf.tackle_enemy_ship(initial_run=True)
                time.sleep(0.1)
                pyautogui.press(GUNS)
                time.sleep(0.1)
                hf.target_lock()
                cc.broadcast_target(enemy_ship)
                initial_loop = False

        time.sleep(0.3)
        hf.tackle_enemy_ship()

        check_health_and_decide_if_to_repair()

        if target_lock_lost and start_time is None:
            start_time = time.time()

        if not sig.check_if_target_is_locked():
            pyautogui.press(GUNS)
            time.sleep(0.1)
            logging.info('Target lock lost.')
            target_lock_lost = True
            hf.target_lock()
            time.sleep(1)
            if start_time and (time.time() - start_time) > 30:
                nm.warp_to_safe_spot()
                break
        else:
            start_time = None
            target_lock_lost = False

        if not enemy_ship:
            break
    nm.warp_to_safe_spot()


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
        logging.warning(f"Hostiles are present in the overview: {detected_hostiles}")
        cc.broadcast_enemy_spotted()
        target_lock_and_engage_a_hostile_ship(detected_hostiles)
    nm.warp_to_safe_spot()


def engage_site_protocol(wait_for_warp_to_end: bool = True) -> None:
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
    for _ in range(len(AMARR_SYSTEMS)):
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


# todo This function got bloated. Try to refactor it.
def get_hostiles_list_or_await_site_completion() -> list:
    initial_scan = True
    enemy_on_scan = False
    short_range_scan_result = []
    counter = 0
    start_time = time.time()
    while True:
        if (time.time() - start_time) > 900:
            logging.warning('15 minutes have passed. I got bored. Moving on.')
            nm.warp_to_safe_spot()
            nm.wait_for_warp_to_end()
            return []
        detected_hostiles = sig.check_overview_for_hostiles()
        if detected_hostiles:
            logging.warning(f'Hostiles are present in the overview: {detected_hostiles}')
            return detected_hostiles
        if initial_scan:
            short_range_scan_result = sig.make_a_short_range_three_sixty_scan()
            initial_scan = False
        elif not enemy_on_scan:
            short_range_scan_result = sig.make_a_short_range_three_sixty_scan(False)
            if short_range_scan_result:
                logging.warning(f'A ship was detected on scan: {short_range_scan_result}')
                enemy_on_scan = True
        if sig.check_if_avoided_ship_is_on_scan_result(short_range_scan_result):
            nm.warp_to_safe_spot()
            return []
        if sig.check_if_location_secured():
            logging.info('Site capture completed. Long live the Holy Amarr!')
            nm.warp_to_safe_spot()
            nm.wait_for_warp_to_end()
            hf.clear_local_chat_content()
            return []
        if enemy_on_scan:
            if counter >= 30:
                enemy_on_scan = False
                counter = 0
            counter += 1


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
    behaviour_at_the_site()
