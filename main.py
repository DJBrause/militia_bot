from typing import Tuple, List, Union
from dataclasses import dataclass

import pyautogui
import io
import time

import pyscreeze
from easyocr import Reader
import keyboard
from PIL import Image
import winsound
import random

from constants import *

import logging

# todo killing rat at the plex
# todo GTFO if conditions are unfavorable
# todo if wingman, then warping to FC and aggroing broadcast target
# todo create status checklist to make sure all steps were completed successfully
# todo create confusion detection to check if bot is stuck
# todo think about utilizing watchlist for fleet management

ocr_reader = Reader(['en'])


@dataclass
class GenericVariables:
    unvisited_systems: list
    dscan_confidence: float = 0.65
    destination: str = ''


generic_variables = GenericVariables(unvisited_systems=[])


def region_selector():
    beep_x_times(1)
    x, y = 0, 0
    while True:
        if keyboard.is_pressed('ctrl'):
            x, y = pyautogui.position()
            z = pyautogui.pixel(x, y)
            logging.info(f"{x, y, z}")
            beep_x_times(1)

        if keyboard.is_pressed('alt'):
            x_, y_ = pyautogui.position()
            logging.info(f"{x}, {y}, {x_ - x}, {y_ - y}")
            beep_x_times(3)

        if keyboard.is_pressed('shift'):
            beep_x_times(2)
            break


def search_for_string_in_region(searched_string: str, region: Tuple, image_file: Image,
                                move_mouse_to_string: bool = False, selected_result: int = 0, debug: bool = False) \
        -> Union[bool, list]:
    results = ocr_reader.readtext(image_file)
    if debug:
        print(results)
    try:
        matching_results = []
        for result in results:
            if searched_string.lower() in result[1].lower():
                matching_results.append(result)
        middle_of_bounding_box = bounding_box_center_coordinates(matching_results[selected_result][0],
                                                                 region=region)
        if move_mouse_to_string:
            pyautogui.moveTo(middle_of_bounding_box)
        return middle_of_bounding_box
    except TypeError:
        return False
    except IndexError:
        return False


def jpg_screenshot_of_the_selected_region(region: Tuple) -> Image:
    screenshot = pyautogui.screenshot(region=region)
    temp_image = io.BytesIO()
    screenshot.save(temp_image, format="JPEG")
    temp_image.seek(0)
    screenshot_jpeg = Image.open(temp_image)
    return screenshot_jpeg


def bounding_box_center_coordinates(bounding_box: List, region: Tuple) -> [int, int]:
    x_min = bounding_box[0][0]
    y_min = bounding_box[0][1]
    x_max = bounding_box[1][0]
    y_max = bounding_box[2][1]
    region_x = region[0]
    region_y = region[1]
    x_center = (x_min + x_max) / 2 + region_x
    y_center = (y_min + y_max) / 2 + region_y
    return x_center, y_center


def get_and_return_system_name(region: Tuple) -> list:
    screenshot_of_top_left_corner = jpg_screenshot_of_the_selected_region(region)
    results = ocr_reader.readtext(screenshot_of_top_left_corner)
    return results


def beep_x_times(x: int) -> None:
    for _ in range(x):
        winsound.Beep(frequency=1500, duration=100)
        time.sleep(0.1)


def notification_beep() -> None:
    winsound.Beep(frequency=2000, duration=100)
    winsound.Beep(frequency=3000, duration=100)
    winsound.Beep(frequency=2000, duration=100)


def test_check_region(region: Tuple) -> list:
    overview_and_selected_item_screenshot = jpg_screenshot_of_the_selected_region(region)
    test_result = ocr_reader.readtext(overview_and_selected_item_screenshot)
    return test_result


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


def check_if_target_is_outside_range() -> bool:
    too_far_away_message = ['the', 'target', 'too', 'far', 'away', 'within']
    region_screenshot = jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    results = ocr_reader.readtext(region_screenshot)
    filtered_strings = [item for sublist in results for item in sublist if isinstance(item, str)]
    for word in too_far_away_message:
        if word in filtered_strings:
            return True
    return False


def check_if_within_targeting_range() -> bool:
    try:
        target_is_lockable = pyautogui.locateCenterOnScreen(LOCK_TARGET_ICON, confidence=0.99,
                                                            region=SELECTED_ITEM_REGION)
        if target_is_lockable is not None:
            return True
    except pyautogui.ImageNotFoundException:
        return False


