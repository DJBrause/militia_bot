import atexit
import time
import logging

from constants import IS_FC, SCANNER_REGION
import helper_functions as hf
import protocols as ptc
# import navigation_and_movement as nm

# import scanning_and_information_gathering as sig
# import communication_and_coordination as cc

logfile_name = 'logfile.log'

logging.basicConfig(filename=logfile_name,
                    level=logging.DEBUG,
                    filemode='w',
                    format="%(asctime)s %(levelname)s %(message)s")


def main() -> None:
    # hf.turn_recording_on_or_off()
    time.sleep(8)
    if IS_FC:
        ptc.fc_mission_plan(True)
    else:
        ptc.fm_mission_plan()


if __name__ == "__main__":
    hf.beep_x_times(1)
    # atexit.register(hf.turn_recording_on_or_off)
    # main()
    # nm.travel_home(True)
    # cc.drag_create_advert_into_region()
    try:
        if not hf.button_detection_config.initial_button_pixel_sums:
            hf.prepare_module_buttons_coordinates_and_initial_pixel_sums()
        ptc.engage_broadcast_target()
    except Exception as e:
        print(e)
        hf.beep_x_times(4)

    hf.beep_x_times(3)

    logging.info("Program ended.")
