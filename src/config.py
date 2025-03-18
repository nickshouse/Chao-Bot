# config.py

from pathlib import Path

# Directories
BASE_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = BASE_DIR / "assets"
GRAPHICS_DIR = ASSETS_DIR / "graphics" / "thumbnails"


# Background images
HERO_BG_PATH = GRAPHICS_DIR / "hero_background.png"
DARK_BG_PATH = GRAPHICS_DIR / "dark_background.png"
NEUTRAL_BG_PATH = GRAPHICS_DIR / "neutral_background.png"
EGG_BG_PATH = GRAPHICS_DIR / "egg_background.png"

# Persistent Views File
STATS_PERSISTENT_VIEWS_FILE = "stats_persistent_views.json"
MARKET_PERSISTENT_VIEWS_FILE = "market_persistent_views.json"


# Chao settings
CHAO_NAMES = [
    "Chaoko", "Chaowser", "Chaorunner", "Chaozart", "Chaobacca", "Chaowder",
    "Chaocolate", "Chaolesterol", "Chao Mein", "Chaoster", "Chaomanji", "Chaosmic",
    "Chaozilla", "Chaoseidon", "Chaosferatu", "Chaolin", "Chow", "Chaotzhu",
    "Chaoblin", "Count Chaocula", "Chaozil", "Chaoz", "Chaokie Chan", "Chaobama", "Chaombie",
    "Xin Chao", "Ka Chao", "Ciao"
]
MOUTH_TYPES = ['happy', 'unhappy', 'grumble', 'evil', 'none']
EYE_TYPES = ['normal', 'happy', 'angry', 'tired']

# Form level thresholds
FORM_LEVEL_2, FORM_LEVEL_3, FORM_LEVEL_4 = 5, 20, 60

# Grading system
GRADES = ['F', 'E', 'D', 'C', 'B', 'A', 'S']
GRADE_TO_VALUE = {g: v for g, v in zip(GRADES, range(-1, 7))}

# Stat thresholds and alignments
SWIM_FLY_THRESHOLD = RUN_POWER_THRESHOLD = 5
ALIGNMENTS = {"hero": 5, "dark": -5, "neutral": 0}

