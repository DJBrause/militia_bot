import ast
import numpy as np
import os
from dotenv import load_dotenv

load_dotenv()

CALDARI_FACTION_ID = 500001
MINMATAR_FACTION_ID = 500002
AMARR_FACTION_ID = 500003
GALLENTE_FACTION_ID = 500004

# SYSTEM NAME, SYSTEM ID
MINMATAR_AMARR_FW_SYSTEMS = [
    ['Tzvi', 30002957],
    ['Klogori', 30002097],
    ['Todifrauan', 30002062],
    ['Raa', 30002958],
    ['Sifilar', 30002959],
    ['Arzad', 30002960],
    ['Oyeman', 30002961],
    ['Ezzara', 30002962],
    ['Roushzar', 30002975],
    ['Labapi', 30002976],
    ['Arayar', 30002977],
    ['Asghed', 30002978],
    ['Tararan', 30002979],
    ['Sosan', 30002980],
    ['Halmah', 30002981],
    ['Bosboger', 30002514],
    ['Lulm', 30002516],
    ['Gulmorogod', 30002517],
    ['Haras', 30003087],
    ['Arnstur', 30002064],
    ['Lasleinur', 30002065],
    ['Amamake', 30002537],
    ['Vard', 30002538],
    ['Siseide', 30002539],
    ['Lantorn', 30002540],
    ['Dal', 30002541],
    ['Auga', 30002542],
    ['Brin', 30002067],
    ['Lamaa', 30003063],
    ['Huola', 30003067],
    ['Kourmonen', 30003068],
    ['Kamela', 30003069],
    ['Sosala', 30003070],
    ['Anka', 30003071],
    ['Iesa', 30003072],
    ['Uusanen', 30003077],
    ['Saikamon', 30003079],
    ['Resbroko', 30002056],
    ['Hadozeko', 30002057],
    ['Ardar', 30002058],
    ['Auner', 30002059],
    ['Evati', 30002060],
    ['Ofstold', 30002061],
    ['Sahtogas', 30003086],
    ['Helgatild', 30002063],
    ['Oyonata', 30003088],
    ['Kurniainen', 30003089],
    ['Saidusairos', 30003090],
    ['Tannakan', 30003091],
    ['Floseswin', 30002082],
    ['Uisper', 30002083],
    ['Aset', 30002084],
    ['Eytjangard', 30002085],
    ['Turnur', 30002086],
    ['Isbrabata', 30002087],
    ['Vimeini', 30002088],
    ['Avenod', 30002089],
    ['Frerstorn', 30002090],
    ['Ontorn', 30002091],
    ['Sirekur', 30002092],
    ['Gebuladi', 30002093],
    ['Ebolfer', 30002094],
    ['Eszur', 30002095],
    ['Hofjaldgund', 30002096],
    ['Orfrold', 30002098],
    ['Egmar', 30002099],
    ['Taff', 30002100],
    ['Ualkin', 30002101],
    ['Gukarla', 30002102],
    ['Arnher', 30002066]
]
FW_SYSTEMS_URL = 'https://esi.evetech.net/latest/fw/systems/?datasource=tranquility'


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

# Make sure these are the same for both FC and FM, otherwise FM might not find the system to travel to at all.
SYSTEMS_TO_TRAVEL_TO = ['Kamela', 'Kourmonen', 'Anka', 'Huola', 'Sosala', 'Lamaa', 'Roushzar']
