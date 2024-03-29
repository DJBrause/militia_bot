import ast
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

FLEET_MEMBERS_COUNT = 0
MAX_NUMBER_OF_ATTEMPTS = 30
IS_FC = ast.literal_eval(os.environ.get('IS_FC'))
DEFAULT_CONFIDENCE = 0.9
MAX_EXPECTED_TRAVEL_DISTANCE = 50
PROP_MOD = 'f1'
WEB = 'f3'
SCRAM = 'f2'
GUNS = 'f4'
REPAIRER = 'f5'

MAX_SCAN_RANGE = 14.3
MAX_PIXEL_SPREAD = 5
SCRAMBLER_EQUIPPED = ast.literal_eval(os.environ.get('SCRAMBLER_EQUIPPED'))
WEBIFIER_EQUIPPED = ast.literal_eval(os.environ.get('WEBIFIER_EQUIPPED'))
DRONES_EQUIPPED = ast.literal_eval(os.environ.get('DRONES_EQUIPPED'))
REPAIRER_EQUIPPED = ast.literal_eval(os.environ.get('REPAIRER_EQUIPPED'))
MAX_MODULE_ACTIVATION_CHECK_ATTEMPTS = 15
LOWER_COLOR_THRESHOLD = np.array([60, 140, 40])
UPPER_COLOR_THRESHOLD = np.array([90, 255, 255])
REPAIRER_CYCLE_TIME = 4.5
WEBIFIER_CYCLE_TIME = 5
PROP_MOD_CYCLE_TIME = 8.5

SHORT_SCAN_THRESHOLD = 15
PAUSE_AFTER_DESTINATION_BROADCAST = 20
TIMEOUT_DURATION = 900
OFFENSIVE_PLEXING = False

UNLOCK_TARGET_ICON = 'images/unlock_icon.PNG'
CANNOT_LOCK_ICON = 'images/cannot_lock.PNG'
LOCK_TARGET_ICON = 'images/lock_target.PNG'
SCRAMBLER_ON_ICON = 'images/scrambler_on.PNG'
SCRAMBLER_ON_ICON_SMALL = 'images/scrambler_on_small.PNG'
WEBIFIER_ON_ICON = 'images/webifier_on.PNG'
WEBIFIER_ON_ICON_SMALL = 'images/web_small.PNG'
LASER_ON = 'images/laser_on.PNG'
LASER_ON_SMALL = 'images/laser_on_small.PNG'
SCRAMBLER_BUTTON = 'images/scrambler_button.PNG'
WEBIFIER_BUTTON = 'images/webifier_button.PNG'
PROP_MOD_BUTTON = 'images/prop_mod_button.PNG'
REPAIRER_BUTTON = 'images/repairer_button.PNG'

RAT_ICON = 'images/rat_icon.PNG'
GATE_ON_ROUTE = 'images/gate_on_route.PNG'
DESTINATION_STATION = 'images/destination_station.PNG'
DESTINATION_HOME_STATION = 'images/destination_home_station.PNG'
DSCAN_SLIDER = 'images/dscan_slider.PNG'
MORE_ICON = 'images/more_icon.PNG'

MASK_LOWER_BAND = np.array([60, 140, 40])
MASK_UPPER_BAND = np.array([90, 255, 255])

GUNS_BUTTON_COORDS = ast.literal_eval(os.environ.get('GUNS_BUTTON_COORDS'))
REPAIRER_BUTTON_COORDS = ast.literal_eval(os.environ.get('REPAIRER_BUTTON_COORDS'))
SHIP_HEALTH_BARS_COORDS = ast.literal_eval(os.environ.get('SHIP_HEALTH_BARS_COORDS'))
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
COORDS_AWAY_FROM_OVERVIEW = ast.literal_eval(os.environ.get('COORDS_AWAY_FROM_OVERVIEW'))

AMARR_FRIGATES = ['Executioner', 'Inquisitor', 'Crucifier', 'Punisher', 'Magnate', 'Tormentor',
                  'Imperial Navy Slicer', 'Crucifier Navy Issue', 'Magnate Navy Issue', 'Slicer']
CALDARI_FRIGATES = ['Condor', 'Bantam', 'Griffin', 'Kestrel', 'Merlin', 'Heron', 'Griffin Navy Issue',
                    'Caldari Navy Hookbill', 'Heron Navy Issue', 'Hookbill']
GALLENTE_FRIGATES = ['Atron', 'Navitas', 'Tristan', 'Incursus', 'Maulus', 'Imicus', 'Federation Navy Comet',
                     'Maulus Navy Issue', 'Imicus Navy Issue', 'Comet', 'Federation']
MINMATAR_FRIGATES = ['Slasher', 'Burst', 'Breacher', 'Rifter', 'Probe', 'Firetail', 'Republic Fleet Firetail', 'Vigil',
                     'Vigil Fleet Issue', 'Probe Fleet Issue', 'Republic']
ROOKIE_SHIPS = ['Ibis', 'Reaper', 'Impairor', 'Velator']
MINER_FRIGATE = ['Venture']
NPC_MINMATAR = ['Frigate']
NPC_AMARR = ['Imperial Frigate', 'Frigate']
CAPSULE = ['Capsule']
CARGO_CONTAINER = ['Cargo', 'Container', 'Cargo Container']
ALL_FRIGATES = AMARR_FRIGATES + CALDARI_FRIGATES + GALLENTE_FRIGATES + MINMATAR_FRIGATES + ROOKIE_SHIPS + MINER_FRIGATE
CALDARI_DESTROYERS = ['Cormorant', 'Corax', 'Flycatcher', 'Jackdaw', 'Cormorant Navy Issue']
GALLENTE_DESTROYERS = ['Algos', 'Catalyst', 'Dragoon', 'Magus', 'Hecate', 'Catalyst Navy Issue']
AMARR_DESTROYERS = ['Coercer', 'Dragoon', 'Heretic', 'Confessor', 'Sunesis', 'Coercer Navy Issue']
MINMATAR_DESTROYERS = ['Thrasher', 'Talwar', 'Svipul', 'Thrasher Fleet Issue']
ALL_DESTROYERS = CALDARI_DESTROYERS + GALLENTE_DESTROYERS + AMARR_DESTROYERS + MINMATAR_DESTROYERS
AMARR_T1_CRUISERS = ["Augoror", "Maller", "Omen", "Tormentor", "Arbitrator"]
CALDARI_T1_CRUISERS = ["Blackbird", "Caracal", "Moa", "Osprey"]
GALLENTE_T1_CRUISERS = ["Celestis", "Exequror", "Thorax", "Vexor"]
MINMATAR_T1_CRUISERS = ["Bellicose", "Rupture", "Scythe", "Stabber"]
T1_CRUISERS = AMARR_T1_CRUISERS + CALDARI_T1_CRUISERS + GALLENTE_T1_CRUISERS + MINMATAR_T1_CRUISERS
AVOID = ['Slicer', 'Vigil', 'Vigil Fleet Issue', 'Imperial Navy Slicer', 'Caldari Navy Hookbill', 'Hookbill',
         'Republic Fleet Firetail', 'Firetail']

MINMATAR_SYSTEMS = ['Huola', 'Sosala', 'Lamaa', 'Roushzar']
AMARR_SYSTEMS = ['Kamela', 'Kourmonen', 'Anka']
# Make sure these are the same for both FC and FM, otherwise FM might not find the system to travel to at all.
SYSTEMS_TO_TRAVEL_TO = AMARR_SYSTEMS
