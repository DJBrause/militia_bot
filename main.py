import atexit
import time
import logging

from constants import IS_FC, REPAIRER_CYCLE_TIME
import helper_functions as hf
import protocols as ptc

import scanning_and_information_gathering as sig

logging.basicConfig(filename='logfile.log',
                    level=logging.DEBUG,
                    filemode='w',
                    encoding='utf-8',
                    format="%(asctime)s %(levelname)s %(message)s")


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
    ptc.behaviour_at_the_site()
    # while True:
    #     print(sig.check_if_scrambler_is_operating())