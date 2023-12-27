from typing import Tuple, List, Union

import cv2
import pyautogui
import io
import time
from easyocr import Reader
import keyboard
from PIL import Image
import winsound
import random

from constants import *

# todo killing rat at the plex
# todo scanning for hostiles
# todo GTFO if conditions are unfavorable
# todo if FC - sending broadcasts
# todo if wingman, then warping to FC and aggroing broadcast target
# todo create a listener on FC side that will detect 'in position' broadcast to broadcast destination in return
# todo report local system needs further work - make it broadcast location
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
                                move_mouse_to_string: bool = False, selected_result: int = 0, debug: bool = False)\
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
    for player_ship in all_frigates:
        if player_ship in filtered_strings:
            target_and_engage_a_hostile_ship(region, results, player_ship)
    if npc in filtered_strings:
        target_and_engage_a_hostile_ship(region, results, npc)
    return None


def check_if_target_is_outside_range() -> bool:
    too_far_away_message = ['the', 'target', 'too', 'far', 'away', 'within']
    region_screenshot = jpg_screenshot_of_the_selected_region(mid_to_top_region)
    results = ocr_reader.readtext(region_screenshot)
    filtered_strings = [item for sublist in results for item in sublist if isinstance(item, str)]
    for word in too_far_away_message:
        if word in filtered_strings:
            return True
    return False


def check_if_within_targeting_range() -> bool:
    try:
        target_is_lockable = pyautogui.locateCenterOnScreen(lock_target_icon, confidence=0.99,
                                                            region=overview_and_selected_item_region)
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
                if check_if_target_is_locked(overview_and_selected_item_region):
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
        unlock_target_icon_present = pyautogui.locateCenterOnScreen(unlock_target_image, grayscale=False,
                                                                    confidence=DEFAULT_CONFIDENCE, region=region)
        if unlock_target_icon_present is not None:
            pyautogui.moveTo(x=unlock_target_icon_present[0], y=unlock_target_icon_present[1])
            return True
    except pyautogui.ImageNotFoundException:
        return False


def check_if_scrambler_is_operating() -> bool:
    try:
        if pyautogui.locateCenterOnScreen(scrambler_on_icon, grayscale=False, confidence=DEFAULT_CONFIDENCE,
                                          region=targets_region):
            return True
        return False
    except pyautogui.ImageNotFoundException:
        pass


def manage_engagement() -> None:
    if not check_if_target_is_locked(overview_and_selected_item_region):
        pass


def move_mouse_away_from_overview() -> None:
    pyautogui.moveTo(x=100, y=10)


def warp_to_safe_spot() -> None:
    pyautogui.moveTo(x=50, y=30)
    pyautogui.rightClick()
    time.sleep(0.1)
    screenshot = jpg_screenshot_of_the_selected_region(top_left_region)
    search_for_string_in_region('loc', top_left_region, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.1)
    screenshot = jpg_screenshot_of_the_selected_region(top_left_region)
    for _ in range(5):
        search_for_string_in_region('spo', top_left_region, screenshot, move_mouse_to_string=True)
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
    screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
    search_for_string_in_region('clear', scanner_region, screenshot, move_mouse_to_string=True)
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
    screenshot = jpg_screenshot_of_the_selected_region(capacitor_region)
    if search_for_string_in_region('wa', capacitor_region, screenshot, debug=True):
        return True
    return False


