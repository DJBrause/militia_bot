from dataclasses import dataclass

import pyautogui
import time

import logging

from constants import (
    PROP_MOD, GUNS, AMARR_SYSTEMS, FLEET_MEMBERS_COUNT, IS_FC, MAX_NUMBER_OF_ATTEMPTS,
    OVERVIEW_REGION
)

import communication_and_coordination as cc
import helper_functions as hf
import navigation_and_movement as nm
import scanning_and_information_gathering as sig


# todo killing rat at the plex
# todo GTFO if conditions are unfavorable
# todo if wingman, then warping to FC and aggroing broadcast target
# todo create status checklist to make sure all steps were completed successfully
# todo create confusion detection to check if bot is stuck
# todo think about utilizing watchlist for fleet management
# todo make readme
# todo test the shit out of this project


@dataclass
class GenericVariables:
    unvisited_systems: list
    dscan_confidence: float = 0.65
    destination: str = ''


generic_variables = GenericVariables(unvisited_systems=[])


def behaviour_at_the_site() -> None:
    hostiles = get_hostiles_list_or_await_site_completion()
    if len(hostiles) > 0:
        cc.broadcast_enemy_spotted()
        if not target_lock_and_engage_a_hostile_ship(hostiles):
            nm.warp_to_safe_spot()


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
            logging.info(f'Enemy ship was detected: {enemy_ship}')
            nm.approach()
            time.sleep(0.1)
            cc.broadcast_target(enemy_ship)

        if initial_loop:
            pyautogui.press(PROP_MOD)
            hf.tackle_enemy_ship(initial_run=True)
            pyautogui.press(GUNS)
            for _ in range(2):
                hf.target_lock()
            time.sleep(1)
            initial_loop = False
        time.sleep(0.3)
        hf.tackle_enemy_ship()

        if target_lock_lost and start_time is None:
            start_time = time.time()

        if not sig.check_if_target_is_locked():
            pyautogui.press(GUNS)
            logging.info('Target lock lost')
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


def fc_mission_plan() -> None:
    for _ in range(len(AMARR_SYSTEMS)):
        nm.travel_to_destination_as_fc()
        cc.await_fleet_members_to_arrive()
        target_coordinates = sig.scan_sites_within_scan_range('scout')
        if target_coordinates:
            nm.warp_within_70_km(target_coordinates, OVERVIEW_REGION)
            cc.broadcast_align_to(target_coordinates)
            time.sleep(4)
            for _ in range(MAX_NUMBER_OF_ATTEMPTS):
                if not sig.check_if_in_warp():
                    break
            nm.jump_through_acceleration_gate()
            behaviour_at_the_site()
            if sig.check_insurance():
                break
        else:
            if sig.check_probe_scanner_for_sites_and_warp_to_70('scout'):
                time.sleep(4)
                for _ in range(MAX_NUMBER_OF_ATTEMPTS):
                    if not sig.check_if_in_warp():
                        break
                nm.jump_through_acceleration_gate()
                behaviour_at_the_site()
                if sig.check_insurance():
                    break
    nm.travel_home()


def wait_for_fleet_members_to_join_and_broadcast_destination() -> None:
    broadcast_count = 0
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if sig.check_for_in_position_broadcast():
            cc.broadcast_destination()
            broadcast_count += 1
        if broadcast_count == FLEET_MEMBERS_COUNT:
            break
        time.sleep(3)


# todo This function got bloated. Try to refactor it.
def get_hostiles_list_or_await_site_completion() -> list:
    initial_scan = True
    enemy_on_scan = False
    short_range_scan_result = []
    counter = 0
    start_time = time.time()
    while True:
        if (time.time() - start_time) > 900:
            logging.warning('15 minutes passed, I got bored. Moving on.')
            nm.warp_to_safe_spot()
            time.sleep(4)
            for _ in range(MAX_NUMBER_OF_ATTEMPTS):
                if not sig.check_if_in_warp():
                    break
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
            logging.info('A ship that is present in the avoid list was detected short scan')
            nm.warp_to_safe_spot()
            return []
        if sig.check_if_location_secured():
            logging.info('Site capture completed. Long live the Holy Amarr!')
            nm.warp_to_safe_spot()
            time.sleep(4)
            for _ in range(MAX_NUMBER_OF_ATTEMPTS):
                if not sig.check_if_in_warp():
                    break
            hf.clear_local_chat_content()
            return []
        if enemy_on_scan:
            if counter >= 30:
                enemy_on_scan = False
                counter = 0
            counter += 1


def main_loop() -> None:
    hf.turn_recording_on_or_off()
    time.sleep(8)
    if IS_FC:
        fc_mission_plan()
    hf.turn_recording_on_or_off()


if __name__ == "__main__":
    # main_loop()
    hf.test_check_region(OVERVIEW_REGION)
