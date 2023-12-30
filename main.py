from typing import Tuple, List, Union

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

# todo killing rat at the plex
# todo GTFO if conditions are unfavorable
# todo if FC - sending broadcasts
# todo if wingman, then warping to FC and aggroing broadcast target
# todo create a listener on FC side that will detect 'in position' broadcast to broadcast destination in return
# todo create status checklist to make sure all steps were completed successfully
# todo create confusion detection to check if bot is stuck

# todo destination as str variable is set only for FC. How to bypass it for fleet member?


ocr_reader = Reader(['en'])
dscan_confidence = 0.65
destination = ''


def region_selector():
    beep_x_times(1)
    x, y = 0, 0
    while True:
        if keyboard.is_pressed('ctrl'):
            x, y = pyautogui.position()
            z = pyautogui.pixel(x, y)
            print(x, y, z)
            beep_x_times(1)

        if keyboard.is_pressed('alt'):
            x_, y_ = pyautogui.position()
            print(f"{x}, {y}, {x_ - x}, {y_ - y}")
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
            pyautogui.moveTo(x=middle_of_bounding_box[0], y=middle_of_bounding_box[1])
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


def beep_x_times(x) -> None:
    for _ in range(x):
        winsound.Beep(frequency=1500, duration=100)
        time.sleep(0.1)


def notification_beep() -> None:
    winsound.Beep(frequency=2000, duration=100)
    winsound.Beep(frequency=3000, duration=100)
    winsound.Beep(frequency=2000, duration=100)


def report_local_system() -> None:
    # just broadcast position
    pass


def test_check_region(region) -> list:
    overview_and_selected_item_screenshot = jpg_screenshot_of_the_selected_region(region)
    test_result = ocr_reader.readtext(overview_and_selected_item_screenshot)
    return test_result


def check_for_hostiles_and_engage(region: Tuple) -> None:
    region_screenshot = jpg_screenshot_of_the_selected_region(region)
    results = ocr_reader.readtext(region_screenshot)
    filtered_strings = [item for sublist in results for item in sublist if isinstance(item, str)]
    for player_ship in ALL_FRIGATES:
        if player_ship in filtered_strings:
            target_and_engage_a_hostile_ship(region, results, player_ship)
    if NPC_MINMATAR in filtered_strings:
        target_and_engage_a_hostile_ship(region, results, NPC_MINMATAR)
    return None


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
    pyautogui.keyDown('ctrl')
    pyautogui.click()
    pyautogui.keyUp('ctrl')


def turn_recording_on_or_off() -> None:
    pyautogui.hotkey('alt', 'f9', interval=0.1)


def target_and_engage_a_hostile_ship(region: Tuple, overview_content: list, ship: str) -> None:
    # turn_recording_on_or_off()
    for item in overview_content:
        if ship in item[1]:
            coordinates = bounding_box_center_coordinates(bounding_box=item[0], region=region)
            pyautogui.moveTo(coordinates)

            # Use AB/MWD
            pyautogui.press(PROP_MOD)

            for _ in range(3):
                approach()
            while True:
                target_lock()
                time.sleep(0.2)
                if check_if_target_is_locked(SELECTED_ITEM_REGION):
                    for _ in range(3):
                        orbit_target()
                        time.sleep(0.1)
                    break

            # Fire guns and try to tackle
            pyautogui.press(GUNS)

            while True:
                if not check_if_scrambler_is_operating():
                    pyautogui.press('f2')
                else:
                    break

            notification_beep()


def check_if_target_is_locked(region: Tuple) -> bool:
    try:
        unlock_target_icon_present = pyautogui.locateCenterOnScreen(UNLOCK_TARGET_ICON, grayscale=False,
                                                                    confidence=DEFAULT_CONFIDENCE, region=region)
        if unlock_target_icon_present is not None:
            pyautogui.moveTo(x=unlock_target_icon_present[0], y=unlock_target_icon_present[1])
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


def manage_engagement() -> None:
    if not check_if_target_is_locked(SELECTED_ITEM_REGION):
        pass


def move_mouse_away_from_overview() -> None:
    pyautogui.moveTo(x=80, y=30)


def warp_to_safe_spot() -> None:
    pyautogui.moveTo(x=50, y=30)
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


def switch_tab_to_broadcasts(region: Tuple) -> None:
    screenshot = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('eet', region, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.1)
    screenshot = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('Broad', region, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.1)


def clear_broadcast_history() -> None:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    search_for_string_in_region('clear', SCANNER_REGION, screenshot, move_mouse_to_string=True)
    pyautogui.click()


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
    pyautogui.keyDown('q')
    pyautogui.click()
    pyautogui.keyUp('q')


def orbit_target() -> None:
    pyautogui.keyDown('w')
    pyautogui.click()
    pyautogui.keyUp('w')