def set_destination_home() -> None:
    pyautogui.hotkey('alt', 'a', interval=0.1)
    screenshot = jpg_screenshot_of_the_selected_region(mid_to_top_region)
    search_for_string_in_region('home station', mid_to_top_region, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    screenshot = jpg_screenshot_of_the_selected_region(mid_to_top_region)
    search_for_string_in_region('set destination', mid_to_top_region, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    pyautogui.hotkey('alt', 'a', interval=0.1)


def warp_to_scout_combat_site(region: Tuple) -> None:
    screenshot_of_scanner = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('probe', scanner_region, screenshot_of_scanner, True)
    pyautogui.click()
    screenshot_of_scanner = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('scout', scanner_region, screenshot_of_scanner, True)
    pyautogui.rightClick()
    screenshot_of_scanner_with_warp_to_option = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('to within', scanner_region, screenshot_of_scanner_with_warp_to_option, True)
    pyautogui.click()
    beep_x_times(2)


def jump_through_acceleration_gate(region: Tuple) -> None:
    overview_and_selected_item_screenshot = jpg_screenshot_of_the_selected_region(region)
    search_for_string_in_region('acceleration', overview_and_selected_item_region,
                                overview_and_selected_item_screenshot,
                                True)
    pyautogui.click()
    time.sleep(0.1)
    for _ in range(3):
        pyautogui.press('d')
        time.sleep(0.2)


def jump_through_gate_to_destination() -> bool:
    try:
        next_gate_on_route = pyautogui.locateCenterOnScreen(gate_on_route, confidence=pc_specific_confidence,
                                                            grayscale=False, region=overview_and_selected_item_region)
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
    stations = [destination_station, destination_home_station]
    for station in stations:
        try:
            docking_station = pyautogui.locateCenterOnScreen(station, confidence=DEFAULT_CONFIDENCE,
                                                             grayscale=False,
                                                             region=overview_and_selected_item_region)
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


def choose_system_to_travel_to() -> str:
    random_system = random.choice(minmatar_systems)
    return random_system


def check_if_docked(region: Tuple) -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(region)
    docked = search_for_string_in_region('undock', region, screenshot, move_mouse_to_string=True)
    if docked:
        return True
    return False


def check_if_destination_system_was_reached(destination: str, region: Tuple) -> bool:
    switch_tab_to_broadcasts(region)
    clear_broadcast_history()
    broadcast_current_location()
    time.sleep(0.2)
    screenshot = jpg_screenshot_of_the_selected_region(region)
    if search_for_string_in_region(destination, region, screenshot):
        return True
    return False


def broadcast_destination() -> bool:
    if destination is not None:
        open_or_close_notepad()
        screenshot = jpg_screenshot_of_the_selected_region(top_left_region)
        search_for_string_in_region(destination, top_left_region, screenshot, move_mouse_to_string=True)
        pyautogui.rightClick()
        screenshot = jpg_screenshot_of_the_selected_region(top_left_region)
        broadcast = search_for_string_in_region('broadcast', top_left_region, screenshot, move_mouse_to_string=True)
        if broadcast:
            time.sleep(0.3)
            pyautogui.click()
        open_or_close_notepad()
        print(f'Destination broadcast to {destination} sent')
        return True
    return False


def set_destination(region: Tuple) -> Union[bool, str]:
    global destination
    select_gates_only_tab()
    move_mouse_away_from_overview()
    time.sleep(0.5)
    open_or_close_notepad()
    time.sleep(4)
    destination = choose_system_to_travel_to()
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
    screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
    search_for_string_in_region('advert', scanner_region, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
    search_for_string_in_region('create', scanner_region, screenshot, selected_result=1, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(1)
    screenshot = jpg_screenshot_of_the_selected_region(mid_to_top_region)
    search_for_string_in_region('submit', mid_to_top_region, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def select_broadcasts() -> None:
    screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
    if search_for_string_in_region('cast', scanner_region, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        return True
    else:
        return False


def join_existing_fleet() -> None:
    pyautogui.hotkey('ctrl', 'alt', 'f', interval=0.1)
    screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
    search_for_string_in_region('ind', scanner_region, screenshot, move_mouse_to_string=True)
    pyautogui.click()
    time.sleep(0.2)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        search_for_string_in_region('ind', scanner_region, screenshot, selected_result=2, move_mouse_to_string=True)
        pyautogui.click()
        time.sleep(0.2)
        screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
        if search_for_string_in_region('uncanny', scanner_region, screenshot, move_mouse_to_string=True):
            pyautogui.rightClick()
            time.sleep(0.2)
            screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
            search_for_string_in_region('join', scanner_region, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            time.sleep(0.2)
            screenshot = jpg_screenshot_of_the_selected_region(mid_to_top_region)
            search_for_string_in_region('yes', mid_to_top_region, screenshot, move_mouse_to_string=True)
            pyautogui.click()
            print('fleet joined')
            return
        else:
            time.sleep(3)


def form_fleet() -> None:
    pyautogui.hotkey('ctrl', 'alt', 'f', interval=0.1)
    time.sleep(0.2)
    screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
    form_fleet_button = search_for_string_in_region('form fleet', scanner_region, screenshot, move_mouse_to_string=True)
    if form_fleet_button:
        pyautogui.click()
        move_mouse_away_from_overview()
        return
    else:
        results = ocr_reader.readtext(screenshot)
        for result in results:
            searched_string = 'fleet'
            if searched_string.lower() in result[1].lower():
                middle_of_bounding_box = bounding_box_center_coordinates(result[0], region=scanner_region)
                pyautogui.click(x=middle_of_bounding_box[0], y=middle_of_bounding_box[1])
                screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
            if search_for_string_in_region('form fleet', scanner_region, screenshot, move_mouse_to_string=True):
                pyautogui.click()
                move_mouse_away_from_overview()
                return
    create_fleet_advert()
    select_broadcasts()


def select_gates_only_tab() -> None:
    screenshot = jpg_screenshot_of_the_selected_region(overview_and_selected_item_region)
    search_for_string_in_region('gates', overview_and_selected_item_region, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def select_fw_tab() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(overview_and_selected_item_region)
    if search_for_string_in_region('fw', overview_and_selected_item_region, screenshot, move_mouse_to_string=True):
        pyautogui.click()
        return True
    return False


def travel_to_destination_as_fc() -> None:
    global destination
    form_fleet()
    time.sleep(0.1)
    if check_if_docked(overview_and_selected_item_region):
        undock()
        time.sleep(20)
    # cannot broadcast destination while docked
    destination = set_destination(top_left_region)
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if select_fleet_tab():
            break
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if select_broadcasts():
            break
    wait_for_fleet_members_to_join_and_broadcast_destination()
    if destination:
        for _ in range(MAX_NUMBER_OF_ATTEMPTS):
            if not check_if_destination_system_was_reached(destination, scanner_region):
                travel_to_destination()

            else:
                break
        warp_to_safe_spot()


def travel_home() -> None:
    set_destination_home()
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        if not check_if_destination_system_was_reached(home_system, scanner_region):
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
    if check_if_docked(overview_and_selected_item_region):
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
        if not check_if_destination_system_was_reached(destination, scanner_region):
            travel_to_destination()
        else:
            break
    warp_to_safe_spot()


def set_destination_from_broadcast() -> bool:
    global destination
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
        for system in minmatar_systems:
            if search_for_string_in_region(system, scanner_region, screenshot, move_mouse_to_string=True):
                destination = system
                pyautogui.rightClick()
                time.sleep(0.1)
                screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
                search_for_string_in_region('dest', scanner_region, screenshot, move_mouse_to_string=True)
                pyautogui.click()
                return True
        else:
            time.sleep(2)
            return False

def broadcast_current_location() -> None:
    pyautogui.press(',')


def select_fleet_tab() -> bool:
    screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
    if search_for_string_in_region('eet', scanner_region, screenshot, move_mouse_to_string=True, debug=True):
        pyautogui.click()
        return True
    return False


def select_directional_scanner() -> None:
    screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
    search_for_string_in_region('direct', scanner_region, screenshot, move_mouse_to_string=True)
    pyautogui.click()


def set_dscan_range_to_minimum() -> None:
    range_slider = None
    screen_width, screen_height = pyautogui.size()
    sliders = pyautogui.locateAllOnScreen(dscan_slider, confidence=dscan_confidence, region=scanner_region)
    for slider in sliders:
        if range_slider is None:
            range_slider = slider
        if slider[0] < range_slider[0]:
            range_slider = slider
    x = range_slider[0] + (range_slider[2]/2)
    y = range_slider[1] + (range_slider[3]/2)
    pyautogui.moveTo(x=x, y=y)
    pyautogui.click()
    pyautogui.dragTo(screen_width*0.80, y, 0.5, button='left')
    move_mouse_away_from_overview()


def set_dscan_range_to_maximum() -> None:
    range_slider = None
    screen_width, screen_height = pyautogui.size()
    sliders = pyautogui.locateAllOnScreen(dscan_slider, confidence=dscan_confidence, region=scanner_region)
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


def set_dscan_angle_to_five_degree() -> None:
    angle_slider = None
    screen_width, screen_height = pyautogui.size()
    sliders = pyautogui.locateAllOnScreen(dscan_slider, confidence=dscan_confidence, region=scanner_region)
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
    sliders = pyautogui.locateAllOnScreen(dscan_slider, confidence=dscan_confidence, region=scanner_region)
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


def dscan_locations_of_interest(scan_target: str = '') -> None:
    range_to_scan_target = None
    screenshot = jpg_screenshot_of_the_selected_region(overview_and_selected_item_region)
    results = ocr_reader.readtext(screenshot)

    searched_term = next((r for r in results if str(r[1]).lower() == scan_target), None)
    matching_items = [r for r in results if r[0][2][1] == searched_term[0][2][1]]
    for item in matching_items:
        new_item_with_period = item.replace(',', '.')
        if 'AU' in new_item_with_period[1]:
            range_to_scan_target = float(new_item_with_period[1][:-3])
        else:
            range_to_scan_target = float(new_item_with_period[1])
    

def broadcast_in_position() -> None:
    pyautogui.press('.')


def wait_for_fleet_members_to_join_and_broadcast_destination() -> None:
    broadcast_count = 0
    for _ in range(MAX_NUMBER_OF_ATTEMPTS):
        screenshot = jpg_screenshot_of_the_selected_region(scanner_region)
        if search_for_string_in_region('position', scanner_region, screenshot, debug=True):
            broadcast_destination()
            clear_broadcast_history()
            broadcast_count += 1
        if broadcast_count == FLEET_MEMBERS_COUNT:
            break
        time.sleep(3)


def main_loop() -> None:
    # check_for_hostiles_and_engage(overview_and_selected_item_region)
    # travel_to_destination_as_fc()
    travel_home()


if __name__ == "__main__":
    # travel_to_destination_as_fleet_member()
    travel_home()

