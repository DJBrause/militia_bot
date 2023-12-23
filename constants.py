import ast
import os
from dotenv import load_dotenv

load_dotenv()

FC = True
DEFAULT_CONFIDENCE = 0.9
MAX_EXPECTED_TRAVEL_DISTANCE = 50
PROP_MOD = 'f1'
WEB = 'f2'
SCRAM = 'f3'
GUNS = 'f4'

unlock_target_image = 'images/unlock_icon.PNG'
cannot_lock_icon = 'images/cannot_lock.PNG'
lock_target_icon = 'images/lock_target.PNG'
scrambler_on_icon = 'images/scrambler_on.PNG'
gate_on_route = 'images/gate_on_route.PNG'
destination_station = 'images/destination_station.PNG'
destination_home_station = 'images/destination_home_station.PNG'

scanner_region = ast.literal_eval(os.environ.get('SCANNER_REGION'))
# screen_center_region = ast.literal_eval(os.environ.get('SCREEN_CENTER_REGION'))
capacitor_region = ast.literal_eval(os.environ.get('CAPACITOR_REGION'))
overview_and_selected_item_region = ast.literal_eval(os.environ.get('OVERVIEW_AND_SELECTED_ITEM_REGION'))
top_left_region = ast.literal_eval(os.environ.get('TOP_LEFT_REGION'))
# local_window_region = ast.literal_eval(os.environ.get('LOCAL_WINDOW_REGION'))
# chat_window_region = ast.literal_eval(os.environ.get('CHAT_WINDOW_REGION'))
mid_to_top_region = ast.literal_eval(os.environ.get('MID_TO_TOP_REGION'))
targets_region = ast.literal_eval(os.environ.get('TARGETS_REGION'))
test_region = ast.literal_eval(os.environ.get('TEST_REGION'))

amarr_frigates = ['Executioner', 'Inquisitor', 'Crucifier', 'Punisher', 'Magnate', 'Tormentor', 'Slicer']
caldari_frigates = ['Condor', 'Bantam', 'Griffin', 'Kestrel', 'Merlin', 'Heron', 'Hookbill']
gallente_frigates = ['Atron', 'Navitas', 'Tristan', 'Incursus', 'Maulus', 'Imicus', 'Comet']
minmatar_frigates = ['Slasher', 'Burst', 'Breacher', 'Rifter', 'Probe', 'Reaper', 'Firetail', 'Vigil']
rookie_ships = ['Ibis', 'Reaper', 'Impairor', 'Velator']
npc = 'Minmatar Frigate'
all_frigates = amarr_frigates + caldari_frigates + gallente_frigates + minmatar_frigates + rookie_ships
avoid = ['Slicer', 'Hookbill']
minmatar_systems = ['Kourmonen', 'Huola', 'Iesa', 'Uusanen']