def check_if_in_warp() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(CAPACITOR_REGION)
    if search_for_string_in_region('wa', CAPACITOR_REGION, screenshot):
        return True
    return False


def set_destination_home() -> None:
    pyautogui.hotkey('alt', 'a', interval=0.1)
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
    beep_x_times(2)


def jump_through_acceleration_gate(region: Tuple) -> None:
    screenshot = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('acceleration',
                                OVERVIEW_REGION,
                                screenshot,
                                move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.1)
    for _ in range(3):
        pyautogui.press('d')
        time.sleep(0.2)


def jump_through_gate_to_destination() -> bool:
    try:
        next_gate_on_route = pyautogui.locateCenterOnScreen(GATE_ON_ROUTE,
                                                            confidence=PC_SPECIFIC_CONFIDENCE,
                                                            grayscale=False,
                                                            region=OVERVIEW_REGION)
        if next_gate_on_route is not None:
            pyautogui.moveTo(x=next_gate_on_route[0], y=next_gate_on_route[1])
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


def dock_at_station() -> None:
    stations = [DESTINATION_STATION, DESTINATION_HOME_STATION]
    for station in stations:
        try:
            docking_station = pyautogui.locateCenterOnScreen(station, confidence=DEFAULT_CONFIDENCE,
                                                             grayscale=False,
                                                             region=OVERVIEW_REGION)
            if docking_station is not None:
                pyautogui.moveTo(x=docking_station[0], y=docking_station[1])
                pyautogui.keyDown('d')
                pyautogui.click()
                pyautogui.keyUp('d')
                break
        except pyautogui.ImageNotFoundException:
            pass


def open_or_close_notepad() -> None:
    pyautogui.hotkey('ctrl', 'n', interval=0.1)


def choose_system_to_travel_to(systems: list) -> str:
    random_system = random.choice(systems)
    return random_system


def check_if_docked(region: Tuple) -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(region)
    docked = search_for_string_in_region('undock', region, screenshot, move_mouse_to_string=True)
    if docked:
        return True
    return False


def check_if_destination_system_was_reached(destination_system: str, region: Tuple) -> bool:
    switch_tab_to_broadcasts(region)
    clear_broadcast_history()
    broadcast_current_location()
    time.sleep(0.2)
    screenshot = jpg_screenshot_of_the_selected_region(region)
    if search_for_string_in_region(destination_system, region, screenshot):
        return True
    return False


def broadcast_destination() -> bool:
    if destination is not None:
        open_or_close_notepad()
        screenshot = jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
        search_for_string_in_region(destination, TOP_LEFT_REGION, screenshot, move_mouse_to_string=True)
        pyautogui.rightClick()
        screenshot = jpg_screenshot_of_the_selected_region(TOP_LEFT_REGION)
        broadcast = search_for_string_in_region('broadcast', TOP_LEFT_REGION, screenshot, move_mouse_to_string=True)
        if broadcast:
            time.sleep(0.3)
            pyautogui.click()
        open_or_close_notepad()
        print(f'Destination broadcast to {destination} sent')
        return True
    return False


def set_destination(region: Tuple, systems: list) -> Union[bool, str]:
    global destination
    if destination:
        systems.remove(destination)
    select_gates_only_tab()
    move_mouse_away_from_overview()
    time.sleep(0.5)
    open_or_close_notepad()
    time.sleep(4)
    destination = choose_system_to_travel_to(systems)
    screenshot = jpg_screenshot_of_the_selected_region(region)
    destination_system = search_for_string_in_region(destination, region, screenshot, move_mouse_to_string=True)
    if destination_system:
        time.sleep(0.3)
        pyautogui.rightClick()
        time.sleep(0.3)
    else:
        open_or_close_notepad()
        return False
    screenshot = jpg_screenshot_of_the_selected_region(region)
    destination_confirmation = search_for_string_in_region('destination', region, screenshot, move_mouse_to_string=True)
    if destination_confirmation:
        pyautogui.click()
        pyautogui.moveTo(destination_system[0], destination_system[1])
    open_or_close_notepad()
    return destination


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
        return
    else:
        results = ocr_reader.readtext(screenshot)
        for result in results:
            searched_string = 'fleet'
            if searched_string.lower() in result[1].lower():
                middle_of_bounding_box = bounding_box_center_coordinates(result[0], region=SCANNER_REGION)
                pyautogui.click(x=middle_of_bounding_box[0], y=middle_of_bounding_box[1])
                screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
            if search_for_string_in_region('form fleet', SCANNER_REGION, screenshot, move_mouse_to_string=True):
                pyautogui.click()
                move_mouse_away_from_overview()
                return
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
    global destination
    form_fleet()
    time.sleep(0.1)
    if check_if_docked(SELECTED_ITEM_REGION):
        undock()
        time.sleep(20)
    # cannot broadcast destination while docked
    destination = set_destination(TOP_LEFT_REGION, AMARR_SYSTEMS)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if select_fleet_tab():
            break
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if select_broadcasts():
            break
    wait_for_fleet_members_to_join_and_broadcast_destination()
    if destination:
        for _ in range(MAX_NUMBER_OF_ATTEMPTS):
            if not check_if_destination_system_was_reached(destination, SCANNER_REGION):
                travel_to_destination()

            else:
                break
        warp_to_safe_spot()


