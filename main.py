from dataclasses import dataclass

import pyautogui
import time

import logging

from constants import (PROP_MOD, GUNS, AMARR_SYSTEMS, FLEET_MEMBERS_COUNT, IS_FC, MAX_NUMBER_OF_ATTEMPTS,
                       OVERVIEW_REGION)

from communication_and_coordination import (broadcast_enemy_spotted, broadcast_target, await_fleet_members_to_arrive,
                                            broadcast_align_to, broadcast_destination, form_fleet)

from helper_functions import (jpg_screenshot_of_the_selected_region, tackle_enemy_ship, target_lock,
                              turn_recording_on_or_off, clear_local_chat_content, search_for_string_in_region)

from navigation_and_movement import (warp_within_70_km, warp_to_safe_spot, approach, travel_to_destination_as_fc,
                                     jump_through_acceleration_gate, travel_home, )

from scanning_and_information_gathering import (check_if_target_is_locked, scan_sites_within_scan_range,
                                                check_insurance, check_if_in_warp, check_for_in_position_broadcast,
                                                check_probe_scanner_for_sites_and_warp_to_70,
                                                check_overview_for_hostiles, make_a_short_range_three_sixty_scan,
                                                check_if_avoided_ship_is_on_scan_result, check_if_location_secured)


# todo killing rat at the plex
# todo GTFO if conditions are unfavorable
# todo if wingman, then warping to FC and aggroing broadcast target
# todo create status checklist to make sure all steps were completed successfully
# todo create confusion detection to check if bot is stuck
# todo think about utilizing watchlist for fleet management
# todo refactor code - split code into several files
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
        broadcast_enemy_spotted()
        if not target_lock_and_engage_a_hostile_ship(hostiles):
            warp_to_safe_spot()


def target_lock_and_engage_a_hostile_ship(hostiles: list) -> None:
    default_hostile_ship = hostiles[0]
    engagement_is_on = True
    initial_loop = True
    start_time = None
    target_lock_lost = False
    while engagement_is_on:
        screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
        enemy_ship = search_for_string_in_region(default_hostile_ship[1],
                                                 OVERVIEW_REGION,
                                                 screenshot,
                                                 move_mouse_to_string=True)
        if enemy_ship:
            logging.info(f'Enemy ship was detected: {enemy_ship}')
            approach()
            time.sleep(0.1)
            broadcast_target(enemy_ship)

        if initial_loop:
            pyautogui.press(PROP_MOD)
            tackle_enemy_ship(initial_run=True)
            pyautogui.press(GUNS)
            for _ in range(2):
                target_lock()
            time.sleep(1)
            initial_loop = False
        time.sleep(0.3)
        tackle_enemy_ship()

        if target_lock_lost and start_time is None:
            start_time = time.time()

        if not check_if_target_is_locked():
            pyautogui.press(GUNS)
            logging.info('Target lock lost')
            target_lock_lost = True
            target_lock()
            time.sleep(1)
            if start_time and (time.time() - start_time) > 30:
                warp_to_safe_spot()
                break
        else:
            start_time = None
            target_lock_lost = False

        if not enemy_ship:
            break


def fc_mission_plan() -> None:
    for _ in range(len(AMARR_SYSTEMS)):
        travel_to_destination_as_fc()
        await_fleet_members_to_arrive()
        target_coordinates = scan_sites_within_scan_range('scout')
        if target_coordinates:
            warp_within_70_km(target_coordinates, OVERVIEW_REGION)
            broadcast_align_to(target_coordinates)
            time.sleep(4)
            for _ in range(MAX_NUMBER_OF_ATTEMPTS):
                if not check_if_in_warp():
                    break
            jump_through_acceleration_gate()
            behaviour_at_the_site()
            if check_insurance():
                break
        else:
            if check_probe_scanner_for_sites_and_warp_to_70('scout'):
                time.sleep(4)
                for _ in range(MAX_NUMBER_OF_ATTEMPTS):
                    if not check_if_in_warp():
                        break
                jump_through_acceleration_gate()
                behaviour_at_the_site()
                if check_insurance():
                    break
    travel_home()


def wait_for_fleet_members_to_join_and_broadcast_destination() -> None:
    broadcast_count = 0
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if check_for_in_position_broadcast():
            broadcast_destination()
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
            warp_to_safe_spot()
            time.sleep(4)
            for _ in range(MAX_NUMBER_OF_ATTEMPTS):
                if not check_if_in_warp():
                    break
            return []
        detected_hostiles = check_overview_for_hostiles()
        if detected_hostiles:
            logging.warning(f'Hostiles are present in the overview: {detected_hostiles}')
            return detected_hostiles
        if initial_scan:
            short_range_scan_result = make_a_short_range_three_sixty_scan()
            initial_scan = False
        elif not enemy_on_scan:
            short_range_scan_result = make_a_short_range_three_sixty_scan(False)
            if short_range_scan_result:
                logging.warning(f'A ship was detected on scan: {short_range_scan_result}')
                enemy_on_scan = True
        if check_if_avoided_ship_is_on_scan_result(short_range_scan_result):
            logging.info('A ship that is present in the avoid list was detected short scan')
            warp_to_safe_spot()
            return []
        if check_if_location_secured():
            logging.info('Site capture completed. Long live the Holy Amarr!')
            warp_to_safe_spot()
            time.sleep(4)
            for _ in range(MAX_NUMBER_OF_ATTEMPTS):
                if not check_if_in_warp():
                    break
            clear_local_chat_content()
            return []
        if enemy_on_scan:
            if counter >= 30:
                enemy_on_scan = False
                counter = 0
            counter += 1


def main_loop() -> None:
    turn_recording_on_or_off()
    time.sleep(8)
    if IS_FC:
        fc_mission_plan()
    turn_recording_on_or_off()


if __name__ == "__main__":
    # main_loop()
    form_fleet()