# Fruit stats adjustments
FRUIT_STATS_ADJUSTMENTS = {
    "round fruit":       {"stamina_ticks": (1, 3), "belly_ticks": (1, 3), "hp_ticks": 1, "energy_ticks": 1},
    "triangle fruit":    {"stamina_ticks": (1, 3), "belly_ticks": (1, 3), "hp_ticks": 1, "energy_ticks": 1},
    "square fruit":      {"stamina_ticks": (1, 3), "belly_ticks": (1, 3), "hp_ticks": 1, "energy_ticks": 1},
    "hero fruit":        {"stamina_ticks": (1, 3), "dark_hero": 1, "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
    "dark fruit":        {"stamina_ticks": (1, 3), "dark_hero": -1, "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
    "chao fruit":        {"swim_ticks": 4, "fly_ticks": 4, "run_ticks": 4, "power_ticks": 4, "stamina_ticks": 4, "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
    "strong fruit":      {"stamina_ticks": 2, "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 3},
    "tasty fruit":       {"stamina_ticks": (3, 6), "belly_ticks": (2, 3), "hp_ticks": (2, 3), "energy_ticks": 1},
    "heart fruit":       {"stamina_ticks": 1, "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
    "garden nut":        {"stamina_ticks": (1, 3), "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
    "orange fruit":      {"swim_ticks": 3, "fly_ticks": -2, "run_ticks": -2, "power_ticks": 3, "stamina_ticks": 1, "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
    "blue fruit":        {"swim_ticks": 2, "fly_ticks": 5, "run_ticks": -1, "power_ticks": -1, "stamina_ticks": 3, "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
    "pink fruit":        {"swim_ticks": 4, "fly_ticks": -3, "run_ticks": 4, "power_ticks": -3, "stamina_ticks": 2, "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
    "green fruit":       {"swim_ticks": 0, "fly_ticks": -1, "run_ticks": 3, "power_ticks": 4, "stamina_ticks": 2, "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
    "purple fruit":      {"swim_ticks": -2, "fly_ticks": 3, "run_ticks": 3, "power_ticks": -2, "stamina_ticks": 1, "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
    "yellow fruit":      {"swim_ticks": -3, "fly_ticks": 4, "run_ticks": -3, "power_ticks": 4, "stamina_ticks": 2, "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
    "red fruit":         {"swim_ticks": 3, "fly_ticks": 1, "run_ticks": 3, "power_ticks": 2, "stamina_ticks": -5, "belly_ticks": (1, 2), "hp_ticks": (1, 2), "energy_ticks": (1, 2)},
    "power fruit":       {"power_ticks": (1, 4), "run_power": 1, "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
    "swim fruit":        {"swim_ticks": (1, 4), "swim_fly": -1, "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
    "run fruit":         {"run_ticks": (1, 4), "run_power": -1, "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
    "fly fruit":         {"fly_ticks": (1, 4), "swim_fly": 1, "belly_ticks": 1, "hp_ticks": 1, "energy_ticks": 1},
    "strange mushroom":  {}
}
FRUITS = [fruit.title() for fruit in FRUIT_STATS_ADJUSTMENTS]

# New default prices for the black market:
DEFAULT_PRICES = {
    "Round Fruit": 25, "Triangle Fruit": 25, "Square Fruit": 25,
    "Hero Fruit": 10, "Dark Fruit": 10, "Strong Fruit": 25,
    "Tasty Fruit": 30, "Heart Fruit": 30, "Chao Fruit": 55,
    "Orange Fruit": 35, "Yellow Fruit": 50, "Green Fruit": 50,
    "Red Fruit": 60, "Blue Fruit": 40, "Pink Fruit": 55, "Purple Fruit": 45,
    "Swim Fruit": 15, "Fly Fruit": 15, "Run Fruit": 15, "Power Fruit": 15,
    "Garden Nut": 10, "Strange Mushroom": 10
}

# Tick positions for stat pages
PAGE1_TICK_POSITIONS = [(446, y) for y in [1176, 315, 591, 883, 1469]]
PAGE2_TICK_POSITIONS = {
    'belly': (272, 314),
    'happiness': (272, 590),
    'illness': (272, 882),
    'energy': (272, 1175),
    'hp': (272, 1468)
}

# Grade ranges for stat increments
GRADE_RANGES = {
    'F': (8, 12), 'E': (11, 15), 'D': (14, 18), 'C': (17, 21),
    'B': (20, 24), 'A': (23, 27), 'S': (26, 30), 'X': (30, 35)
}


CHAO_TYPES = [
    ("dark_normal_1.png", "Normal", "Form 1"),
    ("hero_normal_1.png", "Normal", "Form 1"),
    ("neutral_normal_1.png", "Normal", "Form 1"),

    ("dark_normal_fly_2.png", "Normal", "Form 2"),
    ("dark_normal_normal_2.png", "Normal", "Form 2"),
    ("hero_normal_fly_2.png", "Normal", "Form 2"),
    ("hero_normal_normal_2.png", "Normal", "Form 2"),
    ("neutral_normal_fly_2.png", "Normal", "Form 2"),
    ("neutral_normal_normal_2.png", "Normal", "Form 2"),

    ("dark_fly_3.png", "Fly", "Form 3"),
    ("dark_normal_3.png", "Normal", "Form 3"),
    ("hero_fly_3.png", "Fly", "Form 3"),
    ("hero_normal_3.png", "Normal", "Form 3"),
    ("neutral_fly_3.png", "Fly", "Form 3"),
    ("neutral_normal_3.png", "Normal", "Form 3"),
    ("dark_power_3.png", "Power", "Form 3"),
    ("hero_power_3.png", "Power", "Form 3"),
    ("neutral_power_3.png", "Power", "Form 3"),
    ("dark_run_3.png", "Run", "Form 3"),
    ("hero_run_3.png", "Run", "Form 3"),
    ("neutral_run_3.png", "Run", "Form 3"),
    ("dark_swim_3.png", "Swim", "Form 3"),
    ("hero_swim_3.png", "Swim", "Form 3"),
    ("neutral_swim_3.png", "Swim", "Form 3"),

    ("dark_fly_fly_4.png", "Fly/Fly", "Form 4"),
    ("dark_fly_normal_4.png", "Fly/Normal", "Form 4"),
    ("dark_fly_power_4.png", "Fly/Power", "Form 4"),
    ("dark_fly_run_4.png", "Fly/Run", "Form 4"),
    ("dark_fly_swim_4.png", "Fly/Swim", "Form 4"),
    ("hero_fly_fly_4.png", "Fly/Fly", "Form 4"),
    ("hero_fly_normal_4.png", "Fly/Normal", "Form 4"),
    ("hero_fly_power_4.png", "Fly/Power", "Form 4"),
    ("hero_fly_run_4.png", "Fly/Run", "Form 4"),
    ("hero_fly_swim_4.png", "Fly/Swim", "Form 4"),
    ("neutral_fly_fly_4.png", "Fly/Fly", "Form 4"),
    ("neutral_fly_normal_4.png", "Fly/Normal", "Form 4"),
    ("neutral_fly_power_4.png", "Fly/Power", "Form 4"),
    ("neutral_fly_run_4.png", "Fly/Run", "Form 4"),
    ("neutral_fly_swim_4.png", "Fly/Swim", "Form 4"),

    ("dark_normal_normal_4.png", "Normal/Normal", "Form 4"),
    ("dark_normal_power_4.png", "Normal/Power", "Form 4"),
    ("dark_normal_run_4.png", "Normal/Run", "Form 4"),
    ("dark_normal_swim_4.png", "Normal/Swim", "Form 4"),
    ("hero_normal_normal_4.png", "Normal/Normal", "Form 4"),
    ("hero_normal_power_4.png", "Normal/Power", "Form 4"),
    ("hero_normal_run_4.png", "Normal/Run", "Form 4"),
    ("hero_normal_swim_4.png", "Normal/Swim", "Form 4"),
    ("neutral_normal_normal_4.png", "Normal/Normal", "Form 4"),
    ("neutral_normal_power_4.png", "Normal/Power", "Form 4"),
    ("neutral_normal_run_4.png", "Normal/Run", "Form 4"),
    ("neutral_normal_swim_4.png", "Normal/Swim", "Form 4"),

    ("dark_power_fly_4.png", "Power/Fly", "Form 4"),
    ("dark_power_normal_4.png", "Power/Normal", "Form 4"),
    ("dark_power_power_4.png", "Power/Power", "Form 4"),
    ("dark_power_run_4.png", "Power/Run", "Form 4"),
    ("dark_power_swim_4.png", "Power/Swim", "Form 4"),
    ("hero_power_fly_4.png", "Power/Fly", "Form 4"),
    ("hero_power_normal_4.png", "Power/Normal", "Form 4"),
    ("hero_power_power_4.png", "Power/Power", "Form 4"),
    ("hero_power_run_4.png", "Power/Run", "Form 4"),
    ("hero_power_swim_4.png", "Power/Swim", "Form 4"),
    ("neutral_power_fly_4.png", "Power/Fly", "Form 4"),
    ("neutral_power_normal_4.png", "Power/Normal", "Form 4"),
    ("neutral_power_power_4.png", "Power/Power", "Form 4"),
    ("neutral_power_run_4.png", "Power/Run", "Form 4"),
    ("neutral_power_swim_4.png", "Power/Swim", "Form 4"),

    ("dark_run_fly_4.png", "Run/Fly", "Form 4"),
    ("dark_run_normal_4.png", "Run/Normal", "Form 4"),
    ("dark_run_power_4.png", "Run/Power", "Form 4"),
    ("dark_run_run_4.png", "Run/Run", "Form 4"),
    ("dark_run_swim_4.png", "Run/Swim", "Form 4"),
    ("hero_run_fly_4.png", "Run/Fly", "Form 4"),
    ("hero_run_normal_4.png", "Run/Normal", "Form 4"),
    ("hero_run_power_4.png", "Run/Power", "Form 4"),
    ("hero_run_run_4.png", "Run/Run", "Form 4"),
    ("hero_run_swim_4.png", "Run/Swim", "Form 4"),
    ("neutral_run_fly_4.png", "Run/Fly", "Form 4"),
    ("neutral_run_normal_4.png", "Run/Normal", "Form 4"),
    ("neutral_run_power_4.png", "Run/Power", "Form 4"),
    ("neutral_run_run_4.png", "Run/Run", "Form 4"),
    ("neutral_run_swim_4.png", "Run/Swim", "Form 4"),

    ("dark_swim_fly_4.png", "Swim/Fly", "Form 4"),
    ("dark_swim_normal_4.png", "Swim/Normal", "Form 4"),
    ("dark_swim_power_4.png", "Swim/Power", "Form 4"),
    ("dark_swim_run_4.png", "Swim/Run", "Form 4"),
    ("dark_swim_swim_4.png", "Swim/Swim", "Form 4"),
    ("hero_swim_fly_4.png", "Swim/Fly", "Form 4"),
    ("hero_swim_normal_4.png", "Swim/Normal", "Form 4"),
    ("hero_swim_power_4.png", "Swim/Power", "Form 4"),
    ("hero_swim_run_4.png", "Swim/Run", "Form 4"),
    ("hero_swim_swim_4.png", "Swim/Swim", "Form 4"),
    ("neutral_swim_fly_4.png", "Swim/Fly", "Form 4"),
    ("neutral_swim_normal_4.png", "Swim/Normal", "Form 4"),
    ("neutral_swim_power_4.png", "Swim/Power", "Form 4"),
    ("neutral_swim_run_4.png", "Swim/Run", "Form 4"),
    ("neutral_swim_swim_4.png", "Swim/Swim", "Form 4"),
]
