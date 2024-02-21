import atexit
import time
import logging

from constants import IS_FC, PROP_MOD, REPAIRER
import helper_functions as hf
import protocols as ptc

logging.basicConfig(filename='logfile.log',
                    level=logging.DEBUG,
                    filemode='w',
                    format="%(asctime)s %(levelname)s %(message)s")


import pyautogui

def main() -> None:
    hf.turn_recording_on_or_off()
    time.sleep(8)
    if IS_FC:
        ptc.fc_mission_plan()
    else:
        ptc.fm_mission_plan()


if __name__ == "__main__":
    hf.beep_x_times(1)
    # atexit.register(hf.turn_recording_on_or_off)
    # main()
    start = time.time()
    if not hf.button_detection_config.initial_button_pixel_sums:
        hf.prepare_module_buttons_coordinates_and_initial_pixel_sums()
    hf.remove_graphics()
    while True:

        if not hf.is_module_active('REPAIRER_BUTTON',
                                   hf.button_detection_config.buttons_coordinates['REPAIRER_BUTTON']):
            pyautogui.press(REPAIRER)
            hf.generic_variables.prop_module_on = True
