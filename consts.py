# define action constants
MOVE_FORWARD = 'moveforward'
TURN_LEFT = 'turnleft'
TURN_RIGHT = 'turnright'
PICKUP = 'pickup'
SHOOT = 'shoot'

# define indicator constants
CONFOUNDED = 'confounded'
STENCH = 'stench'
TINGLE = 'tingle'
GLITTER = 'glitter'
BUMP = 'bump'
SCREAM = 'scream'


WALL = 'WALL'

RNORTH = 'rnorth'
REAST = 'reast'
RSOUTH = 'rsouth'
RWEST = 'rwest'

RNORTH_IDX = 0
REAST_IDX = 1
RSOUTH_IDX = 2
RWEST_IDX = 3

DIR_LIST = [RNORTH, REAST, RSOUTH, RWEST]

DIR_MAP = {
    RNORTH: 0,
    REAST: 1,
    RSOUTH: 2,
    RWEST: 3,
}

AGENT = 'agent'
WUMPUS = 'wumpus'
COIN = 'coin'
CONFUNDUS_PORTAL = 'confoundus'
EMPTY = 'empty'
WUMPUS_AND_CONFUNDUS = 'wompus_x_confundus'
NOT_VISITED_SAFE = 'not_visited_safe'
VISITED_SAFE = 'visited_safe'
UNKNOWN = 'unknown'
