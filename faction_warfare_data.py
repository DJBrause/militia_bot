from requests import get as api_get
from constants import AMARR_FACTION_ID, MINMATAR_FACTION_ID, MINMATAR_AMARR_FW_SYSTEMS
import re
import os
import json
from datetime import datetime, timedelta
import logging

from constants import FW_SYSTEMS_URL


def get_system_name_based_on_system_id(system_id: int) -> int:
    for system in MINMATAR_AMARR_FW_SYSTEMS:
        if system[1] == system_id:
            return system[0]


def get_fw_systems() -> dict:
    fw_systems = api_get(FW_SYSTEMS_URL).json()
    return fw_systems


def get_amarr_systems() -> list:
    amarr_controlled_fw_systems = []
    fw_systems = get_fw_systems()
    for system in fw_systems:
        if system['occupier_faction_id'] == AMARR_FACTION_ID:
            amarr_controlled_fw_systems.append([get_system_name_based_on_system_id(system['solar_system_id']),
                                                system['solar_system_id']])
    return amarr_controlled_fw_systems


def get_amarr_frontline_systems() -> list:
    amarr_systems = get_amarr_systems()
    minmatar_system_names = [system_name for system_name, system_id in get_minmatar_systems()]
    frontline_systems = []
    for system in amarr_systems:
        system_data = get_system_data_based_on_system_id(system[1])
        stargate_ids = system_data['stargates']
        for stargate_id in stargate_ids:
            stargate_data = get_gate_data_based_on_stargate_id(stargate_id)
            stargate_name = re.search(r'\((.*?)\)', stargate_data['name']).group(1)
            if stargate_name not in frontline_systems and stargate_name in minmatar_system_names:
                frontline_systems.append(system[0])
                break
    return frontline_systems


def get_minmatar_systems() -> list:
    minmatar_controlled_fw_systems = []
    fw_systems = get_fw_systems()
    for system in fw_systems:
        if system['occupier_faction_id'] == MINMATAR_FACTION_ID:
            minmatar_controlled_fw_systems.append([get_system_name_based_on_system_id(system['solar_system_id']),
                                                   system['solar_system_id']])
    return minmatar_controlled_fw_systems


def get_system_data_based_on_system_id(system_id: int) -> dict:
    system_data_url = f'https://esi.evetech.net/latest/universe/systems/{system_id}/?datasource=tranquility&language=en'
    system_data = api_get(system_data_url).json()
    return system_data


def get_gate_data_based_on_stargate_id(stargate_id: int) -> dict:
    stargate_data_url = f'https://esi.evetech.net/latest/universe/stargates/{stargate_id}/?datasource=tranquility'
    stargate_data = api_get(stargate_data_url).json()
    return stargate_data


def check_and_update_fw_data():
    logging.info("Checking if Faction Warfare data is up to date.")
    file_name = 'fw_data.json'
    utc_now = datetime.utcnow()

    # Determine the last reset time, which is 11:00 UTC of the current day or the previous day
    reset_time_today = utc_now.replace(hour=11, minute=0, second=0, microsecond=0)

    if utc_now < reset_time_today:
        last_reset_time = reset_time_today - timedelta(days=1)
    else:
        last_reset_time = reset_time_today

    logging.info("Check if the file exists.")
    if os.path.exists(file_name):
        with open(file_name, 'r') as file:
            data = json.load(file)
            timestamp = data.get('timestamp')

            if timestamp:
                last_update = datetime.fromisoformat(timestamp)

                logging.info("Check if the last update was before the last reset time.")
                if last_update >= last_reset_time and utc_now - last_update < timedelta(hours=24):
                    logging.info("Data is up-to-date, no need to update.")
                    return

    logging.info("Either the file doesn't exist, timestamp is missing, or data is outdated.")
    frontline_systems = get_amarr_frontline_systems()

    logging.info("Updating the file with new data and timestamp.")
    new_data = {
        'timestamp': utc_now.isoformat(),
        'frontline_systems': frontline_systems
    }

    with open(file_name, 'w') as file:
        json.dump(new_data, file, indent=4)