def target_lock() -> None:
    with pyautogui.hold('ctrl'):
        pyautogui.click()


def turn_recording_on_or_off() -> None:
    pyautogui.hotkey('alt', 'f9', interval=0.1)


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


def check_if_scrambler_is_operating() -> bool:
    try:
        if pyautogui.locateCenterOnScreen(SCRAMBLER_ON_ICON, grayscale=False, confidence=DEFAULT_CONFIDENCE,
                                          region=TARGETS_REGION):
            return True
        return False
    except pyautogui.ImageNotFoundException:
        pass


def check_if_webifier_is_operating() -> bool:
    try:
        if pyautogui.locateCenterOnScreen(WEBIFIER_ON_ICON, grayscale=False, confidence=DEFAULT_CONFIDENCE,
                                          region=TARGETS_REGION):
            return True
    except pyautogui.ImageNotFoundException:
        return False


def move_mouse_away_from_overview() -> None:
    pyautogui.moveTo(x=75, y=45)


def warp_to_safe_spot() -> None:
    move_mouse_away_from_overview()
    pyautogui.rightClick()
    time.sleep(0.1)
    screenshot = jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    search_for_string_in_region('loc', TOP_LEFT_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.1)
    screenshot = jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    for _ in range(5):
        search_for_string_in_region('spo', TOP_LEFT_REGION, screenshot, move_mouse_to_string=True)
        pyautogui.click()
        break