def travel_home() -> None:
    set_destination_home()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if not check_if_destination_system_was_reached(HOME_SYSTEM, SCANNER_REGION):
            travel_to_destination()
        else:
            break
    dock_at_station()


def travel_to_destination_as_fleet_member() -> None:
    global destination
    join_existing_fleet()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if select_broadcasts():
            break
        else:
            print('cannot locate broadcasts')
            time.sleep(2)
    if check_if_docked(SELECTED_ITEM_REGION):
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
        if not check_if_destination_system_was_reached(destination, SCANNER_REGION):
            travel_to_destination()
        else:
            break
    warp_to_safe_spot()


def set_destination_from_broadcast() -> bool:
    global destination
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
        for system in MINMATAR_SYSTEMS:
            if search_for_string_in_region(system, SCANNER_REGION, screenshot, move_mouse_to_string=True):
                destination = system
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
    sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER, confidence=dscan_confidence, region=SCANNER_REGION)
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
        sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER, confidence=dscan_confidence, region=SCANNER_REGION)
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
    sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER, confidence=dscan_confidence, region=SCANNER_REGION)
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
    sliders = pyautogui.locateAllOnScreen(DSCAN_SLIDER, confidence=dscan_confidence, region=SCANNER_REGION)
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


def check_dscan_result() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
    results = ocr_reader.readtext(screenshot)
    frigate_on_scan = [(f, r) for f in ALL_FRIGATES for r in results if f == r[1]]
    if len(frigate_on_scan) > 0:
        print(frigate_on_scan)
        return True
    print(f"No target found in {destination}")
    return False


def scan_target_within_range(target: list) -> None:
    pyautogui.moveTo(bounding_box_center_coordinates(target[1][0], OVERVIEW_REGION))
    pyautogui.keyDown('v')
    pyautogui.click()
    pyautogui.keyUp('v')
    check_dscan_result()


def get_distance_for_scan_target(scan_target: str) -> dict:
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


def make_a_short_range_three_sixty_scan() -> None:
    select_directional_scanner()
    set_dscan_range_to_minimum()
    set_dscan_angle_to_three_sixty_degree()
    time.sleep(4)
    pyautogui.keyDown('v')
    time.sleep(0.1)
    pyautogui.keyUp('v')
    check_dscan_result()


def wait_for_fleet_members_to_join_and_broadcast_destination() -> None:
    broadcast_count = 0
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        screenshot = jpg_screenshot_of_the_selected_region(SCANNER_REGION)
        if search_for_string_in_region('position', SCANNER_REGION, screenshot):
            broadcast_destination()
            clear_broadcast_history()
            broadcast_count += 1
        if broadcast_count == FLEET_MEMBERS_COUNT:
            break
        time.sleep(3)


def warp_within_70_km(target: list) -> bool:
    pyautogui.moveTo(target[0], target[1])
    pyautogui.rightClick()
    screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
    if search_for_string_in_region('ithin (', OVERVIEW_REGION, screenshot,
                                   move_mouse_to_string=True):
        screenshot = jpg_screenshot_of_the_selected_region(OVERVIEW_REGION)
        search_for_string_in_region('ithin 70', OVERVIEW_REGION, screenshot,
                                    move_mouse_to_string=True)
        pyautogui.click()
        return True
    return False


def scan_sites_in_system(site: str) -> None:
    global destination

    targets_within_and_outside_scan_range = get_distance_for_scan_target(site)

    for target_within_range in targets_within_and_outside_scan_range['targets_within_scan_range']:
        scan_target_within_range(target_within_range)
        time.sleep(5)

    for target_outside_range in targets_within_and_outside_scan_range['targets_outside_scan_range']:
        warp_within_70_km(bounding_box_center_coordinates(target_outside_range[1][0], OVERVIEW_REGION))
        time.sleep(3)
        for _ in range(MAX_NUMBER_OF_ATTEMPTS):
            if not check_if_in_warp():
                break
        make_a_short_range_three_sixty_scan()
        time.sleep(2)
        warp_to_safe_spot()


def main_loop() -> None:

    beep_x_times(1)
    # jump_through_acceleration_gate(OVERVIEW_REGION)
    region_selector()
    notification_beep()



if __name__ == "__main__":
    main_loop()
