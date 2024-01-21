import ast
import os
from dotenv import load_dotenv

load_dotenv()

FLEET_MEMBERS_COUNT = 0
MAX_NUMBER_OF_ATTEMPTS = 30
IS_FC = True
DEFAULT_CONFIDENCE = 0.9
MAX_EXPECTED_TRAVEL_DISTANCE = 50
PROP_MOD = 'f1'
WEB = 'f3'
SCRAM = 'f2'
GUNS = 'f4'
MAX_SCAN_RANGE = 14.3
MAX_PIXEL_SPREAD = 5
SCRAMBLER_EQUIPPED = False
WEBIFIER_EQUIPPED = True

UNLOCK_TARGET_ICON = 'images/unlock_icon.PNG'
CANNOT_LOCK_ICON = 'images/cannot_lock.PNG'
LOCK_TARGET_ICON = 'images/lock_target.PNG'
SCRAMBLER_ON_ICON = 'images/scrambler_on.PNG'
WEBIFIER_ON_ICON = 'images/webifier_on.PNG'
GATE_ON_ROUTE = 'images/gate_on_route.PNG'
DESTINATION_STATION = 'images/destination_station.PNG'
DESTINATION_HOME_STATION = 'images/destination_home_station.PNG'
DSCAN_SLIDER = 'images/dscan_slider.PNG'
MORE_ICON = 'images/more_icon.PNG'

SCANNER_REGION = ast.literal_eval(os.environ.get('SCANNER_REGION'))
CAPACITOR_REGION = ast.literal_eval(os.environ.get('CAPACITOR_REGION'))
SELECTED_ITEM_REGION = ast.literal_eval(os.environ.get('SELECTED_ITEM_REGION'))
OVERVIEW_REGION = ast.literal_eval(os.environ.get('OVERVIEW_REGION'))
TOP_LEFT_REGION = ast.literal_eval(os.environ.get('TOP_LEFT_REGION'))
MID_TO_TOP_REGION = ast.literal_eval(os.environ.get('MID_TO_TOP_REGION'))
TARGETS_REGION = ast.literal_eval(os.environ.get('TARGETS_REGION'))
LOCAL_REGION = ast.literal_eval(os.environ.get('LOCAL_REGION'))
TEST_REGION = ast.literal_eval(os.environ.get('TEST_REGION'))
HOME_SYSTEM = os.environ.get('HOME')
PC_SPECIFIC_CONFIDENCE = float(os.environ.get('PC_SPECIFIC_CONFIDENCE'))
COORDS_AWAY_FROM_OVERVIEW = [361, 77]

AMARR_FRIGATES = ['Executioner', 'Inquisitor', 'Crucifier', 'Punisher', 'Magnate', 'Tormentor', 'Slicer',
                  'Imperial Navy Slicer']
CALDARI_FRIGATES = ['Condor', 'Bantam', 'Griffin', 'Kestrel', 'Merlin', 'Heron', 'Hookbill',
                    'Caldari Navy Hookbill']
GALLENTE_FRIGATES = ['Atron', 'Navitas', 'Tristan', 'Incursus', 'Maulus', 'Imicus', 'Comet']
MINMATAR_FRIGATES = ['Slasher', 'Burst', 'Breacher', 'Rifter', 'Probe', 'Reaper', 'Firetail', 'Vigil',
                     'Vigil Fleet Issue']
ROOKIE_SHIPS = ['Ibis', 'Reaper', 'Impairor', 'Velator']
MINER_FRIGATE = ['Venture']
NPC_MINMATAR = 'Minmatar Frigate'
NPC_AMARR = 'Amarr Frigate'
ALL_FRIGATES = AMARR_FRIGATES + CALDARI_FRIGATES + GALLENTE_FRIGATES + MINMATAR_FRIGATES + ROOKIE_SHIPS + MINER_FRIGATE
CALDARI_DESTROYERS = ['Cormorant', 'Corax', 'Flycatcher', 'Jackdaw', 'Svipul']
GALLENTE_DESTROYERS = ['Algos', 'Catalyst', 'Dragoon', 'Magus', 'Hecate']
AMARR_DESTROYERS = ['Coercer', 'Dragoon', 'Heretic', 'Confessor', 'Sunesis']
MINMATAR_DESTROYERS = ['Thrasher', 'Coercer', 'Svipul', 'Jackdaw', 'Hecate']
ALL_DESTROYERS = CALDARI_DESTROYERS + GALLENTE_DESTROYERS + AMARR_DESTROYERS + MINMATAR_DESTROYERS
AVOID = ['Slicer', 'Hookbill', 'Vigil',  'Vigil Fleet Issue', 'Imperial Navy Slicer', 'Caldari Navy Hookbill']
MINMATAR_SYSTEMS = ['Kourmonen', 'Huola', 'Sosala']
AMARR_SYSTEMS = ['Lamaa', 'Kamela', 'Anka']
