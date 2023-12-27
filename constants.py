import ast
import os
from dotenv import load_dotenv

load_dotenv()

FLEET_MEMBERS_COUNT = 1
MAX_NUMBER_OF_ATTEMPTS = 20
IS_FC = True
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
dscan_slider = 'images/dscan_slider.PNG'

scanner_region = ast.literal_eval(os.environ.get('SCANNER_REGION'))
capacitor_region = ast.literal_eval(os.environ.get('CAPACITOR_REGION'))
overview_and_selected_item_region = ast.literal_eval(os.environ.get('OVERVIEW_AND_SELECTED_ITEM_REGION'))
top_left_region = ast.literal_eval(os.environ.get('TOP_LEFT_REGION'))
mid_to_top_region = ast.literal_eval(os.environ.get('MID_TO_TOP_REGION'))
targets_region = ast.literal_eval(os.environ.get('TARGETS_REGION'))
test_region = ast.literal_eval(os.environ.get('TEST_REGION'))
home_system = os.environ.get('HOME')

amarr_frigates = ['Executioner', 'Inquisitor', 'Crucifier', 'Punisher', 'Magnate', 'Tormentor', 'Slicer']
caldari_frigates = ['Condor', 'Bantam', 'Griffin', 'Kestrel', 'Merlin', 'Heron', 'Hookbill']
gallente_frigates = ['Atron', 'Navitas', 'Tristan', 'Incursus', 'Maulus', 'Imicus', 'Comet']
minmatar_frigates = ['Slasher', 'Burst', 'Breacher', 'Rifter', 'Probe', 'Reaper', 'Firetail', 'Vigil']
rookie_ships = ['Ibis', 'Reaper', 'Impairor', 'Velator']
npc = 'Minmatar Frigate'
all_frigates = amarr_frigates + caldari_frigates + gallente_frigates + minmatar_frigates + rookie_ships
avoid = ['Slicer', 'Hookbill']
minmatar_systems = ['Kourmonen', 'Huola', 'Anka', 'Sosala']