def clear_broadcast_history() -> None:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    search_for_string_in_region('clear', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def clear_local_chat_content() -> bool:
    try:
        more_icon = pyautogui.locateCenterOnScreen(MORE_ICON,
                                                   grayscale=False,
                                                   confidence=DEFAULT_CONFIDENCE,
                                                   region=LOCAL_REGION)
        if more_icon:
            pyautogui.moveTo(more_icon)
            pyautogui.click()
            time.sleep(0.2)
            screenshot = jpg_screenshot_of_the_selected_region(LOCAL_REGION)
            search_for_string_in_region('clear', LOCAL_REGION, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            return True
        return False
    except pyautogui.ImageNotFoundException:
        return False


def target_broadcast_ship(region: Tuple) -> None:
    screenshot = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('target', region, screenshot, move_mouse_to_string=True)
    for _ in range(3):
        pyautogui.keyDown('ctrl')
        pyautogui.click()
        pyautogui.keyUp('ctrl')


def undock():
    pyautogui.hotkey('ctrl', 'shift', 'x', interval=0.1)
    move_mouse_away_from_overview()


def approach() -> None:
    with pyautogui.hold('q'):
        pyautogui.click()


def orbit_target() -> None:
    with pyautogui.hold('w'):
        pyautogui.click()


def check_if_in_warp() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(CAPACITOR_REGION)
    if search_for_string_in_region('wa', CAPACITOR_REGION, screenshot):
        return True
    return False


def set_destination_home() -> None:
    pyautogui.hotkey('alt', 'a', interval=0.1)
    screenshot = jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    search_for_string_in_region('character', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    screenshot = jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    search_for_string_in_region('home station', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    screenshot = jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    search_for_string_in_region('set destination', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    pyautogui.hotkey('alt', 'a', interval=0.1)


def warp_to_scout_combat_site(region: Tuple) -> None:
    select_probe_scanner()
    screenshot_of_scanner = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('scout', SCANNER_REGION, screenshot_of_scanner, True)
    pyautogui.rightClick()
    screenshot_of_scanner_with_warp_to_option = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('to within', SCANNER_REGION, screenshot_of_scanner_with_warp_to_option, True)
    pyautogui.click()


def jump_through_acceleration_gate() -> None:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    search_for_string_in_region('acceleration',
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
            move_mouse_away_from_overview()
            return True
    except pyautogui.ImageNotFoundException:
        return False


def travel_to_destination() -> None:
    for _ in range(MAX_EXPECTED_TRAVEL_DISTANCE):
        if not jump_through_gate_to_destination():
            select_gates_only_tab()
            if not jump_through_gate_to_destination():
                select_fw_tab()
                break

        for _ in range(100):
            time.sleep(3)
            if not check_if_in_warp():
                beep_x_times(2)
                break
            time.sleep(1)
        time.sleep(12)
    notification_beep()


def dock_at_station() -> bool:
    stations = [DESTINATION_HOME_STATION, DESTINATION_STATION]
    select_fw_tab()
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


def open_or_close_notepad() -> None:
    pyautogui.hotkey('ctrl', 'n', interval=0.1)


def choose_system_to_travel_to(systems: list) -> str:
    if len(generic_variables.unvisited_systems) == 0:
        random_system = random.choice(systems)
        unvisited_systems = systems
        unvisited_systems.remove(random_system)
        return random_system
    random_system = random.choice(generic_variables.unvisited_systems)
    generic_variables.unvisited_systems.remove(random_system)
    return random_system


def check_if_docked() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if search_for_string_in_region('undock', OVERVIEW_REGION, screenshot, move_mouse_to_string=True):
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


def broadcast_destination() -> bool:
    if generic_variables.destination is not None:
        open_or_close_notepad()
        screenshot = jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
        search_for_string_in_region(generic_variables.destination,
                                    TOP_LEFT_REGION,
                                    screenshot,
                                    move_mouse_to_string=True)
        pyautogui.rightClick()
        screenshot = jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
        broadcast = search_for_string_in_region('broadcast',
                                                TOP_LEFT_REGION,
                                                screenshot,
                                                move_mouse_to_string=True)
        if broadcast:
            time.sleep(0.3)
            pyautogui.click()
        open_or_close_notepad()
        print(f'Destination broadcast to {generic_variables.destination} sent')
        return True
    return False


def set_destination(systems: list) -> bool:
    if generic_variables.destination and generic_variables.destination in systems:
        systems.remove(generic_variables.destination)
    select_gates_only_tab()
    move_mouse_away_from_overview()
    time.sleep(0.5)
    open_or_close_notepad()
    time.sleep(4)
    generic_variables.destination = choose_system_to_travel_to(systems)
    screenshot = jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    destination_system = search_for_string_in_region(generic_variables.destination,
                                                     TOP_LEFT_REGION,
                                                     screenshot,
                                                     move_mouse_to_string=True)
    if destination_system:
        time.sleep(0.3)
        pyautogui.rightClick()
        time.sleep(0.3)
    else:

        open_or_close_notepad()
        return False
    screenshot = jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
    destination_confirmation = search_for_string_in_region('destination',
                                                           TOP_LEFT_REGION,
                                                           screenshot,
                                                           move_mouse_to_string=True)
    if destination_confirmation:
        pyautogui.click()
        pyautogui.moveTo(destination_system)
    open_or_close_notepad()
    return True


def create_fleet_advert() -> None:
    select_fleet_tab()
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    search_for_string_in_region('advert', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    search_for_string_in_region('create', SCANNER_REGION, screenshot, selected_result=1, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(1)
    screenshot = jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
    search_for_string_in_region('submit', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def select_broadcasts() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if search_for_string_in_region('cast', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        return True
    else:
        return False


def join_existing_fleet() -> None:
    pyautogui.hotkey('ctrl', 'alt', 'f', interval=0.1)
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    search_for_string_in_region('ind', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.2)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        search_for_string_in_region('ind', SCANNER_REGION, screenshot, selected_result=2, move_mouse_to_string=True)
        pyautogui.click()
        time.sleep(0.2)
        screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
        if search_for_string_in_region('uncanny', SCANNER_REGION, screenshot, move_mouse_to_string=True):
            pyautogui.rightClick()
            time.sleep(0.2)
            screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
            search_for_string_in_region('join', SCANNER_REGION, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            time.sleep(0.2)
            screenshot = jpg_screenshot_of_the_selected_region(MID_TO_TOP_REGION)
            search_for_string_in_region('yes', MID_TO_TOP_REGION, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            print('fleet joined')
            return
        else:
            time.sleep(3)


def form_fleet() -> None:
    pyautogui.hotkey('ctrl', 'alt', 'f', interval=0.1)
    time.sleep(0.2)
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    form_fleet_button = search_for_string_in_region('form fleet', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    if form_fleet_button:
        pyautogui.click()
        move_mouse_away_from_overview()
    else:
        results = ocr_reader.readtext(screenshot)
        for result in results:
            searched_string = 'fleet'
            if searched_string.lower() in result[1].lower():
                middle_of_bounding_box = bounding_box_center_coordinates(result[0], region=SCANNER_REGION)
                pyautogui.click(middle_of_bounding_box)
                screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
            if search_for_string_in_region('form fleet', SCANNER_REGION, screenshot, move_mouse_to_string=True):
                pyautogui.click()
                move_mouse_away_from_overview()
    create_fleet_advert()
    select_broadcasts()


def select_gates_only_tab() -> None:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    search_for_string_in_region('gates', OVERVIEW_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def select_fw_tab() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if search_for_string_in_region('fw', OVERVIEW_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        return True
    return False


def travel_to_destination_as_fc() -> None:
    if check_if_docked():
        if not check_if_in_fleet():
            form_fleet()
            time.sleep(0.1)
        undock()
        time.sleep(20)
    else:
        if not check_if_in_fleet(is_docked=False):
            form_fleet()
            time.sleep(0.1)
    # cannot broadcast destination while docked
    set_destination(AMARR_SYSTEMS)

    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if select_fleet_tab():
            break
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if select_broadcasts():
            break
    wait_for_fleet_members_to_join_and_broadcast_destination()
    if generic_variables.destination:
        for _ in range(MAX_NUMBER_OF_ATTEMPTS):
            if not check_if_destination_system_was_reached(generic_variables.destination,
                                                           SCANNER_REGION):
                travel_to_destination()
            else:
                break
        warp_to_safe_spot()
        time.sleep(4)
        for _ in range(MAX_NUMBER_OF_ATTEMPTS):
            if not check_if_in_warp():
                return


def align_to(target: list) -> None:
    pyautogui.moveTo(target)
    with pyautogui.hold('a'):
        pyautogui.click()


def travel_home(fleet_up: bool = False) -> None:
    if fleet_up:
        form_fleet()
    set_destination_home()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if not check_if_destination_system_was_reached(HOME_SYSTEM, SCANNER_REGION):
            travel_to_destination()
        else:
            break
    dock_at_station()


def travel_to_destination_as_fleet_member() -> None:
    join_existing_fleet()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if select_broadcasts():
            break
        else:
            print('cannot locate broadcasts')
            time.sleep(2)
    if check_if_docked():
        undock()
        time.sleep(20)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        select_fleet_tab()
    broadcast_in_position()
    time.sleep(2)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if set_destination_from_broadcast():
            break

    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if not check_if_destination_system_was_reached(generic_variables.destination, SCANNER_REGION):
            travel_to_destination()
        else:
            break
    warp_to_safe_spot()
    time.sleep(4)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if not check_if_in_warp():
            break
    broadcast_in_position()


def set_destination_from_broadcast() -> bool:
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
        for system in MINMATAR_SYSTEMS:
            if search_for_string_in_region(system, SCANNER_REGION, screenshot, move_mouse_to_string=True):
                generic_variables.destination = system
                pyautogui.rightClick()
                time.sleep(0.1)
                screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
                search_for_string_in_region('dest', SCANNER_REGION, screenshot, move_mouse_to_string=True)
                pyautogui.click()
                return True
            time.sleep(2)
    return False


def broadcast_current_location() -> None:
    pyautogui.press(',')


def select_fleet_tab() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if search_for_string_in_region('eet', SCANNER_REGION, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        return True
    return False


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


def check_dscan_result() -> list:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    results = ocr_reader.readtext(screenshot)
    frigate_on_scan = [f for f in ALL_FRIGATES for r in results if f == r[1]]
    return frigate_on_scan


def check_if_in_fleet(is_docked: bool = True) -> bool:
    if not is_docked:
        select_fleet_tab()
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if search_for_string_in_region('respawn', SCANNER_REGION, screenshot):
        return True
    return False


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


def broadcast_in_position() -> None:
    pyautogui.press('.')


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


def check_for_in_position_broadcast() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    if search_for_string_in_region('position', SCANNER_REGION, screenshot):
        clear_broadcast_history()
        return True
    return False


def wait_for_fleet_members_to_join_and_broadcast_destination() -> None:
    broadcast_count = 0
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if check_for_in_position_broadcast():
            broadcast_destination()
            broadcast_count += 1
        if broadcast_count == FLEET_MEMBERS_COUNT:
            break
        time.sleep(3)


def warp_within_70_km(target: list, region: Tuple) -> bool:
    pyautogui.moveTo(target)
    pyautogui.rightClick()
    screenshot = jpg_screenshot_of_the_selected_region(region)
    if search_for_string_in_region('ithin (', region, screenshot,
                                   move_mouse_to_string=True):
        screenshot = jpg_screenshot_of_the_selected_region(region)
        search_for_string_in_region('ithin 70', region, screenshot,
                                    move_mouse_to_string=True)
        pyautogui.click()
        return True
    elif search_for_string_in_region('ithin', region, screenshot,
                                     move_mouse_to_string=True, selected_result=1):
        screenshot = jpg_screenshot_of_the_selected_region(region)
        search_for_string_in_region('ithin 70', region, screenshot,
                                    move_mouse_to_string=True)
        pyautogui.click()
        return True
    return False


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


def check_for_station_in_system() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if search_for_string_in_region('station', OVERVIEW_REGION, screenshot):
        return True
    return False


def gtfo() -> None:
    warp_to_safe_spot()

    time.sleep(4)
    for _ in MAX_NUMBER_OF_ATTEMPTS:
        if not check_if_in_warp():
            break
    travel_home()


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


def warp_to_member_if_enemy_is_spotted() -> None:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    broadcast = search_for_string_in_region('spotted', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    if broadcast:
        warp_within_70_km(broadcast, OVERVIEW_REGION)


def broadcast_align_to(target: list) -> None:
    with pyautogui.hold('alt'):
        with pyautogui.hold('v'):
            pyautogui.moveTo(target)
            pyautogui.click()
    clear_broadcast_history()


def broadcast_enemy_spotted() -> None:
    pyautogui.press('z')
    clear_broadcast_history()


def await_orders() -> None:
    select_fleet_tab()
    select_broadcasts()
    while True:
        if check_for_broadcast_and_align():
            break
        time.sleep(1)


def await_fleet_members_to_arrive() -> None:
    fleet_members_to_arrive = FLEET_MEMBERS_COUNT
    select_broadcasts()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if check_for_in_position_broadcast():
            fleet_members_to_arrive -= 1
        if fleet_members_to_arrive == 0:
            return
        time.sleep(2)


def scan_for_short_range_threats() -> bool:
    if make_a_short_range_three_sixty_scan():
        return True
    return False


def check_if_location_secured() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(LOCAL_REGION)
    if search_for_string_in_region('secure', LOCAL_REGION, screenshot):
        return True
    return False


def check_if_avoided_ship_is_on_scan_result(scan_result: list) -> bool:
    avoided_ship_on_scan = [ship for ship in scan_result for avoided_ship in AVOID if ship == avoided_ship]
    print(avoided_ship_on_scan)
    if len(avoided_ship_on_scan) > 0:
        return True
    return False


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


def stop_ship() -> None:
    with pyautogui.hold('ctrl'):
        pyautogui.press('space')


def tackle_enemy_ship(initial_run: bool = False) -> None:
    if initial_run:
        if SCRAMBLER_EQUIPPED:
            pyautogui.press(SCRAM)
        if WEBIFIER_EQUIPPED:
            pyautogui.press(WEB)
    elif SCRAMBLER_EQUIPPED and not check_if_scrambler_is_operating():
        pyautogui.press(SCRAM)
    elif WEBIFIER_EQUIPPED and not check_if_webifier_is_operating():
        pyautogui.press(WEB)


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


def open_or_close_mail() -> None:
    with pyautogui.hold('alt'):
        pyautogui.press('i')


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


# returns coordinates of the scanned site if scan results were empty (no ship was detected in that location)
def scan_sites_within_scan_range(scanned_site_type: str) -> list:
    scan_results = scan_targets_within_and_outside_scan_range(scanned_site_type)
    if scan_results['targets_within_scan_range']:
        target_coordinates = [bounding_box_center_coordinates(target[1][0], OVERVIEW_REGION) for target in
                              scan_results['targets_within_scan_range'] if len(scan_target_within_range(target)) == 0]
        return target_coordinates
    return []


def broadcast_target(target_coordinates: list) -> None:
    pyautogui.moveTo(target_coordinates)
    pyautogui.rightClick()
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    search_for_string_in_region('broadcast', OVERVIEW_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def behaviour_at_the_site() -> None:
    hostiles = get_hostiles_list_or_await_site_completion()
    if len(hostiles) > 0:
        broadcast_enemy_spotted()
        if not target_lock_and_engage_a_hostile_ship(hostiles):
            warp_to_safe_spot()


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


def main_loop() -> None:
    turn_recording_on_or_off()
    time.sleep(8)
    if IS_FC:
        fc_mission_plan()
    turn_recording_on_or_off()


if __name__ == "__main__":
    # main_loop()
    form_fleet()