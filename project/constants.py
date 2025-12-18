# constants.py
# Alle “enum”/string constants.
# Boss states: WAIT, WALKING_IN, LOOKING, WALKING_OUT
# Scenes: SCENE_MAIN_MENU, SCENE_PLAY, etc.
# Zo voorkom je typfouten en hou je scene/state checks netjes.

# Boss states
WAIT, WALKING_IN, LOOKING, WALKING_OUT = "wait", "walking_in", "looking", "walking_out"

# Scenes
SCENE_MAIN_MENU    = "main_menu"
SCENE_LEVEL_SELECT = "level_select"
SCENE_PLAY         = "play"
SCENE_COMPLETE     = "complete"
SCENE_GAMEOVER     = "gameover"
SCENE_SHOP         = "shop"
